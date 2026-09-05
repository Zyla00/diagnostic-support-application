# predictionModels/service/herbert_engine.py
from __future__ import annotations
import os, json
from pathlib import Path
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
import torch

# headless matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    confusion_matrix,
    classification_report,
)
from torch.nn import CrossEntropyLoss


# ------------------------ helpers ------------------------

def _read_old_labels(model_dir: Path) -> List[str]:
    """Wczytaj poprzednie etykiety jeśli istnieją."""
    enc = model_dir / "label_encoder.json"
    if enc.exists():
        try:
            with open(enc, encoding="utf-8") as f:
                obj = json.load(f)
            classes = list(obj.get("classes", []))
            return [str(c) for c in classes]
        except Exception:
            return []
    return []

def _make_union_labels(old_labels: List[str], new_labels: List[str]) -> List[str]:
    """Stare etykiety w tej samej kolejności + nowe, które jeszcze nie występowały."""
    out = list(old_labels)
    for lab in new_labels:
        if lab not in out:
            out.append(lab)
    return out

def _get_head(model):
    """Zwróć warstwę klasyfikacyjną niezależnie od architektury (classifier/score)."""
    return getattr(model, "classifier", None) or getattr(model, "score", None)

def _copy_head_weights(old_model, new_model, old_idx: Dict[str, int], new_idx: Dict[str, int], labels_in_both: List[str]):
    """Skopiuj wagi/biasy głowicy dla etykiet wspólnych."""
    old_head = _get_head(old_model)
    new_head = _get_head(new_model)
    if old_head is None or new_head is None:
        # brak standardowej głowicy — nic nie kopiujemy
        return

    with torch.no_grad():
        for lab in labels_in_both:
            oi = old_idx[lab]
            ni = new_idx[lab]
            # zabezpieczenie na wypadek innych kształtów:
            if oi < old_head.weight.shape[0] and ni < new_head.weight.shape[0]:
                new_head.weight[ni].copy_(old_head.weight[oi])
                new_head.bias[ni].copy_(old_head.bias[oi])


# ------------------------ główna funkcja ------------------------

