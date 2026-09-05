from __future__ import annotations

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

try:
    import faiss  # type: ignore
except Exception as e:
    raise RuntimeError(
        "Pakiet 'faiss' jest wymagany do RAG. Zainstaluj np. faiss-cpu."
    ) from e


# --------------------------- ścieżki ---------------------------

def _default_base_dir() -> Path:
    """
    Domyślne położenie katalogu RAG:
    predictionModels/services/models/rag
    (plik ten znajduje się w predictionModels/service/...)
    """
    return Path(__file__).resolve().parent.parent / "services" / "models" / "rag"


def _resolve_base_dir(base_dir: str | os.PathLike | None) -> Path:
    return Path(base_dir) if base_dir else _default_base_dir()


def _paths(base_dir: Path) -> Dict[str, Path]:
    return {
        "defs_dir": base_dir / "definitions_of_specjalists",
        "books_dir": base_dir / "books",
        "notes_dir": base_dir / "notes",
        "notes_file": base_dir / "notes" / "notatki.txt",
        "index": base_dir / "defs_index.faiss",
        "meta": base_dir / "defs_meta.pkl",
        "chunks": base_dir / "defs_chunks.pkl",
    }


# --------------------------- I/O ---------------------------

def _load_pdfs(folder: Path) -> Tuple[List[str], List[str]]:
    docs, names = [], []
    if not folder.exists():
        return docs, names
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(".pdf"):
            continue
        p = folder / fname
        try:
            reader = PdfReader(str(p))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
            if text.strip():
                docs.append(text)
                names.append(fname)
        except Exception:
            # nie wywracaj indeksowania przez jeden PDF
            continue
    return docs, names


def _load_txts(folder: Path) -> Tuple[List[str], List[str]]:
    docs, names = [], []
    if not folder.exists():
        return docs, names
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(".txt"):
            continue
        p = folder / fname
        try:
            with open(p, encoding="utf-8") as f:
                txt = f.read()
            if txt.strip():
                docs.append(txt)
                names.append(fname)
        except Exception:
            continue
    return docs, names


def _chunk(text: str, size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    out = []
    for i in range(0, len(words), max(1, size - overlap)):
        out.append(" ".join(words[i:i + size]))
    return out


# --------------------------- public API ---------------------------

def build_index(
    base_dir: str | os.PathLike | None = None,
    emb_model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> Dict[str, int]:
    """
    Zbuduj indeks FAISS z:
      - rag/definitions_of_specjalists/*.txt
      - rag/books/*.pdf
      - rag/notes/notatki.txt (jeśli istnieje)

    Zapisuje:
      - defs_index.faiss
      - defs_meta.pkl
      - defs_chunks.pkl

    Zwraca: {"n_docs": int, "n_chunks": int}
    """
    base = _resolve_base_dir(base_dir)
    p = _paths(base)
    base.mkdir(parents=True, exist_ok=True)
    p["defs_dir"].mkdir(parents=True, exist_ok=True)
    p["books_dir"].mkdir(parents=True, exist_ok=True)
    p["notes_dir"].mkdir(parents=True, exist_ok=True)

    # 1) wczytaj dokumenty
    txt_docs, txt_names = _load_txts(p["defs_dir"])
    pdf_docs, pdf_names = _load_pdfs(p["books_dir"])

    # notatki (jeden plik)
    note_docs, note_names = [], []
    if p["notes_file"].exists():
        try:
            note_docs = [p["notes_file"].read_text(encoding="utf-8")]
            note_names = [p["notes_file"].name]
        except Exception:
            pass

    docs = txt_docs + pdf_docs + note_docs
    names = txt_names + pdf_names + note_names

    # 2) chunkowanie
    chunks: List[str] = []
    meta: List[Dict] = []
    for doc_id, (text, name) in enumerate(zip(docs, names)):
        for idx, ch in enumerate(_chunk(text, size=chunk_size, overlap=chunk_overlap)):
            if not ch.strip():
                continue
            chunks.append(ch)
            meta.append({"doc_id": doc_id, "doc_name": name, "chunk_idx": idx})

    # 3) embeddingi + FAISS (cosine/IP)
    if not chunks:
        # wyczyść ewentualny stary indeks i wyjdź
        for k in ("index", "meta", "chunks"):
            try:
                p[k].unlink(missing_ok=True)  # type: ignore[index]
            except Exception:
                pass
        return {"n_docs": 0, "n_chunks": 0}

    embedder = SentenceTransformer(emb_model_id)
    emb = embedder.encode(
        chunks,
        batch_size=64,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,
    ).astype("float32")

    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    # 4) zapisz artefakty
    faiss.write_index(index, str(p["index"]))
    with open(p["meta"], "wb") as f:
        pickle.dump(meta, f)
    with open(p["chunks"], "wb") as f:
        pickle.dump(chunks, f)

    return {"n_docs": len(docs), "n_chunks": len(chunks)}


def query(
    question: str,
    k: int = 5,
    base_dir: str | os.PathLike | None = None,
    emb_model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> List[Dict]:
    """
    Przeszukaj zbudowany indeks. Zwraca listę hitów:
    [
      {rank, score, doc_name, chunk_idx, text}
    ]
    """
    base = _resolve_base_dir(base_dir)
    p = _paths(base)

    if not (p["index"].exists() and p["meta"].exists() and p["chunks"].exists()):
        raise FileNotFoundError(
            f"Brak artefaktów RAG w {base}. Uruchom najpierw build_index()."
        )

    # wczytaj indeks/metadata
    index = faiss.read_index(str(p["index"]))
    with open(p["meta"], "rb") as f:
        meta = pickle.load(f)
    with open(p["chunks"], "rb") as f:
        chunks = pickle.load(f)

    embedder = SentenceTransformer(emb_model_id)
    q_vec = embedder.encode([question], normalize_embeddings=True).astype("float32")
    D, I = index.search(q_vec, k)
    I = I[0]
    D = D[0]

    hits: List[Dict] = []
    for rank, (idx, score) in enumerate(zip(I.tolist(), D.tolist()), start=1):
        if idx < 0 or idx >= len(chunks):
            continue
        m = meta[idx]
        hits.append({
            "rank": rank,
            "score": float(score),
            "doc_name": m.get("doc_name"),
            "chunk_idx": int(m.get("chunk_idx", 0)),
            "text": chunks[idx],
        })
    return hits
