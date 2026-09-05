file_path = 'tlumaczenie/Patient_Allergy_translated.csv'

try:
    with open(file_path, 'r', encoding='utf-8') as file:
        for i, line in enumerate(file):
            if i >= 10:
                break
            print(line.strip())
except Exception as e:
    print(f"Błąd podczas odczytu pliku: {e}")
