import os
import pandas as pd
from transformers import MarianMTModel, MarianTokenizer
import torch

FOLDER = "./tlumaczenie"  
BATCH_SIZE = 10

MODEL_NAME = "jproboszcz/opus-mt-en-pl"
print("Ładowanie modelu...")
tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
model = MarianMTModel.from_pretrained(MODEL_NAME)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"Model załadowany na: {device}")


def translate_batch(texts):
    tokens = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
    tokens = {k: v.to(device) for k, v in tokens.items()}
    translated = model.generate(**tokens)
    return [tokenizer.decode(t, skip_special_tokens=True) for t in translated]

for filename in os.listdir(FOLDER):
    if filename.endswith(".csv"):
        filepath = os.path.join(FOLDER, filename)
        print(f"\nPrzetwarzam: {filename}")

        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            print(f"Błąd wczytywania pliku: {e}")
            continue

        output_filename = filename.replace(".csv", "_translated.csv")
        output_path = os.path.join(FOLDER, output_filename)

        with open(output_path, mode='w', encoding='utf-8', newline='') as f_out:
            header_written = False

            for start in range(0, len(df), BATCH_SIZE):
                end = min(start + BATCH_SIZE, len(df))
                batch = df.iloc[start:end].copy()

                for col in batch.columns:
                    if batch[col].dtype == object:
                        texts = batch[col].astype(str).fillna("").tolist()
                        try:
                            translations = translate_batch(texts)
                        except Exception as e:
                            print(f"Błąd tłumaczenia kolumny '{col}' wiersze {start}-{end}: {e}")
                            translations = texts

                        batch[f"{col}_pl"] = translations

                if not header_written:
                    batch.to_csv(f_out, index=False)
                    header_written = True
                else:
                    batch.to_csv(f_out, index=False, header=False)

                print(f"Wiersze {start}-{end} zapisane")

        print(f"Gotowe: {output_filename}")
