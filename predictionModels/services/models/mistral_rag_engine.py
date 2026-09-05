# from __future__ import annotations
# import os
# import pickle
# import threading
# from pathlib import Path
# from typing import List, Tuple, Dict, Any
#
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from PyPDF2 import PdfReader
#
# from django.conf import settings
# from predictionModels.services.models.mistral_engine import generate_text
#
# EMB_MODEL_ID = os.getenv("RAG_EMB_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")
# MAX_CHARS_PER_CHUNK = int(os.getenv("RAG_MAX_CHARS_PER_CHUNK", "700"))
# CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))
# CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
#
# def _p(x):  # helper
#     return x if isinstance(x, Path) else Path(x)
#
# def _resolve_paths() -> Dict[str, Path]:
#     base_dir = _p(getattr(settings, "BASE_DIR", Path.cwd()))
#
#     # 1) rag_base: ENV -> settings -> domyślnie "rag"
#     rag_base_cfg = os.getenv("RAG_BASE_DIR") or getattr(settings, "RAG_BASE_DIR", "rag")
#     rag_base = _p(rag_base_cfg)
#     if not rag_base.is_absolute():
#         rag_base = base_dir / rag_base
#
#     # 2) TXT/PDF: ENV -> settings -> domyślne nazwy folderów
#     txt_cfg = os.getenv("RAG_TXT_DIR") or getattr(settings, "RAG_TXT_DIR", "definitions_of_specjalists")
#     pdf_cfg = os.getenv("RAG_PDF_DIR") or getattr(settings, "RAG_PDF_DIR", "books")
#
#     # jeśli to nazwy katalogów, zbuduj w oparciu o rag_base; jeśli to ścieżki, uszanuj
#     txt_dir = _p(txt_cfg)
#     if not txt_dir.is_absolute():
#         txt_dir = rag_base / txt_cfg
#
#     pdf_dir = _p(pdf_cfg)
#     if not pdf_dir.is_absolute():
#         pdf_dir = rag_base / pdf_cfg
#
#     # 3) artefakty: ENV nadpisuje lokalizację zapisu/odczytu
#     index_path  = _p(os.getenv("RAG_INDEX_PATH",  rag_base / "defs_index.faiss"))
#     meta_path   = _p(os.getenv("RAG_META_PATH",   rag_base / "defs_meta.pkl"))
#     chunks_path = _p(os.getenv("RAG_CHUNKS_PATH", rag_base / "defs_chunks.pkl"))
#
#     return dict(
#         RAG_BASE=rag_base, TXT_DIR=txt_dir, PDF_DIR=pdf_dir,
#         INDEX_PATH=index_path, META_PATH=meta_path, CHUNKS_PATH=chunks_path
#     )
#
#
# PATHS = _resolve_paths()
#
# # ---------- BUDOWA INDEKSU (gdy brak artefaktów) ----------
# def _load_pdfs(folder: Path):
#     docs, names = [], []
#     if not folder.exists():
#         return docs, names
#     for p in sorted(folder.iterdir()):
#         if p.is_file() and p.suffix.lower() == ".pdf":
#             try:
#                 reader = PdfReader(str(p))
#                 text = "\n".join((page.extract_text() or "") for page in reader.pages)
#                 text = (text or "").strip()
#                 if text:
#                     docs.append(text)
#                     names.append(p.name)
#             except Exception:
#                 # PDF-y bywają problematyczne — pomijamy ciche błędy
#                 continue
#     return docs, names
#
# def _load_txts(folder: Path):
#     docs, names = [], []
#     if not folder.exists():
#         return docs, names
#     for p in sorted(folder.iterdir()):
#         if p.is_file() and p.suffix.lower() == ".txt":
#             try:
#                 txt = p.read_text(encoding="utf-8", errors="ignore")
#                 txt = (txt or "").strip()
#                 if txt:
#                     docs.append(txt)
#                     names.append(p.name)
#             except Exception:
#                 continue
#     return docs, names
#
# def _chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
#     words = text.split()
#     step = max(1, size - overlap)
#     for i in range(0, len(words), step):
#         yield " ".join(words[i:i+size])
#
# def build_index_from_folders(txt_dir: Path = PATHS["TXT_DIR"], pdf_dir: Path = PATHS["PDF_DIR"],
#                              index_path: Path = PATHS["INDEX_PATH"], meta_path: Path = PATHS["META_PATH"],
#                              chunks_path: Path = PATHS["CHUNKS_PATH"]) -> None:
#     """Buduje artefakty FAISS z folderów TXT+PDF i zapisuje w rag/."""
#     txt_docs, txt_names = _load_txts(txt_dir)
#     pdf_docs, pdf_names = _load_pdfs(pdf_dir)
#     docs = txt_docs + pdf_docs
#     names = txt_names + pdf_names
#
#     chunks, meta = [], []
#     for doc_id, (text, name) in enumerate(zip(docs, names)):
#         for cidx, ch in enumerate(_chunk(text)):
#             chunks.append(ch)
#             meta.append({"doc_id": doc_id, "doc_name": name, "chunk_idx": cidx})
#
#     if not chunks:
#         raise RuntimeError("Brak danych do zbudowania indeksu (puste foldery TXT/PDF).")
#
#     embedder = SentenceTransformer(EMB_MODEL_ID)
#     emb = embedder.encode(
#         chunks, batch_size=64, convert_to_numpy=True,
#         show_progress_bar=False, normalize_embeddings=True
#     ).astype("float32")
#
#     index = faiss.IndexFlatIP(emb.shape[1])  # IP ~ cosine (po normalizacji)
#     index.add(emb)
#
#     index_path.parent.mkdir(parents=True, exist_ok=True)
#     faiss.write_index(index, str(index_path))
#     with open(meta_path, "wb") as f: pickle.dump(meta, f)
#     with open(chunks_path, "wb") as f: pickle.dump(chunks, f)
#
# # ---------- SINGLETON ----------
# class _RagSingleton:
#     _instance = None
#     _init_lock = threading.Lock()
#
#     def __init__(self):  # pragma: no cover
#         raise RuntimeError("Użyj _RagSingleton.get()")
#
#     @classmethod
#     def get(cls, auto_build_if_missing: bool = True):
#         if cls._instance is None:
#             with cls._init_lock:
#                 if cls._instance is None:
#                     cls._instance = cls._create(auto_build_if_missing=auto_build_if_missing)
#         return cls._instance
#
#     @classmethod
#     def _create(cls, auto_build_if_missing: bool):
#         paths = PATHS
#         index_p, meta_p, chunks_p = paths["INDEX_PATH"], paths["META_PATH"], paths["CHUNKS_PATH"]
#
#         have_all = index_p.exists() and meta_p.exists() and chunks_p.exists()
#         if not have_all:
#             if not auto_build_if_missing:
#                 missing = [str(p) for p in (index_p, meta_p, chunks_p) if not p.exists()]
#                 raise FileNotFoundError(f"Brak artefaktów RAG: {missing}")
#             # budujemy na szybko
#             build_index_from_folders()
#
#         # wczytanie
#         index = faiss.read_index(str(index_p))
#         with open(meta_p, "rb") as f: meta = pickle.load(f)
#         with open(chunks_p, "rb") as f: chunks = pickle.load(f)
#
#         embedder = SentenceTransformer(EMB_MODEL_ID)
#         lock = threading.Lock()
#
#         obj = object.__new__(cls)
#         obj.index = index
#         obj.meta = meta
#         obj.chunks = chunks
#         obj.embedder = embedder
#         obj.encode_lock = lock
#         return obj
#
# # ---------- API: RETRIEVAL + GENERATION ----------
# def retrieve(question: str, k: int = 3) -> List[Dict[str, Any]]:
#     rag = _RagSingleton.get()
#     with rag.encode_lock:
#         q_vec = rag.embedder.encode([question], normalize_embeddings=True).astype("float32")
#     D, I = rag.index.search(np.asarray(q_vec), k)
#
#     results: List[Dict[str, Any]] = []
#     for rank, (idx, score) in enumerate(zip(I[0].tolist(), D[0].tolist()), start=1):
#         m = rag.meta[idx]
#         results.append({
#             "rank": rank,
#             "score": float(score),
#             "text": rag.chunks[idx],
#             "doc_name": m.get("doc_name"),
#             "doc_id": m.get("doc_id"),
#             "chunk_idx": m.get("chunk_idx"),
#         })
#     return results
#
# def build_rag_block(hits: List[Dict[str, Any]], max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK) -> str:
#     lines = ["### Materiały referencyjne (RAG) – fragmenty:"]
#     for h in hits:
#         txt = (h["text"] or "").strip().replace("\r", " ")
#         if not txt:
#             continue
#         snippet = txt[:max_chars_per_chunk]
#         if len(txt) > max_chars_per_chunk:
#             snippet += "…"
#         label = f"{h.get('doc_name', 'źródło')} (chunk {h.get('chunk_idx')}, score {h.get('score'):.3f})"
#         lines.append(f"- {label}:\n  {snippet}")
#     return "\n".join(lines)
#
# def augment_prompt_with_rag(final_prompt: str, question_for_retrieval: str, k: int = 3,
#                             max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK) -> Tuple[str, List[Dict[str, Any]]]:
#     hits = retrieve(question_for_retrieval, k=k)
#     rag_block = build_rag_block(hits, max_chars_per_chunk=max_chars_per_chunk)
#     augmented = f"{rag_block}\n\n{final_prompt}"
#     return augmented, hits
#
# def generate_with_rag(final_prompt: str,
#                       question_for_retrieval: str,
#                       k: int = 3,
#                       max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK,
#                       gen_kwargs: Dict[str, Any] = None) -> Tuple[str, List[Dict[str, Any]], str]:
#     augmented_prompt, hits = augment_prompt_with_rag(
#         final_prompt, question_for_retrieval, k=k, max_chars_per_chunk=max_chars_per_chunk
#     )
#     gen_kwargs = gen_kwargs or {}
#     text = generate_text(augmented_prompt, **gen_kwargs)
#     return text, hits, augmented_prompt
#
# # Opcjonalnie: ręczna odbudowa indeksu (np. po dodaniu nowych plików)
# def rebuild_index() -> None:
#     build_index_from_folders()
#     # reset singletona
#     _RagSingleton._instance = None

