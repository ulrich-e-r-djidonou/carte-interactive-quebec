"""
prepare_geometries.py
---------------------
Telecharge la couche officielle des decoupages administratifs du Quebec (BDGA 1M - MRNF / Donnees Quebec),
extrait les polygones des 3 echelles :
1. Regions administratives (17 regions officielles)
2. MRC (Municipalites regionales de comte et territoires equivalents)
3. Municipalites locales / Villes

Effectue :
- La fusion (dissolve) des entites decoupees (iles, fragments) par code administratif
- La simplification geometrique controlee pour un affichage web ultra-rapide (Datawrapper-like)
- L'harmonisation des attributs (code, nom, region, mrc)
- L'export en GeoJSON WGS84 et la creation d'un referentiel geographique tabulaire (CSV/Excel)
"""

import os
import sys
import io
import json
import zipfile
import requests
import shapefile
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# Forcer encodage UTF-8 standard console Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
GEOJSON_DIR = os.path.join(DATA_DIR, "geojson")
REF_DIR = os.path.join(DATA_DIR, "references")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

os.makedirs(GEOJSON_DIR, exist_ok=True)
os.makedirs(REF_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

BDGA_URL = "https://diffusion.mern.gouv.qc.ca/Diffusion/RGQ/Vectoriel/Theme/Provincial/BDGA_1M(adm)/SHP/BDGA_1M(adm)_SHP.zip"
ZIP_PATH = os.path.join(CACHE_DIR, "BDGA_1M_adm_SHP.zip")
EXTRACT_DIR = os.path.join(CACHE_DIR, "bdga_extracted")


def download_bdga():
    if not os.path.exists(ZIP_PATH):
        print(f"Telechargement de {BDGA_URL}...")
        resp = requests.get(BDGA_URL, stream=True)
        resp.raise_for_status()
        with open(ZIP_PATH, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        print("Telechargement termine.")
    else:
        print("Archive BDGA deja en cache.")

    if not os.path.exists(EXTRACT_DIR):
        print("Extraction de l'archive...")
        with zipfile.ZipFile(ZIP_PATH, "r") as z:
            z.extractall(EXTRACT_DIR)
        print("Extraction terminee.")
    else:
        print("Fichiers extraits deja disponibles.")


def round_coordinates(geom_dict, precision=4):
    """Arrondit les coordonnees pour reduire la taille du GeoJSON."""
    def _round_coords(coords):
        if isinstance(coords[0], (int, float)):
            return [round(coords[0], precision), round(coords[1], precision)]
        return [_round_coords(c) for c in coords]

    if "coordinates" in geom_dict:
        geom_dict["coordinates"] = _round_coords(geom_dict["coordinates"])
    return geom_dict


def process_regions():
    print("\n--- Traitement des regions administratives ---")
    shp_path = os.path.join(EXTRACT_DIR, "Bdga1m", "SHP", "regio_s.shp")
    sf = shapefile.Reader(shp_path, encoding="utf-8")
    
    # Grouper par RES_CO_REG
    grouped = {}
    for sr in sf.shapeRecords():
        rec = sr.record
        code_reg = str(rec["RES_CO_REG"]).strip().zfill(2)
        nom_reg = str(rec["RES_NM_REG"]).strip()
        geom = shape(sr.shape.__geo_interface__)
        if not geom.is_valid:
            geom = geom.buffer(0)
            
        if code_reg not in grouped:
            grouped[code_reg] = {"nom": nom_reg, "geoms": []}
        grouped[code_reg]["geoms"].append(geom)
    sf.close()

    features = []
    # Ordre officiel des 17 regions
    for code_reg in sorted(grouped.keys()):
        item = grouped[code_reg]
        merged_geom = unary_union(item["geoms"])
        # Simplification legere ~ 0.005 deg (~500m)
        simplified = merged_geom.simplify(0.003, preserve_topology=True)
        geom_json = round_coordinates(mapping(simplified), precision=4)
        
        feature = {
            "type": "Feature",
            "id": code_reg,
            "properties": {
                "code": code_reg,
                "nom": item["nom"],
                "echelle": "region",
                "label": f"{code_reg} - {item['nom']}"
            },
            "geometry": geom_json
        }
        features.append(feature)

    out_geojson = {
        "type": "FeatureCollection",
        "name": "quebec_regions_administratives",
        "features": features
    }

    out_path = os.path.join(GEOJSON_DIR, "quebec_regions.geojson")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_geojson, f, ensure_ascii=False)
    print(f"Regions generees : {len(features)} entites -> {out_path} ({os.path.getsize(out_path) / 1024:.1f} KB)")


def process_mrc():
    print("\n--- Traitement des MRC ---")
    shp_path = os.path.join(EXTRACT_DIR, "Bdga1m", "SHP", "mrc_s.shp")
    sf = shapefile.Reader(shp_path, encoding="utf-8")

    grouped = {}
    for sr in sf.shapeRecords():
        rec = sr.record
        code_mrc = str(rec["MRS_CO_MRC"]).strip()
        nom_mrc = str(rec["MRS_NM_MRC"]).strip()
        code_reg = str(rec["MRS_CO_REG"]).strip().zfill(2)
        nom_reg = str(rec["MRS_NM_REG"]).strip()
        geom = shape(sr.shape.__geo_interface__)
        if not geom.is_valid:
            geom = geom.buffer(0)

        if code_mrc not in grouped:
            grouped[code_mrc] = {
                "nom": nom_mrc,
                "code_region": code_reg,
                "nom_region": nom_reg,
                "geoms": []
            }
        grouped[code_mrc]["geoms"].append(geom)
    sf.close()

    features = []
    for code_mrc in sorted(grouped.keys()):
        item = grouped[code_mrc]
        merged_geom = unary_union(item["geoms"])
        # Simplification legere ~ 0.003 deg
        simplified = merged_geom.simplify(0.002, preserve_topology=True)
        geom_json = round_coordinates(mapping(simplified), precision=4)

        feature = {
            "type": "Feature",
            "id": code_mrc,
            "properties": {
                "code": code_mrc,
                "nom": item["nom"],
                "code_region": item["code_region"],
                "nom_region": item["nom_region"],
                "echelle": "mrc",
                "label": f"{item['nom']} (MRC {code_mrc})"
            },
            "geometry": geom_json
        }
        features.append(feature)

    out_geojson = {
        "type": "FeatureCollection",
        "name": "quebec_mrc",
        "features": features
    }

    out_path = os.path.join(GEOJSON_DIR, "quebec_mrc.geojson")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_geojson, f, ensure_ascii=False)
    print(f"MRC generees : {len(features)} entites -> {out_path} ({os.path.getsize(out_path) / 1024:.1f} KB)")


