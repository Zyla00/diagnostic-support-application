# eval_checkpoints_accuracy.py
import os
import re
import glob
import gc
import logging
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt

from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# =========================
# Config – adjust if needed
# =========================
MAIN_CSV    = "final_dataset_structured.csv"          # used to rebuild the same combined file
EXTRA_CSV_1 = "symptom-disease-train-labels.csv"
EXTRA_CSV_2 = "symptom-disease-test-labels.csv"
FINAL_CSV   = "final_dataset_structured_all.csv"      # combined CSV produced earlier

TEXT_COLS = ["Opis_przypadku", "Alergie", "Choroby_przewlekłe"]
LABEL_COL = "Jednostka_medyczna"

MODEL_PATH = "./herbert-base-cased"                   # only for tokenizer
OUTPUT_DIR = "./herbert_finetuned_textonly_6"         # where checkpoints live
MAX_LEN = 512
BATCH_SIZE = 36

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eval_only")

# =========================
# Helpers to normalize cols
# =========================
RENAME_MAP_EXTRAS = {
    "Opis_przepadku": "Opis_przypadku",
    "Jednosta_medyczna_pl": "Jednostka_medyczna",
}
def normalize_extra_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=RENAME_MAP_EXTRAS)
    for col in ["Alergie", "Choroby_przewlekłe"]:
        if col not in df.columns:
            df[col] = ""
    return df

def ensure_core_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "Opis_przypadku" not in df.columns and "Opis_przepadku" in df.columns:
        df = df.rename(columns={"Opis_przypadku": "Opis_przypadku"})
    if "Jednostka_medyczna" not in df.columns and "Jednosta_medyczna_pl" in df.columns:
        df = df.rename(columns={"Jednosta_medyczna_pl": "Jednostka_medyczna"})
    for col in ["Alergie", "Choroby_przewlekłe"]:
        if col not in df.columns:
            df[col] = ""
    return df

# =========================
# Build the same dataset/splits (seed=42)
# =========================
logger.info("Loading & combining data...")
main_df   = ensure_core_columns(pd.read_csv(MAIN_CSV))
extra1_df = normalize_extra_cols(pd.read_csv(EXTRA_CSV_1))
extra2_df = normalize_extra_cols(pd.read_csv(EXTRA_CSV_2))
df = pd.concat([main_df, extra1_df, extra2_df], ignore_index=True)

# text fields & label encoding
df[TEXT_COLS] = df[TEXT_COLS].fillna("")
df["input_text"] = df[TEXT_COLS].agg(" | ".join, axis=1)
df = df.dropna(subset=[LABEL_COL]).reset_index(drop=True)

label_encoder = LabelEncoder()
df["label"] = label_encoder.fit_transform(df[LABEL_COL])

# reproduce splits (same as training script)
train_df = df.sample(frac=0.8, random_state=42)
temp_df  = df.drop(train_df.index)
val_df   = temp_df.sample(frac=0.5, random_state=42)
test_df  = temp_df.drop(val_df.index)

dataset = DatasetDict({
    "validation": Dataset.from_pandas(val_df),
    "test": Dataset.from_pandas(test_df),
})

# =========================
# Tokenization
# =========================
logger.info("Tokenizing...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

def tokenize_function(examples):
    return tokenizer(examples["input_text"], padding="max_length", truncation=True, max_length=MAX_LEN)

dataset = dataset.map(tokenize_function, batched=True)
# keep only features needed by Trainer
keep_cols = ["input_text", "label", "input_ids", "attention_mask"]
dataset = dataset.remove_columns([c for c in dataset["validation"].column_names if c not in keep_cols])
dataset = dataset.rename_column("label", "labels")
dataset.set_format("torch")

# =========================
# Checkpoints listing
# =========================
def list_checkpoints(output_dir):
    paths = [p for p in glob.glob(os.path.join(output_dir, "checkpoint-*")) if os.path.isdir(p)]
    def step_of(p):
        m = re.search(r"checkpoint-(\d+)", os.path.basename(p))
        return int(m.group(1)) if m else -1
    return sorted(paths, key=step_of)

ckpts = list_checkpoints(OUTPUT_DIR)
if not ckpts:
    raise SystemExit(f"No checkpoints found in {OUTPUT_DIR}")

logger.info("Found %d checkpoints.", len(ckpts))

# =========================
# Metrics: accuracy only
# =========================
def compute_accuracy(p):
    preds = p.predictions if hasattr(p, "predictions") else p[0]
    labels = p.label_ids   if hasattr(p, "label_ids")   else p[1]
    preds = np.argmax(preds, axis=1)
    return {"accuracy": accuracy_score(labels, preds)}

# lightweight TrainingArguments for evaluation
use_fp16 = torch.cuda.is_available()
training_args = TrainingArguments(
    output_dir=os.path.join(OUTPUT_DIR, "eval_tmp"),
    per_device_eval_batch_size=BATCH_SIZE,
    fp16=use_fp16,
    report_to="none",
)

# =========================
# Evaluate every checkpoint
# =========================
history = []
acc_history_path = os.path.join(OUTPUT_DIR, "accuracy_history.csv")
plot_path = os.path.join(OUTPUT_DIR, "accuracy_over_time.png")

for ckpt in ckpts:
    step = int(os.path.basename(ckpt).split("-")[-1])
    logger.info("Evaluating checkpoint %s (step %d)...", ckpt, step)

    model = AutoModelForSequenceClassification.from_pretrained(ckpt)
    trainer = Trainer(
        model=model,
        args=training_args,
        tokenizer=tokenizer,
        compute_metrics=compute_accuracy,
    )

    val_metrics  = trainer.evaluate(eval_dataset=dataset["validation"])
    test_metrics = trainer.evaluate(eval_dataset=dataset["test"])

    history.append({
        "step": step,
        "val_accuracy":  val_metrics.get("eval_accuracy", np.nan),
        "val_loss":      val_metrics.get("eval_loss", np.nan),
        "test_accuracy": test_metrics.get("eval_accuracy", np.nan),
        "test_loss":     test_metrics.get("eval_loss", np.nan),
    })

    # write live CSV
    pd.DataFrame(history).sort_values("step").reset_index(drop=True).to_csv(acc_history_path, index=False)

    # --- free VRAM after this checkpoint ---
    del trainer
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    # ---------------------------------------

# =========================
# Plot accuracy over steps
# =========================
acc_df = pd.DataFrame(history).sort_values("step").reset_index(drop=True)

plt.figure(figsize=(10, 6))
plt.plot(acc_df["step"], acc_df["val_accuracy"],  marker="o", label="VAL accuracy")
plt.plot(acc_df["step"], acc_df["test_accuracy"], marker="o", linestyle="--", label="TEST accuracy")
plt.xlabel("Checkpoint step")
plt.ylabel("Accuracy")
plt.title("Checkpoint accuracy over time (VAL vs TEST)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(plot_path)
plt.close()

logger.info("Done. Wrote %s and %s", acc_history_path, plot_path)