# from __future__ import annotations
# import os
# import pickle
# import threading
# from pathlib import Path
# from typing import List, Tuple, Dict, Any
#
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from PyPDF2 import PdfReader
#
# from django.conf import settings
# from predictionModels.services.models.mistral_engine import generate_text
#
# # --- tryb offline (żeby nic nie pobierało się z sieci) ---
# os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
# os.environ.setdefault("HF_HUB_OFFLINE", "1")
#
# # Konfiguracja embeddera:
# # - jeśli ustawisz RAG_EMB_MODEL_DIR → będzie użyta lokalna ścieżka
# # - w przeciwnym razie RAG_EMB_MODEL_ID (domyślnie: all-MiniLM-L6-v2 z lokalnego cache)
# EMB_MODEL_DIR = os.getenv("RAG_EMB_MODEL_DIR", "").strip()
# EMB_MODEL_ID = os.getenv("RAG_EMB_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2").strip()
#
# MAX_CHARS_PER_CHUNK = int(os.getenv("RAG_MAX_CHARS_PER_CHUNK", "700"))
# CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))
# CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
#
#
# # ------------------------ utils: ścieżki ------------------------
#
# def _p(x):  # Path helper
#     return x if isinstance(x, Path) else Path(str(x))
#
# def _norm_to_path(candidate: str | Path, base: Path) -> Path:
#     """
#     Zamień string (w tym z backslashami) na Path względem BASE_DIR/tego pliku,
#     jeśli nie jest absolutny.
#     """
#     if isinstance(candidate, Path):
#         p = candidate
#     else:
#         p = Path(candidate.replace("\\", "/")).expanduser()
#
#     if not p.is_absolute():
#         p = (base / p).resolve()
#     return p
#
# def _resolve_paths() -> Dict[str, Path]:
#     # spróbuj wziąć BASE_DIR z settings, w innym wypadku katalog projektu
#     base_dir = _p(getattr(settings, "BASE_DIR", Path(__file__).resolve().parents[4]))
#
#     # 1) bazowy katalog RAG
#     rag_base_cfg = os.getenv("RAG_BASE_DIR") or getattr(settings, "RAG_BASE_DIR", "rag")
#     rag_base = _norm_to_path(rag_base_cfg, base_dir)
#
#     # 2) katalogi z danymi (TXT/PDF)
#     txt_cfg = os.getenv("RAG_TXT_DIR") or getattr(settings, "RAG_TXT_DIR", "definitions_of_specjalists")
#     pdf_cfg = os.getenv("RAG_PDF_DIR") or getattr(settings, "RAG_PDF_DIR", "books")
#
#     txt_dir = _norm_to_path(txt_cfg, rag_base) if not _p(txt_cfg).is_absolute() else _p(txt_cfg)
#     pdf_dir = _norm_to_path(pdf_cfg, rag_base) if not _p(pdf_cfg).is_absolute() else _p(pdf_cfg)
#
#     # 3) artefakty
#     index_path  = _norm_to_path(os.getenv("RAG_INDEX_PATH",  rag_base / "defs_index.faiss"), base_dir)
#     meta_path   = _norm_to_path(os.getenv("RAG_META_PATH",   rag_base / "defs_meta.pkl"),   base_dir)
#     chunks_path = _norm_to_path(os.getenv("RAG_CHUNKS_PATH", rag_base / "defs_chunks.pkl"), base_dir)
#
#     return dict(
#         BASE_DIR=base_dir,
#         RAG_BASE=rag_base,
#         TXT_DIR=txt_dir,
#         PDF_DIR=pdf_dir,
#         INDEX_PATH=index_path,
#         META_PATH=meta_path,
#         CHUNKS_PATH=chunks_path,
#     )
#
# PATHS = _resolve_paths()
#
#
# # --------------------- ładowanie dokumentów ---------------------
#
# def _load_pdfs(folder: Path):
#     docs, names = [], []
#     if not folder.exists():
#         return docs, names
#     for p in sorted(folder.iterdir()):
#         if p.is_file() and p.suffix.lower() == ".pdf":
#             try:
#                 reader = PdfReader(str(p))
#                 text = "\n".join((page.extract_text() or "") for page in reader.pages)
#                 text = (text or "").strip()
#                 if text:
#                     docs.append(text)
#                     names.append(p.name)
#             except Exception:
#                 # PDF-y bywają problematyczne — pomijamy ciche błędy
#                 continue
#     return docs, names
#
# def _load_txts(folder: Path):
#     docs, names = [], []
#     if not folder.exists():
#         return docs, names
#     for p in sorted(folder.iterdir()):
#         if p.is_file() and p.suffix.lower() == ".txt":
#             try:
#                 txt = p.read_text(encoding="utf-8", errors="ignore")
#                 txt = (txt or "").strip()
#                 if txt:
#                     docs.append(txt)
#                     names.append(p.name)
#             except Exception:
#                 continue
#     return docs, names
#
# def _chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
#     # proste chunkowanie po słowach
#     words = text.split()
#     step = max(1, size - overlap)
#     for i in range(0, len(words), step):
#         yield " ".join(words[i:i + size])
#
#
# # --------------------- embedder (lokalny lub ID) ---------------------
#
# def _load_embedder() -> SentenceTransformer:
#     """
#     Zwraca SentenceTransformer:
#     - jeśli wskazano RAG_EMB_MODEL_DIR → użyje tej lokalnej ścieżki,
#     - w przeciwnym wypadku użyje RAG_EMB_MODEL_ID (z lokalnego cache).
#     """
#     base_for_rel = PATHS["BASE_DIR"]
#     if EMB_MODEL_DIR:
#         local_dir = _norm_to_path(EMB_MODEL_DIR, base_for_rel)
#         if not local_dir.exists():
#             raise FileNotFoundError(
#                 f"[RAG] RAG_EMB_MODEL_DIR wskazuje na nieistniejący katalog: {local_dir}"
#             )
#         return SentenceTransformer(str(local_dir))
#     # fallback: model ID (musi być w lokalnym cache przy OFFLINE)
#     return SentenceTransformer(EMB_MODEL_ID)
#
#
# # --------------------- budowa indeksu FAISS ---------------------
#
# def build_index_from_folders(
#     txt_dir: Path = PATHS["TXT_DIR"],
#     pdf_dir: Path = PATHS["PDF_DIR"],
#     index_path: Path = PATHS["INDEX_PATH"],
#     meta_path: Path = PATHS["META_PATH"],
#     chunks_path: Path = PATHS["CHUNKS_PATH"],
# ) -> None:
#     """Buduje artefakty FAISS z folderów TXT + PDF i zapisuje do plików."""
#     txt_docs, txt_names = _load_txts(txt_dir)
#     pdf_docs, pdf_names = _load_pdfs(pdf_dir)
#     docs = txt_docs + pdf_docs
#     names = txt_names + pdf_names
#
#     chunks, meta = [], []
#     for doc_id, (text, name) in enumerate(zip(docs, names)):
#         for cidx, ch in enumerate(_chunk(text)):
#             chunks.append(ch)
#             meta.append({"doc_id": doc_id, "doc_name": name, "chunk_idx": cidx})
#
#     if not chunks:
#         raise RuntimeError(
#             f"[RAG] Brak danych do zbudowania indeksu. TXT_DIR={txt_dir}, PDF_DIR={pdf_dir} są puste?"
#         )
#
#     embedder = _load_embedder()
#     emb = embedder.encode(
#         chunks,
#         batch_size=64,
#         convert_to_numpy=True,
#         show_progress_bar=False,
#         normalize_embeddings=True,  # potem IP == cosine
#     ).astype("float32")
#
#     index = faiss.IndexFlatIP(emb.shape[1])
#     index.add(emb)
#
#     index_path.parent.mkdir(parents=True, exist_ok=True)
#     faiss.write_index(index, str(index_path))
#     with open(meta_path, "wb") as f:
#         pickle.dump(meta, f)
#     with open(chunks_path, "wb") as f:
#         pickle.dump(chunks, f)
#
#     print(f"[RAG] Index zbudowany. n_chunks={len(chunks)} → {index_path}")
#
#
# # --------------------- singleton RAG ---------------------
#
# class _RagSingleton:
#     _instance = None
#     _init_lock = threading.Lock()
#
#     def __init__(self):  # pragma: no cover
#         raise RuntimeError("Użyj _RagSingleton.get()")
#
#     @classmethod
#     def get(cls, auto_build_if_missing: bool = True):
#         if cls._instance is None:
#             with cls._init_lock:
#                 if cls._instance is None:
#                     cls._instance = cls._create(auto_build_if_missing=auto_build_if_missing)
#         return cls._instance
#
#     @classmethod
#     def _create(cls, auto_build_if_missing: bool):
#         paths = PATHS
#         index_p, meta_p, chunks_p = paths["INDEX_PATH"], paths["META_PATH"], paths["CHUNKS_PATH"]
#
#         have_all = index_p.exists() and meta_p.exists() and chunks_p.exists()
#         if not have_all:
#             if not auto_build_if_missing:
#                 missing = [str(p) for p in (index_p, meta_p, chunks_p) if not p.exists()]
#                 raise FileNotFoundError(f"[RAG] Brak artefaktów: {missing}")
#             # budujemy z lokalnych plików
#             build_index_from_folders()
#
#         # wczytanie
#         index = faiss.read_index(str(index_p))
#         with open(meta_p, "rb") as f:
#             meta = pickle.load(f)
#         with open(chunks_p, "rb") as f:
#             chunks = pickle.load(f)
#
#         embedder = _load_embedder()
#         lock = threading.Lock()
#
#         obj = object.__new__(cls)
#         obj.index = index
#         obj.meta = meta
#         obj.chunks = chunks
#         obj.embedder = embedder
#         obj.encode_lock = lock
#         return obj
#
#
# # --------------------- API: retrieve + generation ---------------------
#
# def retrieve(question: str, k: int = 3) -> List[Dict[str, Any]]:
#     rag = _RagSingleton.get()
#     with rag.encode_lock:
#         q_vec = rag.embedder.encode([question], normalize_embeddings=True).astype("float32")
#     D, I = rag.index.search(np.asarray(q_vec), k)
#
#     results: List[Dict[str, Any]] = []
#     for rank, (idx, score) in enumerate(zip(I[0].tolist(), D[0].tolist()), start=1):
#         m = rag.meta[idx]
#         results.append({
#             "rank": rank,
#             "score": float(score),
#             "text": rag.chunks[idx],
#             "doc_name": m.get("doc_name"),
#             "doc_id": m.get("doc_id"),
#             "chunk_idx": m.get("chunk_idx"),
#         })
#     return results
#
#
# def build_rag_block(hits: List[Dict[str, Any]], max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK) -> str:
#     lines = ["### Materiały referencyjne (RAG) – fragmenty:"]
#     for h in hits:
#         txt = (h["text"] or "").strip().replace("\r", " ")
#         if not txt:
#             continue
#         snippet = txt[:max_chars_per_chunk]
#         if len(txt) > max_chars_per_chunk:
#             snippet += "…"
#         label = f"{h.get('doc_name', 'źródło')} (chunk {h.get('chunk_idx')}, score {h.get('score'):.3f})"
#         lines.append(f"- {label}:\n  {snippet}")
#     return "\n".join(lines)
#
#
# def augment_prompt_with_rag(
#     final_prompt: str,
#     question_for_retrieval: str,
#     k: int = 3,
#     max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK
# ) -> Tuple[str, List[Dict[str, Any]]]:
#     hits = retrieve(question_for_retrieval, k=k)
#     rag_block = build_rag_block(hits, max_chars_per_chunk=max_chars_per_chunk)
#     augmented = f"{rag_block}\n\n{final_prompt}"
#     return augmented, hits
#
#
# def generate_with_rag(
#     final_prompt: str,
#     question_for_retrieval: str,
#     k: int = 3,
#     max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK,
#     gen_kwargs: Dict[str, Any] = None
# ) -> Tuple[str, List[Dict[str, Any]], str]:
#     augmented_prompt, hits = augment_prompt_with_rag(
#         final_prompt, question_for_retrieval, k=k, max_chars_per_chunk=max_chars_per_chunk
#     )
#     gen_kwargs = gen_kwargs or {}
#     text = generate_text(augmented_prompt, **gen_kwargs)
#     return text, hits, augmented_prompt
#
#
# # --------------------- narzędzie: odbuduj indeks ---------------------
#
# def rebuild_index() -> None:
#     build_index_from_folders()
#     # zresetuj singleton (żeby przy następnym wywołaniu wczytał nowe artefakty)
#     _RagSingleton._instance = None


