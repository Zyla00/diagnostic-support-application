# predictionModels/services/models/xgboost_engine.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import json
import math

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
import xgboost as xgb

# Reużywamy gotowe składanie pól z ankiet:
from predictionModels.services.models.herbert_engine import (
    build_payload_from_surveys as _build_text_from_surveys,
    FIELD_JOINER, FIELD_FORMAT,
)

# --- Ścieżki (lokalne, jak u Ciebie w repo) ---
_THIS_DIR = Path(__file__).resolve().parent
HERBERT_DIR = _THIS_DIR / "her_bert" / "final_model"       # checkpoint HerBERT do embeddingów
XGB_DIR     = _THIS_DIR / "xg_boost"
XGB_MODEL   = XGB_DIR / "model.json"                        # wytrenowany booster
XGB_LABELS  = XGB_DIR / "label_encoder.json"                # {"classes": ["Choroba zakażna", ...]}

# --- Konfiguracja pól z badań (dopasowanie po fragmencie nazwy testu) ---
# Jeśli zaznaczysz JAKIEKOLWIEK badanie, spróbujemy wyciągnąć te pola.
# UZUPEŁNIJ / ZMIEŃ listę pod swoje nazwy testów:
LAB_FIELDS_CONFIG: List[Dict[str, str]] = [
    {"key": "lab_crp",             "match": "crp"},
    {"key": "lab_glukoza",         "match": "glukoza"},
    {"key": "lab_hb",              "match": "hemoglob"},
    {"key": "lab_tsh",             "match": "tsh"},
    {"key": "lab_ldl",             "match": "ldl"},
    {"key": "lab_hdl",             "match": "hdl"},
    {"key": "lab_tc",              "match": "cholesterol całkow"},
    {"key": "lab_trig",            "match": "triglicery"},

    # Biochemia
    {"key": "lab_alt",             "match": "alt"},
    {"key": "lab_ast",             "match": "ast"},
    {"key": "lab_alp",             "match": "alp"},
    {"key": "lab_ggt",             "match": "ggt"},                # obejmie też "ggtp"
    {"key": "lab_albumina",        "match": "albumin"},
    {"key": "lab_bialko_calk",     "match": "białko całkow"},
    {"key": "lab_mocznik",         "match": "mocznik"},            # (BUN)
    {"key": "lab_kreatynina",      "match": "kreatynin"},
    {"key": "lab_bilirubina_calk", "match": "bilirubina całk"},
    {"key": "lab_kwas_moczowy",    "match": "kwas mocz"},
    {"key": "lab_sod",             "match": "sód"},
    {"key": "lab_potas",           "match": "potas"},
    {"key": "lab_chlorki",         "match": "chlork"},
    {"key": "lab_egfr",            "match": "egfr"},
    {"key": "lab_apob",            "match": "apob"},

    # Hematologia (morfologia + rozmaz)
    {"key": "lab_wbc",             "match": "wbc"},
    {"key": "lab_rbc",             "match": "rbc"},
    {"key": "lab_hct",             "match": "hematokryt"},
    {"key": "lab_mcv",             "match": "mcv"},
    {"key": "lab_mch",             "match": "mch"},
    {"key": "lab_mchc",            "match": "mchc"},
    {"key": "lab_rdw",             "match": "rdw"},
    {"key": "lab_plt",             "match": "płytk"},
    {"key": "lab_neut_abs",        "match": "neutrofil"},
    {"key": "lab_lymph_abs",       "match": "limfocyt"},
    {"key": "lab_mono_abs",        "match": "monocyt"},
    {"key": "lab_eos_abs",         "match": "eozynofil"},
    {"key": "lab_baso_abs",        "match": "bazofil"},

    # Parametry życiowe
    {"key": "lab_temp",            "match": "temperatur"},
]

# Jak działa dopasowanie: sprawdzamy czy fragment `match` (lowercase, bez polskich znaków)
# znajduje się w nazwie testu (też znormalizowanej).

