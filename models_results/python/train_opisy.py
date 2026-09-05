import os
import re
import glob
import json
import logging
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
import seaborn as sns

from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from torch.nn import CrossEntropyLoss

# =========================
# Konfiguracja
# =========================
MAIN_CSV    = "final_dataset_structured.csv"
EXTRA_CSV_1 = "symptom-disease-train-labels.csv"
EXTRA_CSV_2 = "symptom-disease-test-labels.csv"
FINAL_CSV   = "final_dataset_structured_all.csv"

# docelowe (ujednolicone) nazwy kolumn
TEXT_COLS = ["Opis_przypadku", "Alergie", "Choroby_przewlekłe"]
LABEL_COL = "Jednostka_medyczna"

MODEL_PATH = "./herbert-base-cased"
OUTPUT_DIR = "./herbert_finetuned_textonly_6"

NUM_EPOCHS    = 4          # zachowane
BATCH_SIZE    = 36         # zachowane
EVAL_STEPS    = 200       # (dla kompatybilności – w tej wersji i tak nie włącza evalu)
SAVE_STEPS    = 200       # checkpointy co N kroków -> na nich zrobimy ewaluację
LOGGING_STEPS = 200

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# Logowanie + filtr (wycisza tylko 2 komunikaty o "head")
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tf_logger = logging.getLogger("transformers.modeling_utils")
class _HideHeadInit(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "were not initialized from the model checkpoint" in msg:
            return False
        if "You should probably TRAIN this model on a down-stream task" in msg:
            return False
        return True
tf_logger.addFilter(_HideHeadInit())

# =========================
# Unifikacja kolumn w plikach extra
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
        df = df.rename(columns={"Opis_przepadku": "Opis_przypadku"})
    if "Jednostka_medyczna" not in df.columns and "Jednosta_medyczna_pl" in df.columns:
        df = df.rename(columns={"Jednosta_medyczna_pl": "Jednostka_medyczna"})
    for col in ["Alergie", "Choroby_przewlekłe"]:
        if col not in df.columns:
            df[col] = ""
    return df

# =========================
# Dane
# =========================
logger.info("Wczytywanie i łączenie danych...")

main_df   = ensure_core_columns(pd.read_csv(MAIN_CSV))
extra1_df = normalize_extra_cols(pd.read_csv(EXTRA_CSV_1))
extra2_df = normalize_extra_cols(pd.read_csv(EXTRA_CSV_2))

df = pd.concat([main_df, extra1_df, extra2_df], ignore_index=True)
df.to_csv(FINAL_CSV, index=False)
logger.info(f"Zapisano połączony zbiór jako: {FINAL_CSV}")

df[TEXT_COLS] = df[TEXT_COLS].fillna("")
df["input_text"] = df[TEXT_COLS].agg(" | ".join, axis=1)

df = df.dropna(subset=[LABEL_COL])
logger.info(f"Liczba przypadków po czyszczeniu (na podstawie label): {len(df)}")

label_encoder = LabelEncoder()
df["label"] = label_encoder.fit_transform(df[LABEL_COL])
num_labels = len(label_encoder.classes_)

train_df = df.sample(frac=0.8, random_state=42)
temp_df  = df.drop(train_df.index)
val_df   = temp_df.sample(frac=0.5, random_state=42)
test_df  = temp_df.drop(val_df.index)

dataset = DatasetDict({
    "train": Dataset.from_pandas(train_df),
    "validation": Dataset.from_pandas(val_df),
    "test": Dataset.from_pandas(test_df),
})

# =========================
# Tokenizacja
# =========================
logger.info("Tokenizacja...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

def tokenize_function(examples):
    return tokenizer(examples["input_text"], padding="max_length", truncation=True, max_length=512)

dataset = dataset.map(tokenize_function, batched=True)
dataset = dataset.remove_columns(df.columns.difference(["input_text", "label"]).tolist())
dataset = dataset.rename_column("label", "labels")
dataset.set_format("torch")

# =========================
# Model + wagi klas
# =========================
logger.info("Wczytywanie modelu...")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, num_labels=num_labels)

class_counts = train_df["label"].value_counts().sort_index()
class_weights = 1.0 / class_counts
class_weights = class_weights / class_weights.sum()
class_weights_tensor = torch.tensor(class_weights.values, dtype=torch.float)
logger.info("Wagi klas: %s", class_weights_tensor.tolist())

class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        loss_fct = CrossEntropyLoss(weight=class_weights_tensor.to(model.device))
        loss = loss_fct(logits, labels)
        return (loss, outputs) if return_outputs else loss

# =========================
# TrainingArguments — bez eval during training (kompatybilne)
# =========================
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    do_train=True,
    do_eval=True,
    # brak evaluation_strategy / evaluate_during_training – nieobsługiwane w Twojej wersji
    eval_steps=EVAL_STEPS,           # zostaje dla kompatybilności; nie szkodzi
    logging_steps=LOGGING_STEPS,
    save_steps=SAVE_STEPS,           # będziemy ewaluować checkpointy po treningu
    save_total_limit=100,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=NUM_EPOCHS,
    logging_dir=f"{OUTPUT_DIR}/logs",
    report_to="none",
    fp16=True
)