# predictionModels/services/models/mistral_rag_engine.py
from __future__ import annotations
import os
import pickle
import threading
from pathlib import Path
from typing import List, Tuple, Dict, Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader

from django.conf import settings
from predictionModels.services.models.mistral_engine import generate_text

# --- tryb offline (żeby nic nie pobierało się z sieci) ---
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

# Konfiguracja embeddera:
EMB_MODEL_DIR = os.getenv("RAG_EMB_MODEL_DIR", "").strip()
EMB_MODEL_ID = os.getenv("RAG_EMB_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2").strip()

MAX_CHARS_PER_CHUNK = int(os.getenv("RAG_MAX_CHARS_PER_CHUNK", "700"))
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

# ------------------------ utils: ścieżki ------------------------

def _p(x):  # Path helper
    return x if isinstance(x, Path) else Path(str(x))

def _norm_to_path(candidate: str | Path, base: Path) -> Path:
    """Zamień string (także z backslashami) na Path względem `base` jeśli nieabsolutny."""
    p = candidate if isinstance(candidate, Path) else Path(str(candidate).replace("\\", "/")).expanduser()
    return p if p.is_absolute() else (base / p).resolve()

def _code_default_rag_dir() -> Path:
    # Ten plik jest w predictionModels/services/models/ -> domyślny RAG to .../rag
    return Path(__file__).resolve().parent / "rag"

