import pandas as pd
from datetime import datetime

CSV_PATH = "tlumaczenie_mat/ready/DimPatient_translated.csv"
KOLUMNA_DATY_URODZENIA = "Data urodzenia"

DATA_ODNIESIENIA = datetime(2025, 5, 1)

df = pd.read_csv(CSV_PATH)

def oblicz_wiek(d):
    try:
        data_urodzenia = pd.to_datetime(d, errors='coerce')
        if pd.isna(data_urodzenia):
            return None
        wiek = DATA_ODNIESIENIA.year - data_urodzenia.year - (
            (DATA_ODNIESIENIA.month, DATA_ODNIESIENIA.day) < (data_urodzenia.month, data_urodzenia.day)
        )
        return wiek
    except:
        return None

df["wiek_w_latach"] = df[KOLUMNA_DATY_URODZENIA].apply(oblicz_wiek)

df.to_csv(CSV_PATH, index=False)
print(f"Dodano kolumnę 'wiek_w_latach' i zapisano do pliku: {CSV_PATH}")