# --- Inicjalizacja modeli (lazy) ---
_device = "cuda" if torch.cuda.is_available() else "cpu"
_emb_tok: Optional[AutoTokenizer] = None
_emb_model: Optional[AutoModel] = None
_booster: Optional[xgb.Booster] = None
_label_order: List[str] = []  # ładne nazwy klas (w kolejności indeksów 0..N-1)

# ---------- utils ----------
import unicodedata
def _norm(s: str) -> str:
    s = s or ""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")

def _ensure_herbert():
    global _emb_tok, _emb_model
    if _emb_tok is None or _emb_model is None:
        _emb_tok = AutoTokenizer.from_pretrained(HERBERT_DIR)
        # baza transformera (bez głowy klasyfikacyjnej)
        _emb_model = AutoModel.from_pretrained(HERBERT_DIR).to(_device)
        _emb_model.eval()

def _ensure_xgb():
    global _booster, _label_order
    if _booster is None:
        if not XGB_MODEL.exists():
            raise FileNotFoundError(f"Nie znaleziono modelu XGBoost: {XGB_MODEL}")
        _booster = xgb.Booster()
        _booster.load_model(str(XGB_MODEL))
    if not _label_order:
        # czytamy przyjazne nazwy klas
        classes = []
        if XGB_LABELS.exists():
            try:
                with open(XGB_LABELS, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and isinstance(data.get("classes"), list):
                    classes = [str(x) for x in data["classes"]]
            except Exception:
                pass
        # fallback gdy brak pliku
        if not classes:
            # próbujemy odczytać liczbę klas z atrybutów boostera
            try:
                num_class = int(_booster.attr("num_class") or "0")
            except Exception:
                num_class = 0
            classes = [f"class_{i}" for i in range(max(num_class, 2))]
        _label_order = classes

def _mean_pool(last_hidden, attention_mask):
    # last_hidden: (1, T, H), mask: (1,T)
    mask = attention_mask.unsqueeze(-1).type_as(last_hidden)  # (1,T,1)
    summed = (last_hidden * mask).sum(dim=1)                   # (1,H)
    denom = mask.sum(dim=1).clamp(min=1.0)                     # (1,1)
    return (summed / denom).squeeze(0)                         # (H,)

def _embed_text(text: str, max_length: int = 512) -> np.ndarray:
    _ensure_herbert()
    enc = _emb_tok(text, truncation=True, max_length=max_length, padding=False, return_tensors="pt").to(_device)
    with torch.no_grad():
        out = _emb_model(**enc)
        # CLS też ok, ale mean pooling bywa stabilniejszy:
        vec = _mean_pool(out.last_hidden_state, enc["attention_mask"]).detach().cpu().numpy().astype("float32")
    return vec  # (H,)

# ---------- laboratoria ----------
def _iter_lab_entries(labs: List[Any]):
    """
    Zwraca iterator wpisów laboratoryjnych (LabResultEntry) dla podanych survey.
    Import w środku, żeby nie robić zależności przy imporcie modułu.
    """
    try:
        from labTest.models import LabResultEntry
    except Exception:
        return []
    ids = [getattr(l, "id", None) for l in labs if getattr(l, "id", None) is not None]
    if not ids:
        return []
    return LabResultEntry.objects.filter(survey_id__in=ids)

def _extract_labs_kv(labs: List[Any]) -> Dict[str, str]:
    """
    Filtrowanie wyników badań pod zadaną listę pól (LAB_FIELDS_CONFIG).
    Zwraca {key: "wartość [jednostka]"} lub "" gdy nie znaleziono.
    """
    out = {c["key"]: "" for c in LAB_FIELDS_CONFIG}
    entries = list(_iter_lab_entries(labs))
    if not entries:
        return out

    def _val(e):
        v = getattr(e, "value", None) or getattr(e, "result", None) or getattr(e, "result_value", None)
        u = getattr(e, "unit", None)
        v = (str(v).strip() if v is not None else "").replace("\n", " ")
        u = (str(u).strip() if isinstance(u, str) else "")
        return f"{v} {u}".strip() if v else ""

    for e in entries:
        name = getattr(e, "test_name", None) or getattr(e, "name", None) or ""
        nm = _norm(name)
        for c in LAB_FIELDS_CONFIG:
            if c["key"] in out and out[c["key"]]:  # już ustawione pierwsze trafienie
                continue
            if _norm(c["match"]) in nm:
                out[c["key"]] = _val(e)
    return out

# ---------- składanie tekstu (ankiety + lab) ----------
def build_text_from_surveys_and_labs(surveys: List[Any], labs: List[Any]) -> Tuple[str, Dict[str, Dict[str, str]]]:
    """
    1) Zbiera TYLKO dozwolone pola z TYLKO dozwolonych ankiet (dokładnie jak w HerBERT).
    2) Jeśli są badania, wybiera wskazane testy i dorzuca do payloadu jako kolejne pary {key=wartość}.
    """
    base_text, used_surv = _build_text_from_surveys(surveys)  # 'plec=... [SEP] ...'
    used: Dict[str, Dict[str, str]] = {"surveys": {}}
    used["surveys"] = {aname: kv for aname, kv in (used_surv or {}).items()}

    fields = [base_text] if base_text else []

    if labs:
        labs_map = _extract_labs_kv(labs)
        used["labs"] = labs_map
        # dorzucamy do tekstu jako kolejne pary w tym samym formacie
        for k, v in labs_map.items():
            fields.append(FIELD_FORMAT.format(key=k, val=(v if v else "none")))

    payload = FIELD_JOINER.join([f for f in fields if f])
    return payload, used

# ---------- predykcja ----------
def _softmax(x: np.ndarray) -> np.ndarray:
    x = x.astype("float64")
    m = np.max(x)
    exps = np.exp(x - m)
    return exps / np.sum(exps)

def predict_from_surveys_and_labs(surveys: List[Any], labs: List[Any]) -> Dict[str, Any]:
    """
    Główna funkcja: zwraca wynik w tym samym kształcie co HerBERT:
    {
      "predicted_label": "...",
      "classes": [{"label": "...", "prob": 0.123, "percent": 12.3}, ...],
      "raw_features": { "surveys": {...}, "labs": {...} },
      "raw_payload": "plec=... [SEP] lab_crp=... [SEP] ..."
    }
    """
    _ensure_xgb()

    text, used = build_text_from_surveys_and_labs(surveys, labs)
    if not text:
        raise ValueError("Brak danych wejściowych (ankiety/laby) do obliczenia embeddingu.")

    vec = _embed_text(text)                               # (H,)
    dmat = xgb.DMatrix(vec.reshape(1, -1))                # (1,H)

    # XGBoost może zwrócić:
    # - (1, K) — softprob
    # - (1,)   — prawdopodobieństwo klasy pozytywnej przy binarce (logistic)
    raw = _booster.predict(dmat)
    if raw.ndim == 2:
        probs = raw[0]  # (K,)
    elif raw.ndim == 1 and len(_label_order) == 2:
        p = float(raw[0])
        probs = np.array([1.0 - p, p], dtype="float64")
    else:
        # ostatnia deska ratunku — normalizacja
        probs = _softmax(raw.reshape(-1))

    # kontrola długości
    K = len(_label_order)
    if probs.shape[0] != K:
        # dopasuj przez przycięcie/padding (żeby nie wywalić UI) i wyraźny sygnał
        if probs.shape[0] > K:
            probs = probs[:K]
        else:
            probs = np.pad(probs, (0, K - probs.shape[0]), constant_values=0.0)

    classes = []
    for i, p in enumerate(probs):
        lbl = _label_order[i] if i < len(_label_order) else f"class_{i}"
        classes.append({"label": lbl, "prob": float(p), "percent": float(p * 100.0)})

    top = max(classes, key=lambda d: d["prob"])
    return {
        "predicted_label": top["label"],
        "classes": classes,
        "raw_features": used,
        "raw_payload": text,
    }
