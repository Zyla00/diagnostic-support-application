import pandas as pd
from typing import List, Dict


def przygotuj_dane_strukturalnie(
    dimpatient_path: str,
    kolumny_z_dimpatient: Dict[str, str],
    dodatkowe_pliki: List[Dict],
    plik_z_labelami: Dict,
    output_path: str = "final_dataset_structured.csv"
):
    print("Wczytywanie DimPatient...")
    usecols_dim = ["Patient_ID"] + list(kolumny_z_dimpatient.keys())
    df = pd.read_csv(dimpatient_path, usecols=usecols_dim)

    df.rename(columns=kolumny_z_dimpatient, inplace=True)

    wynik_df = df.copy()

    for plik in dodatkowe_pliki:
        path = plik["path"]
        kolumny = plik["columns"]
        print(f"Dołączanie danych z: {path} ({len(kolumny)} kolumn)")

        usecols = ["Patient_ID"] + list(kolumny.keys())
        data = pd.read_csv(path, usecols=usecols)
        data.rename(columns=kolumny, inplace=True)

        if "Rodzaj_badania" in data.columns and "Nazwa_testu" in data.columns and "Wartość" in data.columns:
            print("Przetwarzanie badań laboratoryjnych...")

            data["kolumna_badania"] = data["Rodzaj_badania"].astype(str) + "_" + data["Nazwa_testu"].astype(str)

            pivot = data.pivot_table(index="Patient_ID", columns="kolumna_badania", values="Wartość", aggfunc="first")
            pivot.columns = [f"badanie_{col}" for col in pivot.columns]
            pivot.reset_index(inplace=True)

            wynik_df = wynik_df.merge(pivot, on="Patient_ID", how="left")

        else:
            for col in data.columns:
                if col != "Patient_ID":
                    grouped = data.groupby("Patient_ID")[col].apply(lambda x: " | ".join(x.dropna().astype(str))).reset_index()
                    wynik_df = wynik_df.merge(grouped, on="Patient_ID", how="left")

    print(f"Dołączanie labeli z: {plik_z_labelami['path']}")
    label_map = plik_z_labelami["label_columns"]
    usecols_labels = ["Patient_ID"] + list(label_map.keys())
    labels_df = pd.read_csv(plik_z_labelami["path"], usecols=usecols_labels)
    labels_df.rename(columns=label_map, inplace=True)

    wynik_df = wynik_df.merge(labels_df, on="Patient_ID", how="left")

    print(f"Zapisuję wynik do: {output_path}")
    wynik_df.to_csv(output_path, index=False)
    print("Gotowe!")


if __name__ == "__main__":
    przygotuj_dane_strukturalnie(
        dimpatient_path="tlumaczenie_mat/ready/DimPatient_translated.csv",

        kolumny_z_dimpatient={
            "wiek_w_latach": "wiek_w_latach",
            "Płeć": "Płeć",
            "Wysokość": "Wysokość",
            "Masa": "Masa",
            "Grupa krwi": "Grupa krwi"
        },

        dodatkowe_pliki=[
            {
                "path": "tlumaczenie_mat/ready/FactLabTests_translated.csv",
                "columns": {
                    "LabType_pl": "Rodzaj_badania",
                    "TestName_pl": "Nazwa_testu",
                    "TestValue_pl": "Wartość"
                }
            },
            {
                "path": "tlumaczenie_mat/ready/FactVitals_translated.csv",
                "columns": {
                    "Temperatura": "Temperatura"
                }
            },
            {
                "path": "FactEncounter_with_descriptions_3.csv",
                "columns": {
                    "generated_case_description": "Opis_przypadku"
                }
            },
            {
                "path": "pacjenci_z_alergenami.csv",
                "columns": {
                    "nazwa_alergenu": "Alergie"
                }
            },
            {
                "path": "pacjenci_z_chorobami_przewleklymi.csv",
                "columns": {
                    "choroba_przewlekła": "Choroby_przewlekłe"
                }
            }
        ],

        plik_z_labelami={
            "path": "FactEncounter_with_descriptions_3.csv",
            "label_columns": {
                "Admission Diagnosis": "Admission_Diagnosis",
                "Diagnoza przyjmowania": "Diagnoza_przyjmowania",
                "Jednostka medyczna": "Jednostka_medyczna"
            }
        },

        output_path="final_dataset_structured.csv"
    )
