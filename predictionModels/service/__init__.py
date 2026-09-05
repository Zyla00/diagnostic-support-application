# predictionModels/service/__init__.py
from __future__ import annotations
import json
import shutil
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# ======================================================================
# ŚCIEŻKI BAZOWE
# ======================================================================
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent                 # .../predictionModels/service
# katalog z modelami to OSOBNY folder: predictionModels/services/models/
MODELS_DIR  = SERVICE_DIR.parent / "services" / "models"

# --- HerBERT
HERBERT_DIR     = MODELS_DIR / "her_bert"
HERBERT_FINAL   = HERBERT_DIR / "final_model"      # <- tu zapisujemy/odczytujemy model do/po finetuningu
HERBERT_VERSIONS= HERBERT_DIR / "versions"

# --- XGBoost
XGB_DIR         = MODELS_DIR / "xg_boost"          # jeśli u Ciebie katalog nazywa się inaczej, zmień tutaj
XGB_FINAL       = XGB_DIR / "final_model"
XGB_VERSIONS    = XGB_DIR / "versions"

# --- Mistral / RAG
RAG_DIR         = MODELS_DIR / "rag"
RAG_NOTES_DIR   = RAG_DIR / "notes"
RAG_NOTES_FILE  = RAG_NOTES_DIR / "notatki.txt"
               # tworzy się przy 1. zapisie


