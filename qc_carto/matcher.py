"""
qc_carto.matcher
----------------
Moteur d'appariement intelligent entre les donnees tabulaires de l'utilisateur
et les entites geographiques officielles du Quebec.

Gere :
- Les correspondances par code administratif (avec ou sans zero initial)
- Les correspondances par nom avec insensibilite a la casse, aux accents,
  aux traits d'union et aux prefixes courants (ex. 'Ville de', 'MRC de')
- Les alias usuels du Quebec (ex. 'Gaspesie', 'Saguenay', 'Cote-Nord')
- Le rapport d'appariement complet (taux de couverture, entites orphelines)
"""

import re
import unicodedata
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
from .data_loader import load_geojson


def normalize_name(text: Any) -> str:
    """
    Normalise une chaine de caracteres pour la comparaison geographique :
    minuscules, suppression des accents, suppression de la ponctuation,
    et elimination des prefixes administratifs redondants.
    """
    if pd.isna(text) or text is None:
        return ""

    s = str(text).strip().lower()

    # Decomposer les caracteres accentues et enlever les diacritiques
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))

    # Supprimer les prefixes courants
    prefixes = [
        r"^ville\s+de\s+",
        r"^ville\s+d['’]",
        r"^municipalite\s+de\s+",
        r"^municipalite\s+d['’]",
        r"^canton\s+de\s+",
        r"^canton\s+d['’]",
        r"^paroisse\s+de\s+",
        r"^paroisse\s+d['’]",
        r"^mrc\s+de\s+",
        r"^mrc\s+d['’]",
        r"^region\s+de\s+",
        r"^region\s+du\s+",
        r"^region\s+des\s+",
        r"^agglomeration\s+de\s+",
        r"^agglomeration\s+d['’]"
    ]
    for p in prefixes:
        s = re.sub(p, "", s)

    # Remplacer les traits d'union, apostrophes et ponctuation par des espaces
    s = re.sub(r"[\-_'’/.,()]+", " ", s)
    # Compacter les espaces
    s = re.sub(r"\s+", " ", s).strip()

    return s


# Dictionnaire des alias frequents
COMMON_ALIASES = {
    # Regions
    "gaspesie": "gaspesie iles de la madeleine",
    "saguenay": "saguenay lac saint jean",
    "lac saint jean": "saguenay lac saint jean",
    "chaudiere": "chaudiere appalaches",
    "abitibi": "abitibi temiscamingue",
    "nord": "nord du quebec",
    "quebec metro": "capitale nationale",
    "capitale": "capitale nationale",
    # Villes & MRC
    "ville de quebec": "quebec",
    "ville de montreal": "montreal",
    "ville de gatineau": "gatineau",
    "ville de laval": "laval",
    "ville de levis": "levis",
    "ville de sherbrooke": "sherbrooke",
    "ville de trois rivieres": "trois rivieres",
    "trois-rivieres": "trois rivieres"
}


class MatchReport:
    """Rapport detaille sur la qualite de l'appariement des donnees."""

    def __init__(
        self,
        total_geo: int,
        matched_geo: int,
        total_user_rows: int,
        matched_user_rows: int,
        unmatched_user_keys: List[Any],
        unmatched_geo_codes: List[str]
    ):
        self.total_geo = total_geo
        self.matched_geo = matched_geo
        self.total_user_rows = total_user_rows
        self.matched_user_rows = matched_user_rows
        self.unmatched_user_keys = unmatched_user_keys
        self.unmatched_geo_codes = unmatched_geo_codes

    @property
    def coverage_rate(self) -> float:
        """Pourcentage des entites geographiques ayant recu des donnees."""
        if self.total_geo == 0:
            return 0.0
        return round((self.matched_geo / self.total_geo) * 100.0, 1)

    @property
    def user_match_rate(self) -> float:
        """Pourcentage des lignes utilisateurs reconnues."""
        if self.total_user_rows == 0:
            return 0.0
        return round((self.matched_user_rows / self.total_user_rows) * 100.0, 1)

    def summary_text(self) -> str:
        lines = [
            f"Couverture geographique : {self.matched_geo}/{self.total_geo} entites ({self.coverage_rate} %)",
            f"Lignes utilisateurs appariees : {self.matched_user_rows}/{self.total_user_rows} ({self.user_match_rate} %)"
        ]
        if self.unmatched_user_keys:
            sample = self.unmatched_user_keys[:5]
            lines.append(f"Exemples de cles non reconnues ({len(self.unmatched_user_keys)}) : {sample}")
        return "\n".join(lines)


def auto_detect_key_column(df: pd.DataFrame, level: str = "region") -> Optional[str]:
    """
    Tente de detecter automatiquement la colonne identifiant l'entite geographique
    a partir des noms de colonnes et des valeurs types.
    """
    cols = list(df.columns)

    # 1. Verification par mot-cle direct dans le nom de la colonne
    keywords = {
        "region": ["code_reg", "codereg", "region", "nom_reg", "reg_adm", "reg", "administrative"],
        "mrc": ["code_mrc", "codemrc", "mrc", "nom_mrc", "county"],
        "ville": ["code_ville", "code_mun", "ville", "municipalite", "nom_ville", "city"],
        "municipalite": ["code_mun", "codemun", "municipalite", "code_geo", "nom_mun", "ville"]
    }

    kw_list = keywords.get(level, ["code", "nom", "id", "geo"])

    for col in cols:
        col_clean = normalize_name(col).replace(" ", "_")
        for kw in kw_list:
            if kw in col_clean:
                return col

    # 2. Verification sur les valeurs (si colonne textuelle ou code compatible)
    geojson_data = load_geojson(level)
    known_codes = {f["properties"]["code"] for f in geojson_data["features"]}
    known_names = {normalize_name(f["properties"]["nom"]) for f in geojson_data["features"]}

    best_col = None
    best_score = 0

    for col in cols:
        vals = df[col].dropna().astype(str).tolist()
        if not vals:
            continue
        # Tester correspondance code
        code_matches = sum(1 for v in vals if v.strip() in known_codes or v.strip().zfill(2) in known_codes)
        # Tester correspondance nom
        name_matches = sum(1 for v in vals if normalize_name(v) in known_names)

        score = max(code_matches, name_matches)
        if score > best_score:
            best_score = score
            best_col = col

    if best_score > 0:
        return best_col

    # Fallback : premiere colonne
    return cols[0] if cols else None


