"""
generate_sample_data.py
-----------------------
Genere des jeux de donnees socio-economiques de demonstration pour le Quebec
aux 3 echelles :
1. Regions administratives (17 regions)
2. MRC (104 MRC)
3. Villes officielles (231 villes)

Les valeurs sont basees sur les ordres de grandeur officiels de l'Institut de la statistique
du Quebec (ISQ) et de Statistique Canada.
"""

import os
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
GEOJSON_DIR = os.path.join(DATA_DIR, "geojson")
EXAMPLES_DIR = os.path.join(DATA_DIR, "examples")
os.makedirs(EXAMPLES_DIR, exist_ok=True)

# 1. Regions administratives
def make_regions_demo():
    geojson_path = os.path.join(GEOJSON_DIR, "quebec_regions.geojson")
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Donnees realistes ISQ / StatCan
    base_data = {
        "01": {"pop": 201000, "chomage": 5.1, "rev_median": 63200, "jeunes_pct": 18.2, "croissance": 0.4},
        "02": {"pop": 281000, "chomage": 5.4, "rev_median": 66400, "jeunes_pct": 19.1, "croissance": 0.2},
        "03": {"pop": 765000, "chomage": 3.7, "rev_median": 74800, "jeunes_pct": 19.5, "croissance": 1.1},
        "04": {"pop": 277000, "chomage": 5.2, "rev_median": 62500, "jeunes_pct": 17.8, "croissance": 0.5},
        "05": {"pop": 348000, "chomage": 4.5, "rev_median": 68900, "jeunes_pct": 20.2, "croissance": 1.3},
        "06": {"pop": 2085000, "chomage": 5.9, "rev_median": 65100, "jeunes_pct": 18.9, "croissance": 1.4},
        "07": {"pop": 415000, "chomage": 4.3, "rev_median": 79200, "jeunes_pct": 21.8, "croissance": 1.2},
        "08": {"pop": 150000, "chomage": 4.8, "rev_median": 72100, "jeunes_pct": 21.0, "croissance": 0.1},
        "09": {"pop": 90000, "chomage": 5.6, "rev_median": 78300, "jeunes_pct": 20.5, "croissance": -0.3},
        "10": {"pop": 47000, "chomage": 6.8, "rev_median": 76500, "jeunes_pct": 29.4, "croissance": 0.9},
        "11": {"pop": 91000, "chomage": 8.7, "rev_median": 58900, "jeunes_pct": 16.4, "croissance": -0.2},
        "12": {"pop": 435000, "chomage": 3.6, "rev_median": 73400, "jeunes_pct": 20.8, "croissance": 0.9},
        "13": {"pop": 451000, "chomage": 5.3, "rev_median": 71800, "jeunes_pct": 21.5, "croissance": 1.0},
        "14": {"pop": 542000, "chomage": 4.6, "rev_median": 76100, "jeunes_pct": 22.1, "croissance": 1.5},
        "15": {"pop": 655000, "chomage": 4.4, "rev_median": 75300, "jeunes_pct": 21.3, "croissance": 1.6},
        "16": {"pop": 1640000, "chomage": 4.2, "rev_median": 78900, "jeunes_pct": 22.4, "croissance": 1.2},
        "17": {"pop": 253000, "chomage": 4.0, "rev_median": 67800, "jeunes_pct": 20.1, "croissance": 0.8},
    }

    rows = []
    for f in data["features"]:
        code = f["properties"]["code"]
        nom = f["properties"]["nom"]
        d = base_data.get(code, {"pop": 100000, "chomage": 5.0, "rev_median": 65000, "jeunes_pct": 20.0, "croissance": 0.5})
        rows.append({
            "code_region": code,
            "region": nom,
            "population": d["pop"],
            "taux_chomage": d["chomage"],
            "revenu_median": d["rev_median"],
            "part_jeunes_pct": d["jeunes_pct"],
            "croissance_demographique_pct": d["croissance"]
        })

    df = pd.DataFrame(rows)
    csv_path = os.path.join(EXAMPLES_DIR, "demo_regions_quebec.csv")
    xlsx_path = os.path.join(EXAMPLES_DIR, "demo_regions_quebec.xlsx")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_excel(xlsx_path, index=False)
    print(f"Demo regions cree : {len(df)} lignes -> {csv_path}")


