import pandas as pd
from typing import List, Dict


def przygotuj_dane(
    dimpatient_path: str,
    kolumny_z_dimpatient: Dict[str, str],
    dodatkowe_pliki: List[Dict],
    plik_z_labelami: Dict,
    output_path: str = "final_bert_dataset.csv"
):
    print("Wczytywanie DimPatient...")
    usecols_dim = ["Patient_ID"] + list(kolumny_z_dimpatient.keys())
    df = pd.read_csv(dimpatient_path, usecols=usecols_dim)

    df.rename(columns=kolumny_z_dimpatient, inplace=True)

    df["Dane pacjenta"] = df[list(kolumny_z_dimpatient.values())].apply(
        lambda row: " | ".join([f"{col}: {row[col]}" for col in kolumny_z_dimpatient.values() if pd.notna(row[col])]),
        axis=1
    )
    df = df[["Patient_ID", "Dane pacjenta"]]

    for plik in dodatkowe_pliki:
        path = plik["path"]
        kolumny = plik["columns"]

        print(f"Dołączanie danych z: {path} ({len(kolumny)} kolumn)")
        usecols = ["Patient_ID"] + list(kolumny.keys())
        data = pd.read_csv(path, usecols=usecols)

        data.rename(columns=kolumny, inplace=True)

        grouped = data.groupby("Patient_ID").apply(
            lambda g: " | ".join([
                " | ".join([f"{col}: {val}" for col, val in row.items() if col != "Patient_ID" and pd.notna(val)])
                for _, row in g.iterrows()
            ])
        ).reset_index(name="dodatek")

        df = df.merge(grouped, on="Patient_ID", how="left")
        df["dodatek"] = df["dodatek"].fillna("")
        df["Dane pacjenta"] = df.apply(
            lambda row: row["Dane pacjenta"] + " | " + row["dodatek"] if row["dodatek"] else row["Dane pacjenta"],
            axis=1
        )
        df.drop(columns=["dodatek"], inplace=True)

    print(f"Dołączanie labeli z: {plik_z_labelami['path']}")
    label_map = plik_z_labelami["label_columns"] 
    usecols_labels = ["Patient_ID"] + list(label_map.keys())
    labels_df = pd.read_csv(plik_z_labelami["path"], usecols=usecols_labels)
    labels_df.rename(columns=label_map, inplace=True)

    df = df.merge(labels_df, on="Patient_ID", how="left")

    final_cols = ["Patient_ID", "Dane pacjenta"] + list(label_map.values())
    df = df[final_cols]

    print(f"Zapisuję wynik do: {output_path}")
    df.to_csv(output_path, index=False)
    print("Gotowe!")



if __name__ == "__main__":
    przygotuj_dane(
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
                    "generated_case_description": "Opis przypadku"
                }
            },
            {
                "path": "pacjenci_z_alergenami.csv",
                "columns": {
                    "nazwa_alergenu": "nazwa_alergenu"
                }
            },

            {
                "path": "pacjenci_z_chorobami_przewleklymi.csv",
                "columns": {
                    "choroba_przewlekła": "choroba_przewlekła"
                }
            }
        ],

        plik_z_labelami={
            "path": "FactEncounter_with_descriptions_3.csv",
            "label_columns": {
                "Admission Diagnosis": "Admission Diagnosis",
                "Diagnoza przyjmowania": "Diagnoza przyjmowania",
                "Jednostka medyczna": "Jednostka medyczna"
            }
        },

        output_path="final_bert_dataset.csv"
    )
