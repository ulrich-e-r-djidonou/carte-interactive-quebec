"""
qc_carto.palettes
-----------------
Palettes de couleurs style Datawrapper, methodes de discretisation statistique
et formateurs de nombres conformes aux normes quebecoises.
"""

from typing import List, Tuple, Union, Optional, Any
import numpy as np
import pandas as pd


# Palettes de couleurs inspirees des standards Datawrapper & ColorBrewer
PALETTES = {
    # Sequentielles
    "Blues": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#084594"],
    "Greens": ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#005a32"],
    "Oranges": ["#fff5eb", "#fee6ce", "#fdd0a2", "#fdae6b", "#fd8d3c", "#f16913", "#d94801", "#8c2d04"],
    "Reds": ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#99000d"],
    "Purples": ["#fcfbfd", "#efedf5", "#dadaeb", "#bcbddc", "#9e9ac8", "#807dba", "#6a51a3", "#4a1486"],
    "YlOrRd": ["#ffffcc", "#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#b10026"],
    "YlGnBu": ["#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#0c2c84"],
    "Teal": ["#e0f3f8", "#ccece6", "#99d8c9", "#66c2a4", "#41ae76", "#238b45", "#005824"],
    "Viridis": ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"],
    "Plasma": ["#0d0887", "#46039f", "#7201a8", "#9c179e", "#bd3786", "#d8576b", "#ed7953", "#fb9f3a", "#fdca26", "#f0f921"],
    "Sunset": ["#f3e79b", "#fac484", "#eb7f86", "#ce6693", "#a85d9b", "#5c53a5"],
    
    # Divergentes
    "RdBu": ["#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#f7f7f7", "#d1e5f0", "#92c5de", "#4393c3", "#2166ac"],
    "RdYlGn": ["#d73027", "#f46d43", "#fdae61", "#fee08b", "#ffffbf", "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850"],
    "Spectral": ["#9e0142", "#d53e4f", "#f46d43", "#fdae61", "#fee08b", "#ffffbf", "#e6f598", "#abdda4", "#66c2a5", "#3288bd", "#5e4fa2"],
    
    # Neutre / Donnee manquante
    "Neutre": ["#E0E0E0"]
}


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    hex_str = hex_str.lstrip("#")
    return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return f"#{int(np.clip(rgb[0], 0, 255)):02x}{int(np.clip(rgb[1], 0, 255)):02x}{int(np.clip(rgb[2], 0, 255)):02x}"


def interpolate_color(c1_hex: str, c2_hex: str, factor: float) -> str:
    """Interpole lineairement entre deux couleurs hex."""
    factor = max(0.0, min(1.0, factor))
    r1, g1, b1 = hex_to_rgb(c1_hex)
    r2, g2, b2 = hex_to_rgb(c2_hex)
    r = r1 + (r2 - r1) * factor
    g = g1 + (g2 - g1) * factor
    b = b1 + (b2 - b1) * factor
    return rgb_to_hex((r, g, b))


def get_palette(name: str = "Blues", reverse: bool = False, n_colors: Optional[int] = None) -> List[str]:
    """
    Retourne la liste des couleurs hex de la palette demandee,
    avec possibilite d'inversion et de re-echantillonnage a n_colors.
    """
    colors = PALETTES.get(name, PALETTES["Blues"]).copy()
    if reverse:
        colors = list(reversed(colors))

    if n_colors is not None and n_colors != len(colors):
        # Re-echantillonner lineairement
        if n_colors <= 1:
            return [colors[-1]]
        sampled = []
        for i in range(n_colors):
            pos = i / (n_colors - 1) * (len(colors) - 1)
            idx = int(pos)
            remainder = pos - idx
            if idx >= len(colors) - 1:
                sampled.append(colors[-1])
            else:
                sampled.append(interpolate_color(colors[idx], colors[idx + 1], remainder))
        return sampled

    return colors