# ======================================================================
# UTILSY
# ======================================================================
def _ensure_dirs(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _write_manifest(dest_dir: Path, model_name: str, tag: str,
                    params: Optional[dict], metrics: Optional[dict],
                    source_workdir: Optional[Path]) -> None:
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model": model_name,
        "tag": tag,  # "new" albo "old"
        "params": params or {},
        "metrics": metrics or {},
        "source_workdir": str(source_workdir) if source_workdir else None,
        "hostname": os.uname().nodename if hasattr(os, "uname") else None,
    }
    with open(dest_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def _snapshot_version(src_dir: Path, versions_dir: Path, ts: str, tag: str,
                      model_name: str, params: Optional[dict],
                      metrics: Optional[dict]) -> Path:
    _ensure_dirs(versions_dir)
    dest = versions_dir / f"{ts}__{tag}"
    shutil.copytree(src_dir, dest)
    _write_manifest(dest, model_name=model_name, tag=tag,
                    params=params, metrics=metrics, source_workdir=src_dir)
    return dest


def _apply_retention(versions_dir: Path, keep_last: int) -> None:
    if keep_last is None or keep_last <= 0 or not versions_dir.exists():
        return
    entries = sorted([p for p in versions_dir.iterdir() if p.is_dir()])
    to_delete = entries[:-keep_last]
    for p in to_delete:
        shutil.rmtree(p, ignore_errors=True)


def _promote_with_versions(
    work_dir: Path,
    final_path: Path,
    versions_dir: Path,
    model_name: str,
    params: Optional[dict],
    metrics: Optional[dict],
    keep_last: int = 20,
) -> str:
    """
    1) final_model -> versions/{TS}__old
    2) snapshot work_dir -> versions/{TS}__new
    3) work_dir -> final_model
    """
    _ensure_dirs(versions_dir, final_path.parent)
    ts = _timestamp()

    if final_path.exists():
        dest_old = versions_dir / f"{ts}__old"
        shutil.move(str(final_path), str(dest_old))
        _write_manifest(dest_old, model_name=model_name, tag="old",
                        params=None, metrics=None, source_workdir=final_path)

    _snapshot_version(work_dir, versions_dir, ts, tag="new",
                      model_name=model_name, params=params, metrics=metrics)

    shutil.move(str(work_dir), str(final_path))
    _apply_retention(versions_dir, keep_last=keep_last)

    return (
        f"Zarchiwizowano poprzedni final do {versions_dir}/{ts}__old, "
        f"zapisano nową wersję w {versions_dir}/{ts}__new i podmieniono {final_path.name}."
    )


# ======================================================================
# RAG
# ======================================================================
def rag_add_note(title: str, text: str, file_path: str | None = None) -> str:
    """
    Dopisuje notatkę do pliku RAG (tworzy go przy pierwszym razie).
    Format:
        ### Tytuł
        Treść
        (ZAŁĄCZNIK: ścieżka)
        ---
    """
    _ensure_dirs(RAG_NOTES_DIR)
    line = (
        f"### {title.strip()}\n"
        f"{text.strip()}\n"
        f"{'(ZAŁĄCZNIK: ' + file_path + ')' if file_path else ''}\n"
        f"---\n"
    )
    with open(RAG_NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    return f"Dodano notatkę do {RAG_NOTES_FILE.name}."


def rebuild_rag_index() -> str:
    """
    Buduje indeks FAISS z:
      - rag/definitions_of_specjalists/*.txt
      - rag/books/*.pdf
      - rag/notes/notatki.txt
    Zapisuje: defs_index.faiss, defs_meta.pkl, defs_chunks.pkl
    """
    from .mistral_rag_engine import build_index
    stats = build_index(base_dir=str(RAG_DIR))
    return f"Przebudowano indeks RAG: {stats['n_docs']} dokumentów, {stats['n_chunks']} chunków."


def rag_query(question: str, k: int = 5) -> list[dict]:
    from .mistral_rag_engine import query
    return query(question, k, base_dir=str(RAG_DIR))


# ======================================================================
# HERBERT (finetuning + wersjonowanie + swap final_model)
# ======================================================================
def retrain_herbert(params: dict | None = None) -> str:
    """
    Finetuning HerBERT-a startując z aktualnego 'her_bert/final_model'.

    WYMAGANE w `params`:
      - csv_path  (CSV zbudowany z wybranych ankiet/badań przez UI)

    Opcjonalne:
      - text_cols, label_col
      - num_train_epochs, per_device_train_batch_size, per_device_eval_batch_size,
        eval_steps, save_steps, seed
      - keep_last (ile wersji trzymać w 'versions', domyślnie 20)
    """
    from .herbert_engine import finetune_herbert as _finetune

    _ensure_dirs(HERBERT_DIR, HERBERT_VERSIONS)
    ts = _timestamp()
    work_dir = HERBERT_DIR / f"_new_{ts}"
    _ensure_dirs(work_dir)

    params = params or {}
    keep_last = int(params.get("keep_last", 20))

    # WYMAGAMY csv_path – bez fallbacków
    csv_path = params.get("csv_path")
    if not csv_path:
        raise FileNotFoundError(
            "Brak 'csv_path'. Finetuning HerBERT wymaga CSV zbudowanego z wybranych ankiet/badań (powstaje w ML Lab)."
        )
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV nie istnieje: {csv_path}")

    result = _finetune(
        output_dir=str(work_dir),                 # zapis bezpośrednio do work_dir
        csv_path=str(csv_path),
        base_model_dir=str(HERBERT_FINAL),        # start od aktualnego finala
        text_cols=params.get("text_cols"),
        label_col=params.get("label_col", "Jednostka_medyczna"),
        num_train_epochs=int(params.get("num_train_epochs", 3)),
        per_device_train_batch_size=int(params.get("per_device_train_batch_size", 8)),
        per_device_eval_batch_size=int(params.get("per_device_eval_batch_size", 8)),
        eval_steps=int(params.get("eval_steps", 2000)),
        save_steps=int(params.get("save_steps", 2000)),
        seed=int(params.get("seed", 42)),
    )

    msg = _promote_with_versions(
        work_dir=work_dir,
        final_path=HERBERT_FINAL,
        versions_dir=HERBERT_VERSIONS,
        model_name="herbert",
        params={k: v for k, v in params.items() if k != "keep_last"},
        metrics=result.get("metrics"),
        keep_last=keep_last,
    )
    return f"HerBERT finetuning zakończony. {msg} Metryki: {json.dumps(result.get('metrics', {}), ensure_ascii=False)}"


# ======================================================================
# XGBOOST (retrain + wersjonowanie + swap final_model)
# ======================================================================
def retrain_xgboost(params: dict | None = None) -> str:
    """
    Trenuje XGBoost (embeddingi z aktualnego HerBERT 'final_model') i podmienia
    folder 'xg_boost/final_model', wersje trafiają do 'xg_boost/versions'.

    WYMAGANE w `params`:
      - csv_path  (CSV zbudowany z wybranych ankiet/badań przez UI)

    Opcjonalne:
      - xgb_params, numeric_cols, categorical_cols
      - keep_last (ile wersji trzymać)
    """
    from .xgboost_engine import retrain_xgb as _train

    _ensure_dirs(XGB_DIR, XGB_VERSIONS)
    ts = _timestamp()
    work_dir = XGB_DIR / f"_new_{ts}"
    _ensure_dirs(work_dir)

    params = params or {}
    keep_last = int(params.get("keep_last", 20))

    # WYMAGAMY csv_path – bez domyślnej ścieżki
    csv_path = params.get("csv_path")
    if not csv_path:
        raise FileNotFoundError(
            "Brak 'csv_path'. Ten retraining zakłada CSV zbudowane z wybranych ankiet/badań (przychodzi z formularza ML Lab)."
        )
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV nie istnieje: {csv_path}")

    result = _train(
        output_dir=str(work_dir),                 # zapis bezpośrednio do work_dir
        csv_path=str(csv_path),
        herbert_model_dir=str(HERBERT_FINAL),
        xgb_params=params.get("xgb_params"),
        numeric_cols=params.get("numeric_cols"),
        categorical_cols=params.get("categorical_cols"),
    )

    msg = _promote_with_versions(
        work_dir=work_dir,
        final_path=XGB_FINAL,
        versions_dir=XGB_VERSIONS,
        model_name="xgboost",
        params={k: v for k, v in params.items() if k != "keep_last"},
        metrics=result.get("metrics"),
        keep_last=keep_last,
    )
    return f"XGBoost retraining zakończony. {msg} Metryki: {json.dumps(result.get('metrics', {}), ensure_ascii=False)}"