def process_municipalites_and_villes():
    print("\n--- Traitement des municipalites et villes ---")
    shp_path = os.path.join(EXTRACT_DIR, "Bdga1m", "SHP", "munic_s.shp")
    sf = shapefile.Reader(shp_path, encoding="utf-8")

    grouped = {}
    rows_ref = []

    try:
        field_names = [f[0] for f in sf.fields[1:]]
        for sr in sf.shapeRecords():
            rec_dict = dict(zip(field_names, sr.record))
            code_mun = str(rec_dict.get("MUS_CO_GEO", "")).strip()
            nom_mun = str(rec_dict.get("MUS_NM_MUN", "")).strip()
            desig = str(rec_dict.get("MUS_CO_DES", "")).strip()
            code_mrc = str(rec_dict.get("MUS_CO_MRC", "")).strip()
            nom_mrc = str(rec_dict.get("MUS_NM_MRC", "")).strip()
            code_reg = str(rec_dict.get("MUS_CO_REG", "")).strip().zfill(2)
            nom_reg = str(rec_dict.get("MUS_NM_REG", "")).strip()

            geom = shape(sr.shape.__geo_interface__)
            if not geom.is_valid:
                geom = geom.buffer(0)

            if code_mun not in grouped:
                grouped[code_mun] = {
                    "nom": nom_mun,
                    "designation": desig,
                    "code_mrc": code_mrc,
                    "nom_mrc": nom_mrc,
                    "code_region": code_reg,
                    "nom_region": nom_reg,
                    "geoms": []
                }
                rows_ref.append({
                    "code_municipalite": code_mun,
                    "nom_municipalite": nom_mun,
                    "designation": desig,
                    "code_mrc": code_mrc,
                    "nom_mrc": nom_mrc,
                    "code_region": code_reg,
                    "nom_region": nom_reg
                })
            grouped[code_mun]["geoms"].append(geom)
    finally:
        sf.close()

    # Sauvegarder le referentiel tabulaire en CSV
    import pandas as pd
    df_ref = pd.DataFrame(rows_ref)
    ref_csv_path = os.path.join(REF_DIR, "referentiel_geographique_quebec.csv")
    df_ref.to_csv(ref_csv_path, index=False, encoding="utf-8")
    print(f"Referentiel officiel exporte : {len(df_ref)} municipalites -> {ref_csv_path}")

    # Separer villes (V) et municipalites principales
    features_villes = []
    features_all = []

    # Seuil de simplification un peu plus fin pour municipalites
    for code_mun, item in grouped.items():
        merged_geom = unary_union(item["geoms"])
        # Simplification adaptee
        simplified = merged_geom.simplify(0.0015, preserve_topology=True)
        geom_json = round_coordinates(mapping(simplified), precision=4)

        desig_libelle = "Ville" if item["designation"] == "V" else item["designation"]
        feature = {
            "type": "Feature",
            "id": code_mun,
            "properties": {
                "code": code_mun,
                "nom": item["nom"],
                "designation": desig_libelle,
                "code_mrc": item["code_mrc"],
                "nom_mrc": item["nom_mrc"],
                "code_region": item["code_region"],
                "nom_region": item["nom_region"],
                "echelle": "municipalite",
                "label": f"{item['nom']} ({desig_libelle})"
            },
            "geometry": geom_json
        }
        features_all.append(feature)

        # Si designation 'V' (Ville officielle du Quebec)
        if item["designation"] == "V":
            feature_ville = dict(feature)
            feature_ville["properties"] = dict(feature["properties"])
            feature_ville["properties"]["echelle"] = "ville"
            features_villes.append(feature_ville)

    # 1. Export Villes (couche legere ~230 villes officielles, tres demandee et reactive)
    out_villes = {
        "type": "FeatureCollection",
        "name": "quebec_villes",
        "features": features_villes
    }
    villes_path = os.path.join(GEOJSON_DIR, "quebec_villes.geojson")
    with open(villes_path, "w", encoding="utf-8") as f:
        json.dump(out_villes, f, ensure_ascii=False)
    print(f"Villes officielles generees : {len(features_villes)} entites -> {villes_path} ({os.path.getsize(villes_path) / 1024:.1f} KB)")

    # 2. Export Toutes les municipalites (~1300 entites)
    out_all = {
        "type": "FeatureCollection",
        "name": "quebec_municipalites_completes",
        "features": features_all
    }
    all_path = os.path.join(GEOJSON_DIR, "quebec_municipalites.geojson")
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(out_all, f, ensure_ascii=False)
    print(f"Toutes municipalites generees : {len(features_all)} entites -> {all_path} ({os.path.getsize(all_path) / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    download_bdga()
    process_regions()
    process_mrc()
    process_municipalites_and_villes()
    print("\nTraitement des geometries termine avec succes.")
