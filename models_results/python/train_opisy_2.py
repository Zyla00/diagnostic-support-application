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
from torch.nn import CrossEntropyLoss

MAIN_CSV = "final_dataset_structured.csv"
FINAL_CSV = "final_dataset_structured_all.csv"  

TEXT_COLS = ["Opis_przypadku", "Alergie", "Choroby_przewlekłe"]
LABEL_COL = "Jednostka_medyczna"
MODEL_PATH = "./herbert-base-cased"
OUTPUT_DIR = "./herbert_finetuned_textonly_2"
NUM_EPOCHS = 4
BATCH_SIZE = 36
EVAL_STEPS = 2000
SAVE_STEPS = 2000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Wczytywanie danych...")

df = pd.read_csv(MAIN_CSV)

df.to_csv(FINAL_CSV, index=False)
logger.info(f"Zapisano zbiór jako: {FINAL_CSV}")

df[TEXT_COLS] = df[TEXT_COLS].fillna("")
df["input_text"] = df[TEXT_COLS].agg(" | ".join, axis=1)

df = df.dropna(subset=[LABEL_COL])
logger.info(f"Liczba przypadków po czyszczeniu (na podstawie label): {len(df)}")

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
    return tokenizer(examples["input_text"], padding="max_length", truncation=True, max_length=512)

dataset = dataset.map(tokenize_function, batched=True)
dataset = dataset.remove_columns(df.columns.difference(["input_text", "label"]).tolist())
dataset = dataset.rename_column("label", "labels")
dataset.set_format("torch")

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

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    do_train=True,
    do_eval=True,
    eval_steps=2000,
    save_steps=2000,
    save_total_limit=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    logging_dir=f"{OUTPUT_DIR}/logs",
    logging_steps=200,
    report_to="none",
    fp16=True
)

def compute_metrics(pred):
    logits, labels = pred
    preds = np.argmax(logits, axis=1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro"),
        "f1_weighted": f1_score(labels, preds, average="weighted")
    }

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

logger.info("Ewaluacja...")
val_results = trainer.evaluate(eval_dataset=dataset["validation"])
test_results = trainer.evaluate(eval_dataset=dataset["test"])

pd.DataFrame([val_results, test_results], index=["validation", "test"]).to_csv(f"{OUTPUT_DIR}/metrics.csv")

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

log_df = pd.DataFrame(trainer.state.log_history)
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
