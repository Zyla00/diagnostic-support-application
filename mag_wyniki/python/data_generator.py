import pandas as pd
import json
import random
import os
from tqdm import tqdm
import nlpaug.augmenter.word as naw

BATCH_SIZE = 100
ENCOUNTER_PATH = "medsynora/FactEncounter.csv"
DISEASE_DIM_PATH = "tlumaczenie_mat/ready/DimDisease_translated.csv"  
CHOROBY_JSON_PATH = "choroby/choroby_wszystkie_30.json"
OUTPUT_PATH = "FactEncounter_with_descriptions_3.csv"

DISEASE_ID_COL = "Disease_ID"
DISEASE_NAME_COL = "Admission Diagnosis"

syn_aug = naw.SynonymAug(aug_src='wordnet')

LACZNIKI = [
    "również", "co ciekawe", "dodatkowo", "jak się okazuje",
    "warto dodać, że", "co więcej", "niewykluczone, że",
    "na marginesie", "jak wskazano", "zauważono także, że",
    "trzeba wspomnieć, że", "co istotne", "bywa również, że",
    "w niektórych przypadkach", "obserwowano też", "czasem dochodzi do"
]


def losuj_objawy(objawy_dict, zakres):
    objawy = list(objawy_dict.items())
    losowe = [obj for obj in objawy if random.random() < obj[1]]
    if len(losowe) < 3:
        losowe = sorted(objawy, key=lambda x: -x[1])[:3]
    return random.sample(losowe, min(len(losowe), random.randint(*zakres)))


def parafrazuj_tekst(text):
    try:
        if random.random() < 0.5:
            return syn_aug.augment(text, n=1)[0]
        return text
    except:
        return text


def buduj_opis(objawy, czasy, dziedzicznosc, choroba_nazwa=None, jednostka_medyczna=None):
    frazy = []
    for objaw, _ in objawy:
        czas = czasy.get(objaw, "od niedawna")
        fraza = f"{objaw} ({czas})"

        if random.random() < 0.65:
            fraza = random.choice(LACZNIKI) + ", " + fraza
        frazy.append(fraza)

    tekst = ", ".join(frazy)
    tekst = parafrazuj_tekst(tekst)

    if dziedzicznosc.get('istnieje_ryzyko') and random.random() < dziedzicznosc.get('prawdopodobieństwo_dziedziczne', 0):
        dodatki = [
            f"W rodzinie występowały przypadki z zakresu {jednostka_medyczna}.",
            f"Podobne objawy były zgłaszane u krewnych z jednostkami {jednostka_medyczna}.",
            f"Występują rodzinne predyspozycje do schorzeń w dziedzinie {jednostka_medyczna}.",
            f"Zgłaszano przypadki chorób z obszaru {jednostka_medyczna} w rodzinie."
        ]
        tekst += ". " + random.choice(dodatki)

    return tekst


def generuj_opis_dla_przypadku(choroba_nazwa, jednostka_medyczna, choroba_dane):
    objawy = choroba_dane['objawy']
    czasy = choroba_dane['czas_trwania_objawow']
    dziedz = choroba_dane.get('dziedziczność', {
        'istnieje_ryzyko': False,
        'prawdopodobieństwo_dziedziczne': 0.0
    })
    opis = buduj_opis(losuj_objawy(objawy, (3, 10)), czasy, dziedz, choroba_nazwa, jednostka_medyczna)
    return opis


def generuj_opisy():
    print(f"\nWczytywanie danych wejściowych...")
    df = pd.read_csv(ENCOUNTER_PATH)
    dim = pd.read_csv(DISEASE_DIM_PATH)
    with open(CHOROBY_JSON_PATH, 'r', encoding='utf-8') as f:
        choroby_data = json.load(f)

    choroby_dict = {c['choroba']: c for c in choroby_data}

    dim_map_name_en = dict(zip(dim[DISEASE_ID_COL], dim['Admission Diagnosis']))
    dim_map_name_pl = dict(zip(dim[DISEASE_ID_COL], dim['Diagnoza przyjmowania']))
    dim_map_jednostka = dict(zip(dim[DISEASE_ID_COL], dim['Jednostka medyczna']))

    df[DISEASE_NAME_COL] = df[DISEASE_ID_COL].map(dim_map_name_en)
    df['Diagnoza przyjmowania'] = df[DISEASE_ID_COL].map(dim_map_name_pl)
    df['Jednostka medyczna'] = df[DISEASE_ID_COL].map(dim_map_jednostka)

    print(f"🛠 Rozpoczynam generowanie opisów ({len(df)} rekordów)...")

    if os.path.exists(OUTPUT_PATH):
        print(f"Plik wyjściowy już istnieje – zostanie nadpisany: {OUTPUT_PATH}")
        os.remove(OUTPUT_PATH)

    for start in tqdm(range(0, len(df), BATCH_SIZE), desc="Przetwarzanie batchy"):
        end = start + BATCH_SIZE
        batch = df.iloc[start:end].copy()

        batch['generated_case_description'] = batch.apply(
            lambda row: generuj_opis_dla_przypadku(
                row[DISEASE_NAME_COL],
                row['Jednostka medyczna'],
                choroby_dict[row[DISEASE_NAME_COL]]
            ) if row[DISEASE_NAME_COL] in choroby_dict else "",
            axis=1
        )

        header = not os.path.exists(OUTPUT_PATH)
        batch.to_csv(OUTPUT_PATH, mode='a', header=header, index=False)

        if start % (BATCH_SIZE * 10) == 0:
            print(f"Przetworzono {start} przypadków...")

    print(f"\nGotowe! Opisy zapisano do: {OUTPUT_PATH}\n")


if __name__ == "__main__":
    generuj_opisy()