def match_data_to_geo(
    df: pd.DataFrame,
    key_col: str,
    level: str = "region",
    value_col: Optional[str] = None
) -> Tuple[pd.DataFrame, MatchReport]:
    """
    Apparie le DataFrame de l'utilisateur avec le decoupage officiel demande.
    Retourne un DataFrame enrichi contenant pour chaque entite geographique :
    - code : code officiel
    - nom : nom officiel
    - label : etiquette officielle
    - toutes les colonnes du DataFrame utilisateur apparie
    - _matched : booleen indiquant si des donnees ont ete trouvees
    """
    geojson_data = load_geojson(level)
    features = geojson_data["features"]

    # Index de reference officiel
    geo_rows = []
    code_to_geo = {}
    name_to_geo = {}

    for f in features:
        props = f["properties"]
        code = str(props["code"]).strip()
        nom = str(props["nom"]).strip()
        norm_nom = normalize_name(nom)

        entry = {
            "code": code,
            "nom": nom,
            "label": props.get("label", nom),
            "code_region": props.get("code_region", ""),
            "nom_region": props.get("nom_region", ""),
            "code_mrc": props.get("code_mrc", ""),
            "nom_mrc": props.get("nom_mrc", ""),
            "echelle": props.get("echelle", level)
        }
        geo_rows.append(entry)
        code_to_geo[code] = entry
        # Support zero-padding pour les codes numeriques
        if code.isdigit():
            code_to_geo[str(int(code))] = entry
            code_to_geo[code.zfill(2)] = entry
            code_to_geo[code.zfill(5)] = entry

        name_to_geo[norm_nom] = entry

    df_user = df.copy()
    if key_col not in df_user.columns:
        raise KeyError(f"La colonne '{key_col}' n'existe pas dans le tableau fourni.")

    # Table de correspondance construite a partir des donnees utilisateur
    matched_records = {}
    unmatched_user_keys = []
    matched_user_row_count = 0

    for idx, row in df_user.iterrows():
        raw_val = row[key_col]
        val_str = str(raw_val).strip() if pd.notna(raw_val) else ""
        norm_val = normalize_name(val_str)
        norm_val_alias = COMMON_ALIASES.get(norm_val, norm_val)

        target_entry = None

        # 1. Test par code
        if val_str in code_to_geo:
            target_entry = code_to_geo[val_str]
        elif val_str.isdigit() and str(int(val_str)) in code_to_geo:
            target_entry = code_to_geo[str(int(val_str))]
        elif val_str.isdigit() and val_str.zfill(2) in code_to_geo:
            target_entry = code_to_geo[val_str.zfill(2)]

        # 2. Test par nom normalise ou alias
        if not target_entry:
            if norm_val in name_to_geo:
                target_entry = name_to_geo[norm_val]
            elif norm_val_alias in name_to_geo:
                target_entry = name_to_geo[norm_val_alias]

        # 3. Test partiel souple (ex. si le nom contient la cible)
        if not target_entry and len(norm_val) >= 4:
            for n_key, entry in name_to_geo.items():
                if norm_val in n_key or n_key in norm_val:
                    target_entry = entry
                    break

        if target_entry:
            code_key = target_entry["code"]
            # Conserver la derniere ligne si doublon
            row_dict = row.to_dict()
            matched_records[code_key] = row_dict
            matched_user_row_count += 1
        else:
            unmatched_user_keys.append(raw_val)

    # Fusion avec l'ensemble des entites geographiques
    merged_rows = []
    unmatched_geo_codes = []

    for geo in geo_rows:
        code = geo["code"]
        row_out = dict(geo)
        if code in matched_records:
            user_data = matched_records[code]
            for col_name, col_val in user_data.items():
                # Ne pas ecraser le code ou le nom officiel si deja present
                target_name = f"user_{col_name}" if col_name in ["code", "nom"] else col_name
                row_out[target_name] = col_val
            row_out["_matched"] = True
        else:
            # Remplir les colonnes utilisateurs par NaN
            for col_name in df_user.columns:
                target_name = f"user_{col_name}" if col_name in ["code", "nom"] else col_name
                row_out[target_name] = None
            row_out["_matched"] = False
            unmatched_geo_codes.append(code)

        merged_rows.append(row_out)

    df_merged = pd.DataFrame(merged_rows)

    report = MatchReport(
        total_geo=len(geo_rows),
        matched_geo=len(matched_records),
        total_user_rows=len(df_user),
        matched_user_rows=matched_user_row_count,
        unmatched_user_keys=unmatched_user_keys,
        unmatched_geo_codes=unmatched_geo_codes
    )

    return df_merged, report
