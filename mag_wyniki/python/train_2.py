import pandas as pd
import numpy as np
import torch
import json
import os
import logging
import matplotlib.pyplot as plt
import seaborn as sns

from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CSV_PATH = "final_bert_dataset.csv"
TEXT_COL = "Dane pacjenta"
LABEL_COL = "Jednostka medyczna"
MODEL_PATH = "./herbert-base-cased"
OUTPUT_DIR = "./herbert_model"
NUM_EPOCHS = 4
BATCH_SIZE = 18
EVAL_STEPS = 1000
SAVE_STEPS = 1000

logger.info("Wczytywanie danych...")
df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=[TEXT_COL, LABEL_COL])
logger.info(f"Liczba przypadków po czyszczeniu: {len(df)}")

label_encoder = LabelEncoder()
df["label"] = label_encoder.fit_transform(df[LABEL_COL])
num_labels = len(label_encoder.classes_)

train_df = df.sample(frac=0.8, random_state=42)
temp_df = df.drop(train_df.index)
val_df = temp_df.sample(frac=0.5, random_state=42)
test_df = temp_df.drop(val_df.index)

dataset = DatasetDict({
    "train": Dataset.from_pandas(train_df),
    "validation": Dataset.from_pandas(val_df),
    "test": Dataset.from_pandas(test_df),
})

logger.info("Tokenizacja...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

def tokenize_function(examples):
    return tokenizer(examples[TEXT_COL], padding="max_length", truncation=True, max_length=512)

dataset = dataset.map(tokenize_function, batched=True)
dataset = dataset.remove_columns([TEXT_COL, LABEL_COL, "__index_level_0__"])
dataset = dataset.rename_column("label", "labels")
dataset.set_format("torch")

logger.info("Wczytywanie modelu...")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, num_labels=num_labels)

def compute_metrics(pred):
    logits, labels = pred
    preds = np.argmax(logits, axis=1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro"),
        "f1_weighted": f1_score(labels, preds, average="weighted")
    }

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    do_train=True,
    do_eval=True,
    eval_steps=EVAL_STEPS,
    save_steps=SAVE_STEPS,
    save_total_limit=3,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=NUM_EPOCHS,
    logging_dir=f"{OUTPUT_DIR}/logs",
    logging_steps=100
)

logger.info("Trening modelu...")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

trainer.train()

logger.info("Ewaluacja...")
val_results = trainer.evaluate(eval_dataset=dataset["validation"])
test_results = trainer.evaluate(eval_dataset=dataset["test"])

metrics_df = pd.DataFrame([val_results, test_results], index=["validation", "test"])
metrics_df.to_csv(f"{OUTPUT_DIR}/metrics.csv")

logger.info("Zapis modelu...")
trainer.save_model(f"{OUTPUT_DIR}/final_model")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/final_model")
with open(f"{OUTPUT_DIR}/final_model/label_encoder.json", "w") as f:
    json.dump({"classes": label_encoder.classes_.tolist()}, f)

logger.info("Confusion matrix...")
preds_output = trainer.predict(dataset["test"])
preds = np.argmax(preds_output.predictions, axis=1)
true_labels = preds_output.label_ids

conf_mat = confusion_matrix(true_labels, preds)
report = classification_report(true_labels, preds, target_names=label_encoder.classes_)

plt.figure(figsize=(12, 10))
sns.heatmap(conf_mat, annot=True, fmt='d', xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_, cmap="Blues")
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

logger.info("Zapis logów i wykresów...")
log_history = trainer.state.log_history
log_df = pd.DataFrame(log_history)
log_df.to_csv(f"{OUTPUT_DIR}/training_log.csv", index=False)

def plot_metric(metric_name, ylabel, title):
    plt.figure(figsize=(10, 6))
    if f"eval_{metric_name}" in log_df.columns:
        plt.plot(log_df["step"], log_df[f"eval_{metric_name}"], label=f"eval_{metric_name}", marker="o")
    if metric_name in log_df.columns:
        plt.plot(log_df["step"], log_df[metric_name], label=metric_name, linestyle="--")
    plt.xlabel("Krok")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/{metric_name}_plot.png")
    plt.close()

plot_metric("loss", "Strata", "Strata podczas treningu")
plot_metric("accuracy", "Accuracy", "Dokładność podczas treningu")
plot_metric("f1_macro", "F1 Macro", "F1 Macro podczas treningu")

logger.info("Trening zakończony. Wszystko zapisane w katalogu: %s", OUTPUT_DIR)