def _resolve_paths() -> Dict[str, Path]:
    # 1) domyślna baza RAG: obok tego pliku (predictionModels/services/models/rag)
    code_default = _code_default_rag_dir()

    # 2) pozwól nadpisać w settings/ENV (opcjonalnie)
    #    - jeśli nie podasz, użyjemy domyślnego code_default
    rag_base_cfg = os.getenv("RAG_BASE_DIR") or getattr(settings, "RAG_BASE_DIR", str(code_default))
    rag_base = _norm_to_path(rag_base_cfg, code_default.parent)

    # podkatalogi
    txt_cfg   = os.getenv("RAG_TXT_DIR")   or getattr(settings, "RAG_TXT_DIR", "definitions_of_specjalists")
    pdf_cfg   = os.getenv("RAG_PDF_DIR")   or getattr(settings, "RAG_PDF_DIR", "books")
    notes_cfg = os.getenv("RAG_NOTES_FILE") or getattr(settings, "RAG_NOTES_FILE", str(rag_base / "notes" / "notatki.txt"))

    txt_dir = _norm_to_path(txt_cfg, rag_base) if not _p(txt_cfg).is_absolute() else _p(txt_cfg)
    pdf_dir = _norm_to_path(pdf_cfg, rag_base) if not _p(pdf_cfg).is_absolute() else _p(pdf_cfg)
    notes_file = _norm_to_path(notes_cfg, rag_base) if not _p(notes_cfg).is_absolute() else _p(notes_cfg)

    # artefakty
    index_path  = _norm_to_path(os.getenv("RAG_INDEX_PATH",  rag_base / "defs_index.faiss"), rag_base)
    meta_path   = _norm_to_path(os.getenv("RAG_META_PATH",   rag_base / "defs_meta.pkl"),   rag_base)
    chunks_path = _norm_to_path(os.getenv("RAG_CHUNKS_PATH", rag_base / "defs_chunks.pkl"), rag_base)

    return dict(
        RAG_BASE=rag_base,
        TXT_DIR=txt_dir,
        PDF_DIR=pdf_dir,
        NOTES_FILE=notes_file,
        INDEX_PATH=index_path,
        META_PATH=meta_path,
        CHUNKS_PATH=chunks_path,
    )

