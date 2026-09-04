import pandas as pd

# 🔧 KONFIGURACJA – wpisz swoje nazwy plików i kolumn
plik_fact_encounter = 'tlumaczenie/FactEncounter_with_descriptions.csv'     # Plik główny z chorobami
plik_dimdisease = 'tlumaczenie_mat/ready/DimDisease_translated.csv'             # Słownik chorób

kol_disease_id_fact = 'Disease_ID'             # Kolumna ID choroby w fact_encounter
kol_disease_id_dim = 'Disease_ID'              # Kolumna ID choroby w dimdisease

kol_nazwa_choroby = 'Diagnoza przyjmowania'                    # Kolumna z nazwą choroby w dimdisease
kol_dziedzina_choroby = 'Jednostka medyczna'            # Kolumna z dziedziną w dimdisease

output_file = 'fact_encounter_z_opisem.csv'    # Nazwa pliku wynikowego

def dopisz_nazwe_i_dziedzine_choroby():
    try:
        # Wczytaj dane
        df_fact = pd.read_csv(plik_fact_encounter)
        df_dim = pd.read_csv(plik_dimdisease)

        for kol in [kol_disease_id_fact]:
            if kol not in df_fact.columns:
                raise ValueError(f"Brakuje kolumny '{kol}' w pliku fact_encounter.")

        for kol in [kol_disease_id_dim, kol_nazwa_choroby, kol_dziedzina_choroby]:
            if kol not in df_dim.columns:
                raise ValueError(f"Brakuje kolumny '{kol}' w pliku dimdisease.")

        df_wynik = pd.merge(df_fact, df_dim[[kol_disease_id_dim, kol_nazwa_choroby, kol_dziedzina_choroby]],
                            how='left',
                            left_on=kol_disease_id_fact,
                            right_on=kol_disease_id_dim)

        if kol_disease_id_dim != kol_disease_id_fact:
            df_wynik.drop(columns=[kol_disease_id_dim], inplace=True)

        df_wynik.to_csv(output_file, index=False)
        print(f'Zapisano plik wynikowy: {output_file}')

    except Exception as e:
        print(f'Błąd: {e}')

if __name__ == '__main__':
    dopisz_nazwe_i_dziedzine_choroby()