def finetune_herbert(
    output_dir: str,
    csv_path: str,
    base_model_dir: str,            # ← wskaż folder poprzedniego finału (HERBERT_FINAL)
    text_cols: list[str] | None = None,
    label_col: str = "Jednostka_medyczna",
    num_train_epochs: int = 3,
    per_device_train_batch_size: int = 8,
    per_device_eval_batch_size: int = 8,
    eval_steps: int = 2000,
    save_steps: int = 2000,
    seed: int = 42,
) -> dict:
    """
    Kontynuacja finetuningu HerBERT:
    - zachowuje stare klasy i ich wagi,
    - dodaje nowe klasy (nowe wiersze w głowicy) z losową inicjalizacją.
    """
    text_cols = text_cols or ["Opis_przypadku", "Alergie", "Choroby_przewlekłe"]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    base_dir = Path(base_model_dir)  # to powinien być poprzedni final_model
    if not base_dir.exists():
        raise ValueError(f"Nie znaleziono katalogu modelu bazowego: {base_dir}")

    # ---------- dane ----------
    df = pd.read_csv(csv_path)
    for c in text_cols:
        if c not in df.columns:
            df[c] = ""
    df[text_cols] = df[text_cols].fillna("")
    df = df.dropna(subset=[label_col])
    df["input_text"] = df[text_cols].agg(" | ".join, axis=1)

    new_labels_from_data = [str(x) for x in sorted(df[label_col].astype(str).unique())]
    old_labels = _read_old_labels(base_dir)
    all_labels = _make_union_labels(old_labels, new_labels_from_data)

    if len(all_labels) < 2:
        raise ValueError(
            f"Do treningu potrzeba co najmniej 2 klasy. Znaleziono: {all_labels}. "
            f"Dodaj przykłady z drugą etykietą."
        )

    # stabilne mapowania
    new_index = {lab: i for i, lab in enumerate(all_labels)}
    old_index = {lab: i for i, lab in enumerate(old_labels)} if old_labels else {}

    # przemapuj etykiety w bieżących próbkach na indeksy z unii
    df["labels"] = df[label_col].astype(str).map(new_index)

    # ---------- split ----------
    train_df = df.sample(frac=0.8, random_state=seed)
    temp_df = df.drop(train_df.index)
    val_df = temp_df.sample(frac=0.5, random_state=seed)
    test_df = temp_df.drop(val_df.index)

    dataset = DatasetDict(
        {
            "train": Dataset.from_pandas(train_df, preserve_index=False),
            "validation": Dataset.from_pandas(val_df, preserve_index=False),
            "test": Dataset.from_pandas(test_df, preserve_index=False),
        }
    )

    # ---------- tokenizer ----------
    tokenizer = AutoTokenizer.from_pretrained(str(base_dir), local_files_only=True)

    def tokenize_function(examples):
        return tokenizer(
            examples["input_text"],
            padding="max_length",
            truncation=True,
            max_length=512,
        )

    dataset = dataset.map(tokenize_function, batched=True)
    keep_cols = ["input_ids", "attention_mask", "labels"]
    for split in ["train", "validation", "test"]:
        cols = [c for c in dataset[split].column_names if c not in keep_cols]
        dataset[split] = dataset[split].remove_columns(cols)
    dataset.set_format("torch")

    # ---------- model ----------
    num_labels = len(all_labels)

    # 1) załaduj stary model (żeby mieć stare wagi głowicy)
    old_model = AutoModelForSequenceClassification.from_pretrained(
        str(base_dir), local_files_only=True
    )

    # 2) stwórz nowy model z poszerzoną głowicą (num_labels = unia)
    model = AutoModelForSequenceClassification.from_pretrained(
        str(base_dir),
        num_labels=num_labels,
        local_files_only=True,
        ignore_mismatched_sizes=True,  # pozwala utworzyć większą głowicę
    )

    # przepisz wagi dla wspólnych etykiet (stare klasy)
    labels_in_both = [lab for lab in old_labels if lab in new_index]
    _copy_head_weights(old_model, model, old_index, new_index, labels_in_both)

    # uzupełnij label2id/id2label w configu
    model.config.label2id = {lab: i for i, lab in enumerate(all_labels)}
    model.config.id2label = {i: lab for i, lab in enumerate(all_labels)}

    # ---------- ważenie klas (na bazie aktualnego zbioru) ----------
    class_counts = torch.tensor(train_df["labels"].value_counts().sort_index().reindex(range(num_labels), fill_value=0).values, dtype=torch.float)
    # uniknij dzielenia przez zero (klasy bez próbek nie będą ważyć)
    class_weights = torch.where(class_counts > 0, 1.0 / class_counts, torch.zeros_like(class_counts))
    if class_weights.sum() > 0:
        class_weights = class_weights / class_weights.sum()

    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.get("labels")
            outputs = model(**inputs)
            logits = outputs.get("logits")
            # przenieś wagi na device modelu
            cw = class_weights.to(model.device)
            loss_fct = CrossEntropyLoss(weight=cw if cw.sum() > 0 else None)
            loss = loss_fct(logits, labels)
            return (loss, outputs) if return_outputs else loss

    # ---------- trening ----------
    use_fp16 = torch.cuda.is_available()
    args = TrainingArguments(
        output_dir=str(out),
        do_train=True,
        do_eval=True,
        eval_steps=eval_steps,
        save_steps=save_steps,
        save_total_limit=3,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_eval_batch_size,
        num_train_epochs=num_train_epochs,
        logging_dir=str(out / "logs"),
        logging_steps=200,
        report_to="none",
        fp16=use_fp16,
        seed=seed,
        # delikatny dalszy finetuning — warto dodać mały LR:
        learning_rate=2e-5,
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=1)
        return {
            "accuracy": accuracy_score(labels, preds),
            "f1_macro": f1_score(labels, preds, average="macro", zero_division=0),
            "f1_weighted": f1_score(labels, preds, average="weighted", zero_division=0),
        }

    trainer = WeightedTrainer(
        model=model,
        args=args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    # Gdy w batchu faktycznie występuje tylko jedna etykieta, HF potrafi wywalić metryki.
    # Złapmy i zgłośmy czytelny błąd:
    if train_df["labels"].nunique() < 2:
        raise ValueError(
            "Bieżąca paczka treningowa zawiera tylko jedną etykietę. "
            "Dodaj choć kilka przykładów drugiej klasy (lub dołącz próbki z poprzedniego zbioru)."
        )

    trainer.train()

    # ---------- ewaluacja ----------
    val_results = trainer.evaluate(eval_dataset=dataset["validation"])
    test_results = trainer.evaluate(eval_dataset=dataset["test"])
    pd.DataFrame([val_results, test_results], index=["validation", "test"]).to_csv(out / "metrics.csv")

    # ---------- zapis modelu + encoder ----------
    trainer.save_model(str(out))
    tokenizer.save_pretrained(str(out))
    with open(out / "label_encoder.json", "w", encoding="utf-8") as f:
        json.dump({"classes": all_labels}, f, ensure_ascii=False, indent=2)

    # ---------- wizualizacje ----------
    preds_output = trainer.predict(dataset["test"])
    if preds_output and hasattr(preds_output, "predictions"):
        preds = np.argmax(preds_output.predictions, axis=1)
        true_labels = preds_output.label_ids
        if true_labels is not None and len(true_labels) and len(np.unique(true_labels)) > 1:
            conf_mat = confusion_matrix(true_labels, preds, labels=list(range(num_labels)))
            plt.figure(figsize=(12, 10))
            plt.imshow(conf_mat, aspect="auto")
            plt.title("Confusion Matrix"); plt.xlabel("Predicted"); plt.ylabel("True")
            plt.colorbar(); plt.tight_layout()
            plt.savefig(out / "confusion_matrix.png"); plt.close()

            try:
                report = classification_report(true_labels, preds, target_names=all_labels, zero_division=0)
                with open(out / "classification_report.txt", "w", encoding="utf-8") as f:
                    f.write(report)
            except Exception:
                pass

    # log historii
    try:
        log_df = pd.DataFrame(trainer.state.log_history)
        log_df.to_csv(out / "training_log.csv", index=False)
    except Exception:
        pass

    return {
        "metrics": {
            "val_accuracy": float(val_results.get("eval_accuracy", 0.0)),
            "val_f1_macro": float(val_results.get("eval_f1_macro", 0.0)),
            "test_accuracy": float(test_results.get("eval_accuracy", 0.0)),
            "test_f1_macro": float(test_results.get("eval_f1_macro", 0.0)),
        },
        "n_classes": int(num_labels),
        "labels": all_labels,
        "output_dir": str(out),
    }