PATHS = _resolve_paths()

# --------------------- ładowanie dokumentów ---------------------

def _load_pdfs(folder: Path) -> Tuple[List[str], List[str]]:
    docs, names = [], []
    if not folder.exists():
        return docs, names
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(str(p))
                text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
                if text:
                    docs.append(text)
                    names.append(p.name)
            except Exception:
                continue
    return docs, names

def _load_txts(folder: Path) -> Tuple[List[str], List[str]]:
    docs, names = [], []
    if not folder.exists():
        return docs, names
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() == ".txt":
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore").strip()
                if txt:
                    docs.append(txt)
                    names.append(p.name)
            except Exception:
                continue
    return docs, names

def _load_notes(notes_file: Path) -> Tuple[List[str], List[str]]:
    """Czyta pojedynczy plik notatek (appendowana kronika)."""
    if notes_file.exists():
        try:
            txt = notes_file.read_text(encoding="utf-8", errors="ignore").strip()
            if txt:
                return [txt], [notes_file.name]
        except Exception:
            pass
    return [], []

def _chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    words = text.split()
    step = max(1, size - overlap)
    for i in range(0, len(words), step):
        yield " ".join(words[i:i + size])

# --------------------- embedder ---------------------

def _load_embedder() -> SentenceTransformer:
    if EMB_MODEL_DIR:
        local_dir = _norm_to_path(EMB_MODEL_DIR, PATHS["RAG_BASE"])
        if not local_dir.exists():
            raise FileNotFoundError(f"[RAG] RAG_EMB_MODEL_DIR nie istnieje: {local_dir}")
        return SentenceTransformer(str(local_dir))
    return SentenceTransformer(EMB_MODEL_ID)