# =========================
# Metryki (kompatybilne)
# =========================
def compute_metrics(p):
    preds = p.predictions if hasattr(p, "predictions") else p[0]
    labels = p.label_ids   if hasattr(p, "label_ids")   else p[1]
    preds = np.argmax(preds, axis=1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro"),
        "f1_weighted": f1_score(labels, preds, average="weighted"),
    }

# =========================
# Trening
# =========================
logger.info("Trening modelu...")
trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)
trainer.train()

# =========================
# Ewaluacja KOŃCOWA (val + test)
# =========================
logger.info("Ewaluacja końcowa...")
val_results  = trainer.evaluate(eval_dataset=dataset["validation"])
test_results = trainer.evaluate(eval_dataset=dataset["test"])
pd.DataFrame([val_results, test_results], index=["validation", "test"]).to_csv(f"{OUTPUT_DIR}/metrics.csv")

# =========================
# Ocena WSZYSTKICH checkpointów => monitoring accuracy (VAL + TEST) w czasie
# =========================
def list_checkpoints(output_dir):
    paths = [p for p in glob.glob(os.path.join(output_dir, "checkpoint-*")) if os.path.isdir(p)]
    def step_of(p):
        m = re.search(r"checkpoint-(\d+)", os.path.basename(p))
        return int(m.group(1)) if m else -1
    return sorted(paths, key=step_of)

ckpts = list_checkpoints(OUTPUT_DIR)
history = []

# CSV file path for live writing
acc_history_path = os.path.join(OUTPUT_DIR, "accuracy_history.csv")