def compute_bins(
    values: pd.Series,
    method: str = "quantiles",
    n_bins: int = 5,
    custom_bins: Optional[List[float]] = None
) -> List[float]:
    """
    Calcule les bornes d'intervalles statistiques pour la choroplethe :
    - 'quantiles' : quantiles ou percentiles reguliers
    - 'equal' : intervalles egaux entre min et max
    - 'continuous' : deux bornes simples [min, max]
    - 'custom' : bornes fournies par l'utilisateur
    """
    clean_vals = values.dropna().astype(float)
    if len(clean_vals) == 0:
        return [0.0, 1.0]

    v_min = float(clean_vals.min())
    v_max = float(clean_vals.max())

    if v_min == v_max:
        return [v_min - 1.0, v_max + 1.0]

    if custom_bins and len(custom_bins) >= 2:
        return sorted(list(dict.fromkeys(custom_bins)))

    if method == "continuous":
        return [v_min, v_max]

    if method == "equal":
        return list(np.linspace(v_min, v_max, n_bins + 1))

    # Par defaut : quantiles
    q_points = np.linspace(0, 1, n_bins + 1)
    bins = list(np.quantile(clean_vals, q_points))
    # S'assurer de l'unicite stricte des bornes en cas de valeurs repetees
    unique_bins = [bins[0]]
    for b in bins[1:]:
        if b > unique_bins[-1]:
            unique_bins.append(b)
        else:
            unique_bins.append(unique_bins[-1] + 1e-4)
    return unique_bins


def assign_colors(
    values: pd.Series,
    palette_name: str = "Blues",
    method: str = "quantiles",
    n_bins: int = 5,
    custom_bins: Optional[List[float]] = None,
    reverse: bool = False,
    nan_color: str = "#E0E0E0"
) -> Tuple[List[str], List[float], List[str]]:
    """
    Assigne a chaque valeur une couleur hex selon la methode choisie.
    Retourne :
    - colors_assigned : liste des couleurs correspondant a chaque ligne
    - bins : les seuils utilises
    - bin_colors : la palette hex par intervalle
    """
    clean_series = pd.to_numeric(values, errors="coerce")
    bins = compute_bins(clean_series, method=method, n_bins=n_bins, custom_bins=custom_bins)

    if method == "continuous":
        palette = get_palette(palette_name, reverse=reverse, n_colors=10)
        v_min, v_max = bins[0], bins[-1]
        denom = v_max - v_min if v_max > v_min else 1.0

        colors_out = []
        for v in clean_series:
            if pd.isna(v):
                colors_out.append(nan_color)
            else:
                ratio = (float(v) - v_min) / denom
                idx = ratio * (len(palette) - 1)
                i_base = int(idx)
                rem = idx - i_base
                if i_base >= len(palette) - 1:
                    colors_out.append(palette[-1])
                else:
                    colors_out.append(interpolate_color(palette[i_base], palette[i_base + 1], rem))
        return colors_out, bins, palette

    # Discret (quantiles, equal, custom)
    effective_n_bins = max(1, len(bins) - 1)
    bin_colors = get_palette(palette_name, reverse=reverse, n_colors=effective_n_bins)

    colors_out = []
    for v in clean_series:
        if pd.isna(v):
            colors_out.append(nan_color)
            continue
        v_flt = float(v)
        # Trouver l'intervalle
        assigned = bin_colors[-1]
        for b_idx in range(len(bins) - 1):
            low = bins[b_idx]
            high = bins[b_idx + 1]
            if b_idx == len(bins) - 2:
                if low <= v_flt <= high:
                    assigned = bin_colors[b_idx]
                    break
            else:
                if low <= v_flt < high:
                    assigned = bin_colors[b_idx]
                    break
        colors_out.append(assigned)

    return colors_out, bins, bin_colors


def format_quebec_number(
    val: Any,
    decimals: int = 1,
    unit: str = "",
    prefix: str = ""
) -> str:
    """
    Formate un nombre selon la norme quebecoise et francophone :
    espace insecable comme separateur de milliers et virgule decimale.
    Exemples :
    - 1234567.8 -> "1 234 567,8"
    - val=74800, unit="$" -> "74 800 $"
    - val=5.4, unit="%" -> "5,4 %"
    """
    if pd.isna(val) or val is None:
        return "Non documenté"

    try:
        f = float(val)
    except (ValueError, TypeError):
        return str(val)

    # Format avec virgule
    if decimals == 0:
        s = f"{int(round(f)):,}".replace(",", " ")
    else:
        fmt = f"{{:,.{decimals}f}}"
        s = fmt.format(f).replace(",", " ").replace(".", ",")

    parts = []
    if prefix:
        parts.append(prefix.strip())
    parts.append(s)
    if unit:
        parts.append(unit.strip())

    return " ".join(parts)