# --------------------- budowa indeksu ---------------------

def build_index_from_folders(
    txt_dir: Path = PATHS["TXT_DIR"],
    pdf_dir: Path = PATHS["PDF_DIR"],
    notes_file: Path = PATHS["NOTES_FILE"],
    index_path: Path = PATHS["INDEX_PATH"],
    meta_path: Path = PATHS["META_PATH"],
    chunks_path: Path = PATHS["CHUNKS_PATH"],
) -> None:
    """Buduje artefakty FAISS z TXT + PDF + NOTATKI i zapisuje do plików."""
    txt_docs, txt_names     = _load_txts(txt_dir)
    pdf_docs, pdf_names     = _load_pdfs(pdf_dir)
    notes_docs, notes_names = _load_notes(notes_file)

    docs  = txt_docs + pdf_docs + notes_docs
    names = txt_names + pdf_names + notes_names

    chunks, meta = [], []
    for doc_id, (text, name) in enumerate(zip(docs, names)):
        for cidx, ch in enumerate(_chunk(text)):
            chunks.append(ch)
            meta.append({"doc_id": doc_id, "doc_name": name, "chunk_idx": cidx})

    if not chunks:
        raise RuntimeError(
            f"[RAG] Brak danych do zbudowania indeksu. TXT={txt_dir}, PDF={pdf_dir}, NOTES={notes_file}"
        )

    embedder = _load_embedder()
    emb = embedder.encode(
        chunks,
        batch_size=64,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,
    ).astype("float32")

    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    with open(meta_path, "wb") as f:
        pickle.dump(meta, f)
    with open(chunks_path, "wb") as f:
        pickle.dump(chunks, f)

    print(f"[RAG] Index zbudowany. n_chunks={len(chunks)} → {index_path}")