for ckpt in ckpts:
    step = int(os.path.basename(ckpt).split("-")[-1])
    logger.info(f"Evaluating checkpoint at step {step}...")

    ckpt_model = AutoModelForSequenceClassification.from_pretrained(ckpt, num_labels=num_labels)
    ckpt_trainer = Trainer(
        model=ckpt_model,
        args=training_args,
        eval_dataset=dataset["validation"],  # placeholder, we pass dataset explicitly in evaluate()
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    # Evaluate on validation
    val_metrics = ckpt_trainer.evaluate(eval_dataset=dataset["validation"])
    # Evaluate on test
    test_metrics = ckpt_trainer.evaluate(eval_dataset=dataset["test"])

    # Append current checkpoint metrics
    history.append({
        "step": step,
        "val_eval_accuracy":  val_metrics.get("eval_accuracy", np.nan),
        "val_eval_loss":      val_metrics.get("eval_loss", np.nan),
        "test_eval_accuracy": test_metrics.get("eval_accuracy", np.nan),
        "test_eval_loss":     test_metrics.get("eval_loss", np.nan),
    })

    # Write to CSV after each checkpoint for live updates
    pd.DataFrame(history).sort_values("step").reset_index(drop=True).to_csv(acc_history_path, index=False)

# If no checkpoints were saved, add final model's evaluation results
if not history:
    history.append({
        "step": int(trainer.state.global_step) if hasattr(trainer.state, "global_step") else 0,
        "val_eval_accuracy":  val_results.get("eval_accuracy", np.nan),
        "val_eval_loss":      val_results.get("eval_loss", np.nan),
        "test_eval_accuracy": test_results.get("eval_accuracy", np.nan),
        "test_eval_loss":     test_results.get("eval_loss", np.nan),
    })
    pd.DataFrame(history).to_csv(acc_history_path, index=False)

# =========================
# Wykresy: accuracy w czasie (VAL + TEST)
# =========================
acc_df = pd.DataFrame(history).sort_values("step").reset_index(drop=True)

plt.figure(figsize=(10, 6))
plt.plot(acc_df["step"], acc_df["val_eval_accuracy"],  marker="o", label="VAL accuracy")
plt.plot(acc_df["step"], acc_df["test_eval_accuracy"], marker="o", linestyle="--", label="TEST accuracy")
plt.xlabel("Krok (checkpoint)")
plt.ylabel("Accuracy")
plt.title("Dokładność (eval) w trakcie uczenia – VAL vs TEST")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/eval_accuracy_over_time.png")
plt.close()

# =========================
# Zapis modelu + label encoder
# =========================
logger.info("Zapis modelu...")
trainer.save_model(f"{OUTPUT_DIR}/final_model")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/final_model")
with open(f"{OUTPUT_DIR}/final_model/label_encoder.json", "w") as f:
    json.dump({"classes": label_encoder.classes_.tolist()}, f)

# =========================
# Confusion matrix + report
# =========================
logger.info("Confusion matrix...")
preds_output = trainer.predict(dataset["test"])
preds = np.argmax(preds_output.predictions, axis=1)
true_labels = preds_output.label_ids

conf_mat = confusion_matrix(true_labels, preds)
report = classification_report(true_labels, preds, target_names=label_encoder.classes_)

plt.figure(figsize=(12, 10))
sns.heatmap(conf_mat, annot=True, fmt='d',
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_,
            cmap="Blues")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.title("Confusion Matrix")
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/confusion_matrix.png")
plt.close()

with open(f"{OUTPUT_DIR}/classification_report.txt", "w") as f:
    f.write(report)

# =========================
# Pełne logi treningu + wykresy
# =========================
log_df = pd.DataFrame(trainer.state.log_history)
log_df.to_csv(f"{OUTPUT_DIR}/training_log.csv", index=False)

# wykres loss/accuracy
def plot_metric_from_logs(log_df, metric_name, ylabel, title, out_name):
    plt.figure(figsize=(10, 6))
    eval_col = f"eval_{metric_name}"
    if eval_col in log_df.columns and log_df[eval_col].notna().any():
        plt.plot(log_df["step"], log_df[eval_col], marker="o", label=eval_col)
    if metric_name in log_df.columns and log_df[metric_name].notna().any():
        plt.plot(log_df["step"], log_df[metric_name], linestyle="--", label=metric_name)
    plt.xlabel("Krok")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, out_name))
    plt.close()

# loss z logów (train + ewaluacyjne jeśli są)
plot_metric_from_logs(log_df, "loss", "Strata", "Strata podczas treningu", "loss_plot.png")

# czysty wykres ACCURACY z ewaluacji checkpointów
plt.figure(figsize=(10, 6))
plt.plot(acc_df["step"], acc_df["eval_accuracy"], marker="o")
plt.xlabel("Krok (checkpoint)")
plt.ylabel("Accuracy")
plt.title("Dokładność (eval) w trakcie uczenia – z checkpointów")
plt.grid(True)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/eval_accuracy_over_time.png")
plt.close()

logger.info("Trening zakończony. Monitoring accuracy zapisany do accuracy_history.csv i eval_accuracy_over_time.png w: %s", OUTPUT_DIR)
