#!/usr/bin/env python3
# plik: kolumny_csv.py
import csv
import sys
from pathlib import Path

# === USTAWIENIA DO EDYCJI =========================================
# 1) Ścieżka do pliku CSV:
#    - Domyślnie: plik "dane.csv" obok tego skryptu.
CSV_PATH = Path(__file__).with_name("final_dataset_structured_all.csv")
#    - Alternatywnie wpisz pełną ścieżkę, np.:
# CSV_PATH = Path(r"/pełna/ścieżka/do/pliku.csv")

# 2) Separator kolumn:
#    - Ustaw na None, aby wykrywać automatycznie (",", ";", tab, "|")
#    - Albo wpisz konkretny np. ";" lub "," lub "\t"
DELIMITER = None

# 3) Kodowanie pliku (np. "utf-8-sig" albo "cp1250")
ENCODING = "utf-8-sig"
# ===================================================================

def detect_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        if ";" in sample and "," not in sample:
            return ";"
        if "\t" in sample:
            return "\t"
        return ","

def main():
    try:
        with open(CSV_PATH, "r", encoding=ENCODING, newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            delimiter = DELIMITER if DELIMITER else detect_delimiter(sample)

            reader = csv.reader(f, delimiter=delimiter)
            header = next(reader, None)
            if not header:
                print("Plik jest pusty lub nie zawiera nagłówka.", file=sys.stderr)
                sys.exit(1)

            for col in header:
                print(col.strip())

    except FileNotFoundError:
        print(f"Nie znaleziono pliku: {CSV_PATH}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError:
        print("Błąd dekodowania. Zmień ENCODING (np. na 'cp1250').", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
