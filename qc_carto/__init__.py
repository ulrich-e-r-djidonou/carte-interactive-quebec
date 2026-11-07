"""
qc_carto - Datawrapper pour la cartographie du Quebec en Python.

Module d'analyse spatiale et de generation de cartes choroplethes interactives
pour les regions administratives, les MRC et les villes/municipalites du Quebec.
"""

from .core import QuebecMap
from .matcher import match_data_to_geo, normalize_name
from .palettes import get_palette, format_quebec_number
from .data_loader import load_geojson, get_available_levels, get_referentiel

__version__ = "1.0.0"
__all__ = [
    "QuebecMap",
    "match_data_to_geo",
    "normalize_name",
    "get_palette",
    "format_quebec_number",
    "load_geojson",
    "get_available_levels",
    "get_referentiel"
]
