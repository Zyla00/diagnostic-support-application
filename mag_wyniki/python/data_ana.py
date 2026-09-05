import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

CSV_PATH = "final_bert_dataset.csv"
TEXT_COL = "Dane pacjenta"
LABEL_COL = "Jednostka medyczna"

df = pd.read_csv(CSV_PATH)

print("Wczytano dane.")
print(f"Liczba wszystkich rekordów: {len(df)}")
print(f"Kolumny w zbiorze: {list(df.columns)}\n")

print("Braki danych:")
print(df[[TEXT_COL, LABEL_COL]].isnull().sum(), "\n")

print("Przykładowe dane:")
print(df[[TEXT_COL, LABEL_COL]].sample(10, random_state=42), "\n")

df["text_length"] = df[TEXT_COL].astype(str).apply(len)
print("Statystyki długości tekstów:")
print(df["text_length"].describe(), "\n")

print("Unikalne etykiety klas:")
print(df[LABEL_COL].value_counts(), "\n")

print("10 największych klas:")
print(df[LABEL_COL].value_counts().head(10), "\n")

print("🔻 10 najmniejszych klas:")
print(df[LABEL_COL].value_counts().tail(10), "\n")

plt.figure(figsize=(12, 6))
sns.histplot(df[LABEL_COL], stat="count", bins=30)
plt.title("Liczba przykładów na klasę")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

plt.savefig("class_distribution.png")
print("Wykres rozkładu klas zapisany do: class_distribution.png")

short_texts = df[df["text_length"] < 10]
print(f"Znaleziono {len(short_texts)} rekordów z tekstami krótszymi niż 10 znaków.")
if not short_texts.empty:
    print("Przykłady bardzo krótkich tekstów:")
    print(short_texts[[TEXT_COL, LABEL_COL]].head())

