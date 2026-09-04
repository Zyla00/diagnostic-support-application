# predictionModels/services/xg_boost/xgboost_engine.py
from __future__ import annotations
import os, json, pickle
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from xgboost import XGBClassifier

# rysowanie w trybie headless
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# Domyślne kolumny — możesz podać własne w argumencie funkcji
DEFAULT_NUMERIC_COLS = [
    "wiek_w_latach", "Wysokość", "Masa", "Temperatura",
    "badanie_CRP_CRP", "badanie_Chem_ALP (U/l)", "badanie_Chem_AST (U/l)", "badanie_Chem_AlAT (U/l)",
    "badanie_Chem_Albumina (g/dl)", "badanie_Chem_BUN (mg/dl)", "badanie_Chem_Całkowita_białko (g/dl)",
    "badanie_Chem_Chlorek (mEq/l)", "badanie_Chem_GGT (U/l)", "badanie_Chem_Glukoza (mg/dl)",
    "badanie_Chem_Kreatyna (mg/dl)", "badanie_Chem_Ogółem_bilirubina (mg/dl)", "badanie_Chem_Potas (mEq/l)",
    "badanie_Chem_Sód (mEq/l)", "badanie_Chem_Uric_ acid (mg/dl)", "badanie_Chem_eGFR (ml/min/1,73m^2)",
    "badanie_Lipidy_ApoB (mg/dl)", "badanie_Lipidy_HDL (mg/dl)", "badanie_Lipidy_LDL (mg/dl)",
    "badanie_Lipidy_TotalCholesterol (mg/dl)", "badanie_Lipidy_Triglicerydy (mg/dl)",
    "badanie_morfologia_Basophils_abs (10^3/μl)", "badanie_morfologia_Eozynofile_ abs (10^3/μl)",
    "badanie_morfologia_Hematokryt (%)", "badanie_morfologia_Hemoglobina (g/dl)",
    "badanie_morfologia_Limfocyty_ abs (10^3/μl)", "badanie_morfologia_MCH (pg)",
    "badanie_morfologia_MCHC (g/dl)", "badanie_morfologia_MCV (fL)",
    "badanie_morfologia_Monocyty_ abs (10^3/μl)", "badanie_morfologia_Neutrofile_ abs (10^3/μl)",
    "badanie_morfologia_Płytki krwi (10^3/μl)", "badanie_morfologia_RBC (10^6/μl)",
    "badanie_morfologia_RDW (%)", "badanie_morfologia_WBC (10^3/μl)"
]
DEFAULT_CATEGORICAL_COLS = ["Płeć", "Grupa krwi"]


def retrain_xgb(
    output_dir: str,
    csv_path: str,
    herbert_model_dir: str,
    xgb_params: dict | None = None,
    numeric_cols: list[str] | None = None,
    categorical_cols: list[str] | None = None,
    random_state: int = 42,
) -> dict:
    """
    Trenuje XGBoost z embeddingami HerBERT, zapisuje artefakty do output_dir.
    Zwraca słownik z metrykami.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    xgb_params = xgb_params or dict(
        n_estimators=300,
        objective="multi:softprob",
        eval_metric="mlogloss",
        n_jobs=-1,
    )
    numeric_cols = numeric_cols or DEFAULT_NUMERIC_COLS
    categorical_cols = categorical_cols or DEFAULT_CATEGORICAL_COLS

    # --- wczytanie danych
    df = pd.read_csv(csv_path)

    # --- czyszczenie i kolumna tekstowa
    for col in ["Opis_przypadku", "Alergie", "Choroby_przewlekłe"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
        else:
            df[col] = ""
    df = df.dropna(subset=["Jednostka_medyczna"])
    df["tekst"] = df["Opis_przypadku"] + " " + df["Alergie"] + " " + df["Choroby_przewlekłe"]

    # --- etykiety
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df["Jednostka_medyczna"])
    with open(out / "label_encoder.json", "w", encoding="utf-8") as f:
        json.dump({"classes": label_encoder.classes_.tolist()}, f, ensure_ascii=False, indent=2)

    # --- HerBERT (CLS)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(herbert_model_dir)
    model = AutoModel.from_pretrained(herbert_model_dir).to(device)
    model.eval()

    def embed_batch(texts: list[str]) -> np.ndarray:
        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state[:, 0, :].cpu().numpy()  # CLS

    batch_size = 16
    texts = df["tekst"].tolist()
    batches = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Embeddings"):
        batches.append(embed_batch(texts[i:i + batch_size]))
    X_text = np.vstack(batches)

    # --- numeryczne
    X_num = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    scaler = StandardScaler()
    X_num_scaled = scaler.fit_transform(X_num)
    with open(out / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    # --- kategoryczne
    X_cat = pd.get_dummies(df[categorical_cols].fillna("Brak"))
    cat_cols = X_cat.columns.tolist()
    with open(out / "categorical_columns.json", "w", encoding="utf-8") as f:
        json.dump(cat_cols, f, ensure_ascii=False, indent=2)

    # --- połącz
    X = np.hstack([X_text, X_num_scaled, X_cat.values])

    # --- split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=random_state
    )

    # --- model
    clf = XGBClassifier(num_class=len(label_encoder.classes_), **xgb_params)
    clf.fit(X_train, y_train, eval_set=[(X_train, y_train), (X_test, y_test)], verbose=True)
    clf.save_model(str(out / "model.json"))

    # --- raporty/metryki
    y_pred = clf.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=label_encoder.classes_, digits=4)
    (out / "reports").mkdir(exist_ok=True)
    with open(out / "reports" / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=False, fmt="d")
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(out / "reports" / "confusion_matrix.png")
    plt.close()

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro")),
        "f1_weighted": float(f1_score(y_test, y_pred, average="weighted")),
    }
    pd.DataFrame([metrics]).to_csv(out / "reports" / "metrics.csv", index=False)

    # --- zapis konfiguracji treningu
    with open(out / "training_config.json", "w", encoding="utf-8") as f:
        json.dump({
            "csv_path": str(csv_path),
            "herbert_model_dir": str(herbert_model_dir),
            "numeric_cols": numeric_cols,
            "categorical_cols": categorical_cols,
            "xgb_params": xgb_params,
        }, f, ensure_ascii=False, indent=2)

    return {"metrics": metrics, "n_classes": int(len(label_encoder.classes_)), "output_dir": str(out)}