# --------------------- singleton RAG ---------------------

class _RagSingleton:
    _instance = None
    _init_lock = threading.Lock()

    def __init__(self):  # pragma: no cover
        raise RuntimeError("Użyj _RagSingleton.get()")

    @classmethod
    def get(cls, auto_build_if_missing: bool = True):
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls._create(auto_build_if_missing=auto_build_if_missing)
        return cls._instance

    @classmethod
    def _create(cls, auto_build_if_missing: bool):
        index_p, meta_p, chunks_p = PATHS["INDEX_PATH"], PATHS["META_PATH"], PATHS["CHUNKS_PATH"]
        have_all = index_p.exists() and meta_p.exists() and chunks_p.exists()
        if not have_all:
            if not auto_build_if_missing:
                missing = [str(p) for p in (index_p, meta_p, chunks_p) if not p.exists()]
                raise FileNotFoundError(f"[RAG] Brak artefaktów: {missing}")
            build_index_from_folders()

        index = faiss.read_index(str(index_p))
        with open(meta_p, "rb") as f:
            meta = pickle.load(f)
        with open(chunks_p, "rb") as f:
            chunks = pickle.load(f)

        embedder = _load_embedder()
        lock = threading.Lock()

        obj = object.__new__(cls)
        obj.index = index
        obj.meta = meta
        obj.chunks = chunks
        obj.embedder = embedder
        obj.encode_lock = lock
        return obj