# 2. MRC
def make_mrc_demo():
    geojson_path = os.path.join(GEOJSON_DIR, "quebec_mrc.geojson")
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    np.random.seed(42)
    rows = []
    for f in data["features"]:
        code = f["properties"]["code"]
        nom = f["properties"]["nom"]
        code_reg = f["properties"]["code_region"]
        nom_reg = f["properties"]["nom_region"]

        # Valeurs simulees et coherentes par region
        if code in ["66", "23", "65", "64", "58"]:
            pop = int(np.random.normal(300000, 50000)) if code != "66" else 2085000
            vitalite = round(float(np.random.normal(8.5, 0.8)), 1)
            densite = round(float(np.random.normal(1200, 300)), 1)
        else:
            pop = max(4500, int(np.random.exponential(45000)))
            vitalite = round(float(np.random.normal(5.0, 1.5)), 1)
            densite = round(max(0.5, float(np.random.exponential(25))), 1)

        indice_defavorisation = round(float(np.random.uniform(1.0, 5.0)), 2)
        tx_activite = round(float(np.random.normal(63.0, 4.0)), 1)

        rows.append({
            "code_mrc": code,
            "mrc": nom,
            "code_region": code_reg,
            "region": nom_reg,
            "population": pop,
            "densite_km2": densite,
            "vitalite_economique": vitalite,
            "indice_defavorisation": indice_defavorisation,
            "taux_activite_pct": tx_activite
        })

    df = pd.DataFrame(rows)
    csv_path = os.path.join(EXAMPLES_DIR, "demo_mrc_quebec.csv")
    xlsx_path = os.path.join(EXAMPLES_DIR, "demo_mrc_quebec.xlsx")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_excel(xlsx_path, index=False)
    print(f"Demo MRC cree : {len(df)} lignes -> {csv_path}")


# 3. Villes officielles
def make_villes_demo():
    geojson_path = os.path.join(GEOJSON_DIR, "quebec_villes.geojson")
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    np.random.seed(101)
    rows = []
    for f in data["features"]:
        code = f["properties"]["code"]
        nom = f["properties"]["nom"]
        code_reg = f["properties"]["code_region"]
        nom_reg = f["properties"]["nom_region"]
        code_mrc = f["properties"]["code_mrc"]
        nom_mrc = f["properties"]["nom_mrc"]

        if nom == "Montréal":
            pop = 1800000
            rev = 62000
            age = 39.5
        elif nom == "Québec":
            pop = 550000
            rev = 71000
            age = 42.1
        elif nom == "Laval":
            pop = 445000
            rev = 73000
            age = 40.8
        elif nom == "Gatineau":
            pop = 295000
            rev = 81000
            age = 39.1
        elif nom == "Longueuil":
            pop = 255000
            rev = 69000
            age = 41.5
        elif nom == "Sherbrooke":
            pop = 175000
            rev = 61000
            age = 40.2
        elif nom == "Trois-Rivières":
            pop = 142000
            rev = 59000
            age = 45.3
        elif nom == "Lévis":
            pop = 152000
            rev = 79000
            age = 41.2
        elif nom == "Saguenay":
            pop = 148000
            rev = 64000
            age = 46.1
        else:
            pop = max(2000, int(np.random.exponential(18000)))
            rev = int(np.random.normal(67000, 8000))
            age = round(float(np.random.normal(43.5, 3.5)), 1)

        pct_proprietaires = round(float(np.clip(np.random.normal(64.0, 10.0), 30.0, 88.0)), 1)

        rows.append({
            "code_ville": code,
            "ville": nom,
            "code_mrc": code_mrc,
            "mrc": nom_mrc,
            "code_region": code_reg,
            "region": nom_reg,
            "population": pop,
            "revenu_median": rev,
            "age_median": age,
            "taux_proprietaires_pct": pct_proprietaires
        })

    df = pd.DataFrame(rows)
    csv_path = os.path.join(EXAMPLES_DIR, "demo_villes_quebec.csv")
    xlsx_path = os.path.join(EXAMPLES_DIR, "demo_villes_quebec.xlsx")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_excel(xlsx_path, index=False)
    print(f"Demo villes cree : {len(df)} lignes -> {csv_path}")


if __name__ == "__main__":
    make_regions_demo()
    make_mrc_demo()
    make_villes_demo()
    print("Tous les jeux de demonstration ont ete generes.")
