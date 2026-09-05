import pandas as pd
import numpy as np
import torch
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

CSV_PATH = "final_dataset_structured.csv"
TEXT_COL = "Opis_przypadku"
LABEL_COL = "Jednostka_medyczna"
MODEL_PATH = "./herbert-base-cased"
OUTPUT_DIR = "xgb_herbert_model_3"

NUMERIC_COLS = [
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
    "badanie_morfologia_MCHC (g/dl)", "badanie_morfologia_MCV (fL)", "badanie_morfologia_Monocyty_ abs (10^3/μl)",
    "badanie_morfologia_Neutrofile_ abs (10^3/μl)", "badanie_morfologia_Płytki krwi (10^3/μl)",
    "badanie_morfologia_RBC (10^6/μl)", "badanie_morfologia_RDW (%)", "badanie_morfologia_WBC (10^3/μl)"
]
CATEGORICAL_COLS = ["Płeć", "Grupa krwi"]

os.makedirs(OUTPUT_DIR, exist_ok=True)
df = pd.read_csv(CSV_PATH)

df = df.dropna(subset=[LABEL_COL])
print(f"Rekordy po czyszczeniu labeli: {len(df)}")


label_encoder = LabelEncoder()
df["label"] = label_encoder.fit_transform(df[LABEL_COL])
with open(f"{OUTPUT_DIR}/label_encoder.json", "w") as f:
    json.dump({"classes": label_encoder.classes_.tolist()}, f)
print(f"Zapisano label encoder (klas: {len(label_encoder.classes_)}).")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModel.from_pretrained(MODEL_PATH).to(device)
model.eval()

def get_herbert_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
    return cls_embedding

print("Generowanie embeddingów HerBERT...")
embeddings = [get_herbert_embedding(str(text)) for text in tqdm(df[TEXT_COL].fillna(""))]
X_text = np.vstack(embeddings)

X_num = df[NUMERIC_COLS].apply(pd.to_numeric, errors="coerce")
scaler = StandardScaler()
X_num_scaled = scaler.fit_transform(X_num)

X_cat = pd.get_dummies(df[CATEGORICAL_COLS].fillna("Brak"))

X = np.hstack([X_text, X_num_scaled, X_cat.values])
y = df["label"].values
print(f"X shape: {X.shape}, y shape: {y.shape}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

print("Trening modelu XGBoost...")
clf = XGBClassifier(
    objective="multi:softprob",
    num_class=26,
    eval_metric="mlogloss",
    n_estimators=600,             # więcej drzew dla lepszej nauki
    learning_rate=0.03,           # wolniejsze uczenie => lepsze dopasowanie
    max_depth=10,                 # głębsze drzewa dla bardziej złożonych relacji
    subsample=0.85,               # więcej danych per drzewo
    colsample_bytree=0.85,        # więcej cech per drzewo
    min_child_weight=1,           # bardziej czuły na mniejsze podziały
    gamma=0,                      # pozwala na więcej podziałów
    reg_alpha=0.5,                # regularizacja L1
    reg_lambda=1.0,               # regularizacja L2
    n_jobs=-1,
    verbosity=1
)
clf.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=True)

clf.save_model(f"{OUTPUT_DIR}/model.json")
print("Model zapisany do:", f"{OUTPUT_DIR}/model.json")

y_pred = clf.predict(X_test)
report = classification_report(y_test, y_pred, target_names=label_encoder.classes_, digits=4)
print(report)
with open(f"{OUTPUT_DIR}/classification_report.txt", "w") as f:
    f.write(report)

cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(12, 10))
sns.heatmap(cm, annot=False, cmap="Blues", fmt="d")
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/confusion_matrix.png")
plt.close()

metrics = {
    "accuracy": accuracy_score(y_test, y_pred),
    "f1_macro": f1_score(y_test, y_pred, average="macro"),
    "f1_weighted": f1_score(y_test, y_pred, average="weighted")
}
pd.DataFrame([metrics]).to_csv(f"{OUTPUT_DIR}/metrics.csv", index=False)
print("Metryki, raport i confusion matrix zapisane.")

