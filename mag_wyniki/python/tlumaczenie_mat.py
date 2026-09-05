import os
import pandas as pd
from transformers import MarianMTModel, MarianTokenizer
import torch, time, traceback, re

# ─── Settings ────────────────────────────────────────────────────────────────
FOLDER       = "./tlumaczenie_ang"
BATCH_SIZE   = 12
MAX_RETRIES  = 5
MODEL_NAME   = "jproboszcz/opus-mt-en-pl"

# ─── Load model ──────────────────────────────────────────────────────────────
print("Ładowanie modelu…")
tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
model     = MarianMTModel.from_pretrained(MODEL_NAME)

if not torch.cuda.is_available():
    raise SystemExit("GPU is not available. Exiting.")
device = torch.device("cuda")
model.to(device)
print(f"Model załadowany na: {device}")

# ─── Helper: batch translation that skips pure numbers/empties ───────────────
def translate_batch(texts, attempt=1):
    try:
        translated_indices, filtered_texts = [], []
        result = texts[:]                           # pre-fill with originals

        # filter numeric / empty strings
        for i, t in enumerate(texts):
            t_stripped = t.strip()
            if re.fullmatch(r"[-+]?\d+([.,]\d+)?", t_stripped) or t_stripped == "":
                continue
            translated_indices.append(i)
            filtered_texts.append(t)

        if not filtered_texts:                      # nothing to translate
            return result

        tokens = tokenizer(filtered_texts, return_tensors="pt",
                           padding=True, truncation=True).to(device)
        with torch.no_grad():
            translated = model.generate(**tokens)

        decoded = [tokenizer.decode(t, skip_special_tokens=True)
                   for t in translated]
        for i, idx in enumerate(translated_indices):
            result[idx] = decoded[i]
        return result

    except Exception as e:
        print(f"Błąd podczas tłumaczenia (próba {attempt}): {e}")
        traceback.print_exc()
        if attempt < MAX_RETRIES:
            print("Spróbuję ponownie — upewniam się, że model jest na GPU…")
            try:
                if next(model.parameters()).device != device:
                    print("Model nie jest na GPU — przenoszę go.")
                    model.to(device)
            except Exception as e:
                print(f"Błąd sprawdzania/przenoszenia modelu: {e}")
                
            time.sleep(1)
            torch.cuda.empty_cache()
            return translate_batch(texts, attempt + 1)
        print("Maksymalna liczba prób osiągnięta – pomijam.")
        return None

# ─── Main loop over CSV files ────────────────────────────────────────────────
for filename in os.listdir(FOLDER):
    if not filename.endswith(".csv"):
        continue

    filepath = os.path.join(FOLDER, filename)
    print(f"\nPrzetwarzam: {filename}")

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Błąd wczytywania pliku: {e}")
        continue

    # ensure all cells are strings for safe translation
    df = df.fillna("").astype(str)

    # build header map *for every column*, not only object dtypes
    all_columns = list(df.columns)
    translated_header_names = translate_batch(all_columns)
    print(f'translated_header_names: {translated_header_names}')
    if translated_header_names is None or len(translated_header_names) != len(all_columns):
        translated_header_names = [f"{c}_pl" for c in all_columns]
    col_map = {}
    for original, translated in zip(all_columns, translated_header_names):
        # If translation is identical, or already used → append "_pl"
        if translated == original or translated in col_map.values():
            translated += "_pl"
        col_map[original] = translated

    output_path = os.path.join(
        FOLDER, filename.replace(".csv", "_translated.csv"))

    with open(output_path, "w", encoding="utf-8", newline="") as fout:
        header_written = False

        for start in range(0, len(df), BATCH_SIZE):
            end   = min(start + BATCH_SIZE, len(df))
            batch = df.iloc[start:end].copy()

            for col in all_columns:
                new_col = col_map[col]
                if col == "First Name" or col == "Last Name":
                    batch[new_col] = batch[col]  # just copy without translation
                    continue
                
                if df[col].dtype == object:                     # translate cells
                    trans = translate_batch(batch[col].tolist())
                    if trans is None:
                        print(f"Pomijam batch {start}-{end} (kolumna '{col}')")
                        break
                    batch[new_col] = trans
                else:                                           # numeric → copy
                    batch[new_col] = batch[col]

            else:  # runs only if the loop **did not** break
                if not header_written:
                    batch.to_csv(fout, index=False)
                    header_written = True
                else:
                    batch.to_csv(fout, index=False, header=False)

    print(f"Gotowe: {os.path.basename(output_path)}")
