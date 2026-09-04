import os, faiss, pickle, json, numpy as np
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader


TXT_DIR      = "definitions_of_specjalists"
PDF_DIR      = "books"
INDEX_PATH   = "defs_index.faiss"
META_PATH    = "defs_meta.pkl"
EMB_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"


def load_pdfs(folder: str):
    docs, names = [], []
    for fname in sorted(os.listdir(folder)):
        if fname.lower().endswith(".pdf"):
            path = os.path.join(folder, fname)
            reader = PdfReader(path)
            # scalamy tekst ze wszystkich stron
            text = "\n".join(
                (page.extract_text() or "")   # extract_text może zwrócić None
                for page in reader.pages
            )
            docs.append(text)
            names.append(fname)
    return docs, names

def load_txts(folder: str):
    docs, names = [], []
    for fname in sorted(os.listdir(folder)):
        if fname.lower().endswith(".txt"):
            path = os.path.join(folder, fname)
            with open(path, encoding="utf-8") as f:
                docs.append(f.read())
                names.append(fname)
    return docs, names

txt_docs, txt_names   = load_txts(TXT_DIR)
pdf_docs, pdf_names   = load_pdfs(PDF_DIR)

docs       = txt_docs + pdf_docs
doc_names  = txt_names + pdf_names
print(f"Łącznie wczytano {len(docs)} dokumentów "
      f"({len(txt_docs)} txt + {len(pdf_docs)} pdf).")


def chunk(text, size=500, overlap=50):
    words = text.split()
    for i in range(0, len(words), size - overlap):
        yield " ".join(words[i:i+size])

chunks, meta = [], []   
for doc_id, (text, name) in enumerate(zip(docs, doc_names)):
    for start, ch in enumerate(chunk(text)):
        chunks.append(ch)
        meta.append({"doc_id": doc_id, "doc_name": name, "chunk_idx": start})

print(f"Powstało {len(chunks)} chunków.")


embedder = SentenceTransformer(EMB_MODEL_ID)
emb = embedder.encode(chunks, batch_size=64, convert_to_numpy=True, show_progress_bar=True, normalize_embeddings=True)

index = faiss.IndexFlatIP(emb.shape[1])     
index.add(emb)
print("Indeks FAISS gotowy.")


faiss.write_index(index, INDEX_PATH)
with open(META_PATH, "wb") as f:
    pickle.dump(meta, f)
print(f"Zapisano {INDEX_PATH} i {META_PATH}")


def rag_query(question, k=5):
    q_vec = embedder.encode([question], normalize_embeddings=True)
    D, I = index.search(np.asarray(q_vec, dtype="float32"), k)
    retrieved = [chunks[i] for i in I[0]]
    sources   = [meta[i]["doc_name"] for i in I[0]]
    return retrieved, sources
