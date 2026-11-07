"""
qc_carto.data_loader
--------------------
Gestion du chargement et de la mise en cache des decoupages administratifs
officiels du Quebec et du referentiel geographique.
"""

import os
import json
import pandas as pd
from typing import Dict, Any, Optional

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(PACKAGE_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
GEOJSON_DIR = os.path.join(DATA_DIR, "geojson")
REF_DIR = os.path.join(DATA_DIR, "references")

LEVEL_FILES = {
    "region": "quebec_regions.geojson",
    "mrc": "quebec_mrc.geojson",
    "ville": "quebec_villes.geojson",
    "municipalite": "quebec_municipalites.geojson"
}

LEVEL_LABELS = {
    "region": "Régions administratives (17)",
    "mrc": "MRC et territoires équivalents (104)",
    "ville": "Villes officielles (231)",
    "municipalite": "Municipalités complètes (1 289)"
}

_GEOJSON_CACHE: Dict[str, Dict[str, Any]] = {}
_REF_CACHE: Optional[pd.DataFrame] = None


def get_available_levels() -> Dict[str, str]:
    """Retourne la liste des echelles geographiques disponibles avec leurs libelles."""
    return dict(LEVEL_LABELS)


def load_geojson(level: str = "region") -> Dict[str, Any]:
    """
    Charge le GeoJSON correspondant a l'echelle demandee.
    Mise en cache en memoire pour des performances optimales.
    """
    level = level.lower().strip()
    if level not in LEVEL_FILES:
        raise ValueError(
            f"Echelle geographique inconnue : '{level}'. "
            f"Choix possibles : {list(LEVEL_FILES.keys())}"
        )

    if level in _GEOJSON_CACHE:
        return _GEOJSON_CACHE[level]

    file_name = LEVEL_FILES[level]
    file_path = os.path.join(GEOJSON_DIR, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Fichier GeoJSON introuvable : {file_path}. "
            "Veuillez executer 'python scripts/prepare_geometries.py' pour le generer."
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _GEOJSON_CACHE[level] = data
    return data


def get_referentiel() -> pd.DataFrame:
    """
    Retourne la table de reference officielle reliant municipalites, MRC et regions.
    """
    global _REF_CACHE
    if _REF_CACHE is not None:
        return _REF_CACHE.copy()

    ref_path = os.path.join(REF_DIR, "referentiel_geographique_quebec.csv")
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Referentiel geographique introuvable : {ref_path}")

    _REF_CACHE = pd.read_csv(ref_path, dtype={"code_municipalite": str, "code_mrc": str, "code_region": str})
    return _REF_CACHE.copy()
