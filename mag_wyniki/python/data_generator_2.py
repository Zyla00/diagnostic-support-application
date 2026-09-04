import pandas as pd
import json
import random
import os
from tqdm import tqdm
import nlpaug.augmenter.word as naw

BATCH_SIZE = 100
N_OPISOW_NA_PRZYPADEK = (3, 10)

ENCOUNTER_PATH = "medsynora/FactEncounter.csv"
DISEASE_DIM_PATH = "medsynora/DimDisease.csv"
CHOROBY_JSON_PATH = "choroby/choroby_wszystkie_30.json"
OUTPUT_PATH = "FactEncounter_with_descriptions.csv"

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
    return random.sample(losowe, min(len(losowe), random.randint(*zakres)))

def parafrazuj_tekst(text):
    try:
        if random.random() < 0.5:
            return syn_aug.augment(text, n=1)[0]
        return text
    except:
        return text

def buduj_opis(objawy, czasy, dziedzicznosc, choroba_nazwa=None):
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
            f"W rodzinie występowała choroba {choroba_nazwa}.",
            f"Podobne objawy były zgłaszane u krewnych z chorobą {choroba_nazwa}.",
            f"Występują rodzinne predyspozycje do {choroba_nazwa}.",
            f"Zgłaszano przypadki {choroba_nazwa} w rodzinie."
        ]
        tekst += ". " + random.choice(dodatki)

    return tekst

def generuj_opisy_dla_przypadku(choroba_nazwa, choroba_dane):
    objawy = choroba_dane['objawy']
    czasy = choroba_dane['czas_trwania_objawow']
    dziedz = choroba_dane.get('dziedziczność', {
        'istnieje_ryzyko': False,
        'prawdopodobieństwo_dziedziczne': 0.0
    })
    liczba_opisow = random.randint(*N_OPISOW_NA_PRZYPADEK)
    return [
        buduj_opis(losuj_objawy(objawy, (3, 10)), czasy, dziedz, choroba_nazwa)
        for _ in range(liczba_opisow)
    ]


def generuj_opisy():
    print(f"\nWczytywanie danych wejściowych...")
    df = pd.read_csv(ENCOUNTER_PATH)
    dim = pd.read_csv(DISEASE_DIM_PATH)
    with open(CHOROBY_JSON_PATH, 'r', encoding='utf-8') as f:
        choroby_data = json.load(f)

    choroby_dict = {c['choroba']: c for c in choroby_data}
    dim_map = dict(zip(dim[DISEASE_ID_COL], dim[DISEASE_NAME_COL]))
    df[DISEASE_NAME_COL] = df[DISEASE_ID_COL].map(dim_map)

    print(f"🛠 Rozpoczynam generowanie opisów ({len(df)} rekordów)...")

    if os.path.exists(OUTPUT_PATH):
        print(f"⚠ Plik wyjściowy już istnieje – zostanie nadpisany: {OUTPUT_PATH}")
        os.remove(OUTPUT_PATH)

    for start in tqdm(range(0, len(df), BATCH_SIZE), desc="Przetwarzanie batchy"):
        end = start + BATCH_SIZE
        batch = df.iloc[start:end].copy()

        batch['generated_case_descriptions'] = batch[DISEASE_NAME_COL].apply(
            lambda x: generuj_opisy_dla_przypadku(x, choroby_dict[x]) if x in choroby_dict else []
        )

        header = not os.path.exists(OUTPUT_PATH)
        batch.to_csv(OUTPUT_PATH, mode='a', header=header, index=False)

        if start % (BATCH_SIZE * 10) == 0:
            print(f"Przetworzono {start} przypadków...")

    print(f"\nGotowe! Opisy zapisano do: {OUTPUT_PATH}\n")

if __name__ == "__main__":
    generuj_opisy()
