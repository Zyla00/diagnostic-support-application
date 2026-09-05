import pandas as pd

# plik_pacjenci = 'tlumaczenie_mat/ready/Patient_Allergy_translated.csv'              # Nazwa pliku z pacjentami
# plik_alergeny = 'tlumaczenie_mat/ready/DimAllergy_translated.csv'              # Nazwa pliku z alergenami
# kol_id_pacjenta = 'Patient_ID'              # Kolumna z ID pacjenta
# kol_nr_alergii_pacjenta = 'AllergyID'      # Kolumna z numerem alergii w pliku pacjentów
# kol_nr_alergii_slownik = 'AllergyID'      # Kolumna z numerem alergii w pliku alergenów
# kol_nazwa_alergenu = 'AlergiaName'       # Kolumna z nazwą alergenu
# output_file = 'pacjenci_z_alergenami.csv'   # Nazwa pliku wyjściowego

plik_pacjenci = 'medsynora/Patient_ChronicDisease.csv'              # Nazwa pliku z pacjentami
plik_alergeny = 'tlumaczenie_mat/ready/DimChronicDisease_translated.csv'              # Nazwa pliku z alergenami
kol_id_pacjenta = 'Patient_ID'              # Kolumna z ID pacjenta
kol_nr_alergii_pacjenta = 'ChronicDiseaseID'      # Kolumna z numerem alergii w pliku pacjentów
kol_nr_alergii_slownik = 'ChronicDiseaseID'      # Kolumna z numerem alergii w pliku alergenów
kol_nazwa_alergenu = 'Przewlekła chorobaName'       # Kolumna z nazwą alergenu
output_file = 'pacjenci_z_chorobami_przewleklymi.csv'   # Nazwa pliku wyjściowego

def dodaj_nazwe_alergenu():
    try:

        df_pacjenci = pd.read_csv(plik_pacjenci)
        df_alergeny = pd.read_csv(plik_alergeny)

        for kolumna in [kol_id_pacjenta, kol_nr_alergii_pacjenta]:
            if kolumna not in df_pacjenci.columns:
                raise ValueError(f"Brak kolumny '{kolumna}' w pliku pacjentów.")

        for kolumna in [kol_nr_alergii_slownik, kol_nazwa_alergenu]:
            if kolumna not in df_alergeny.columns:
                raise ValueError(f"Brak kolumny '{kolumna}' w pliku alergenów.")

        mapa_alergenow = dict(zip(df_alergeny[kol_nr_alergii_slownik], df_alergeny[kol_nazwa_alergenu]))

        df_pacjenci['choroba_przewlekła'] = df_pacjenci[kol_nr_alergii_pacjenta].map(mapa_alergenow)

        df_pacjenci.to_csv(output_file, index=False)
        print(f'Zapisano plik wynikowy: {output_file}')

    except Exception as e:
        print(f'Błąd: {e}')

if __name__ == '__main__':
    dodaj_nazwe_alergenu()