# --------------------- API: retrieve + generation ---------------------

def retrieve(question: str, k: int = 3) -> List[Dict[str, Any]]:
    rag = _RagSingleton.get()
    with rag.encode_lock:
        q_vec = rag.embedder.encode([question], normalize_embeddings=True).astype("float32")
    D, I = rag.index.search(np.asarray(q_vec), k)

    results: List[Dict[str, Any]] = []
    for rank, (idx, score) in enumerate(zip(I[0].tolist(), D[0].tolist()), start=1):
        m = rag.meta[idx]
        results.append({
            "rank": rank,
            "score": float(score),
            "text": rag.chunks[idx],
            "doc_name": m.get("doc_name"),
            "doc_id": m.get("doc_id"),
            "chunk_idx": m.get("chunk_idx"),
        })
    return results

def build_rag_block(hits: List[Dict[str, Any]], max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK) -> str:
    lines = ["### Materiały referencyjne (RAG) – fragmenty:"]
    for h in hits:
        txt = (h["text"] or "").strip().replace("\r", " ")
        if not txt:
            continue
        snippet = txt[:max_chars_per_chunk] + ("…" if len(txt) > max_chars_per_chunk else "")
        label = f"{h.get('doc_name', 'źródło')} (chunk {h.get('chunk_idx')}, score {h.get('score'):.3f})"
        lines.append(f"- {label}:\n  {snippet}")
    return "\n".join(lines)

def augment_prompt_with_rag(
    final_prompt: str,
    question_for_retrieval: str,
    k: int = 3,
    max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK
) -> Tuple[str, List[Dict[str, Any]]]:
    hits = retrieve(question_for_retrieval, k=k)
    rag_block = build_rag_block(hits, max_chars_per_chunk=max_chars_per_chunk)
    return f"{rag_block}\n\n{final_prompt}", hits

def generate_with_rag(
    final_prompt: str,
    question_for_retrieval: str,
    k: int = 3,
    max_chars_per_chunk: int = MAX_CHARS_PER_CHUNK,
    gen_kwargs: Dict[str, Any] = None
) -> Tuple[str, List[Dict[str, Any]], str]:
    augmented_prompt, hits = augment_prompt_with_rag(final_prompt, question_for_retrieval, k=k, max_chars_per_chunk=max_chars_per_chunk)
    gen_kwargs = gen_kwargs or {}
    text = generate_text(augmented_prompt, **gen_kwargs)
    return text, hits, augmented_prompt

# --------------------- narzędzie: odbuduj indeks ---------------------

def rebuild_index() -> None:
    build_index_from_folders()
    # zresetuj singleton (żeby przy następnym wywołaniu wczytał nowe artefakty)
    _RagSingleton._instance = None
