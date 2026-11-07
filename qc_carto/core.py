"""
qc_carto.core
-------------
Classe principale QuebecMap : constructeur cartographique interactif style Datawrapper
specialise pour les echelles territoriales du Quebec.
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import folium
from folium import plugins
import branca.colormap as cm

from .data_loader import load_geojson, LEVEL_LABELS
from .matcher import match_data_to_geo, auto_detect_key_column, MatchReport
from .palettes import assign_colors, format_quebec_number, get_palette, compute_bins


# Emplacements et zooms par defaut selon l'echelle
DEFAULT_VIEWPORTS = {
    "region": {"center": [52.2, -70.5], "zoom": 5},
    "mrc": {"center": [49.5, -71.5], "zoom": 6},
    "ville": {"center": [46.8, -72.0], "zoom": 7},
    "municipalite": {"center": [48.0, -71.5], "zoom": 6}
}

BASEMAP_TILES = {
    "carto_positron": {
        "tiles": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        "subdomains": "abcd"
    },
    "carto_dark": {
        "tiles": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        "subdomains": "abcd"
    },
    "osm": {
        "tiles": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
        "subdomains": "abc"
    },
    "blanc": {
        "tiles": None,
        "attr": ""
    }
}


class QuebecMap:
    """
    Constructeur de cartes choroplethes interactives pour le Quebec,
    concue selon les standards de clarte, de rigueur et d'elegance de Datawrapper.
    """

    def __init__(self, level: str = "region"):
        """
        Initialise la carte pour une echelle donnee :
        - 'region' : 17 regions administratives
        - 'mrc' : 104 MRC et territoires equivalents
        - 'ville' : 231 villes officielles
        - 'municipalite' : 1 289 municipalites locales
        """
        level = level.lower().strip()
        if level not in LEVEL_LABELS:
            raise ValueError(f"Echelle invalide : '{level}'. Choix : {list(LEVEL_LABELS.keys())}")

        self.level = level
        self.geojson = load_geojson(level)
        self.df_user: Optional[pd.DataFrame] = None
        self.df_merged: Optional[pd.DataFrame] = None
        self.match_report: Optional[MatchReport] = None

        self.key_col: Optional[str] = None
        self.value_col: Optional[str] = None
        self.extra_cols: List[str] = []

        # Configuration du style
        self.title: str = f"Carte du Québec par {self.level}"
        self.subtitle: str = ""
        self.source: str = "Données Québec / Gouvernement du Québec"
        self.palette_name: str = "Blues"
        self.reverse_palette: bool = False
        self.discretization: str = "quantiles"
        self.n_bins: int = 5
        self.custom_bins: Optional[List[float]] = None
        self.unit: str = ""
        self.decimals: int = 1
        self.nan_color: str = "#E0E0E0"
        self.basemap: str = "carto_positron"
        self.show_search: bool = True
        self.center: Optional[List[float]] = None
        self.zoom: Optional[int] = None

    def set_data(
        self,
        data: Union[pd.DataFrame, str],
        key_col: Optional[str] = None,
        value_col: Optional[str] = None,
        extra_cols: Optional[List[str]] = None
    ) -> "QuebecMap":
        """
        Charge et apparie un jeu de donnees (DataFrame, chemin CSV ou Excel).
        Detecte automatiquement la colonne d'identification si key_col est omis.
        """
        if isinstance(data, str):
            if data.endswith(".csv"):
                df = pd.read_csv(data)
            elif data.endswith((".xls", ".xlsx")):
                df = pd.read_excel(data)
            else:
                raise ValueError(f"Format de fichier non pris en charge : {data}")
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise TypeError("data doit etre un DataFrame pandas ou un chemin vers un fichier CSV/Excel.")

        if key_col is None:
            detected = auto_detect_key_column(df, level=self.level)
            if detected is None:
                raise ValueError("Impossible de detecter automatiquement la colonne geographique. Specifiez 'key_col'.")
            key_col = detected

        self.key_col = key_col

        # Detecter value_col si non fourni
        if value_col is None:
            numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c != key_col]
            if numeric_cols:
                value_col = numeric_cols[0]
            else:
                raise ValueError("Aucune colonne numerique detectee pour la coloration de la carte. Specifiez 'value_col'.")

        self.value_col = value_col
        self.extra_cols = extra_cols or []

        # Realiser l'appariement officiel
        self.df_user = df
        self.df_merged, self.match_report = match_data_to_geo(
            df=df,
            key_col=self.key_col,
            level=self.level,
            value_col=self.value_col
        )

        return self

    def configure_style(
        self,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        source: Optional[str] = None,
        palette: Optional[str] = None,
        reverse_palette: Optional[bool] = None,
        discretization: Optional[str] = None,
        n_bins: Optional[int] = None,
        custom_bins: Optional[List[float]] = None,
        unit: Optional[str] = None,
        decimals: Optional[int] = None,
        nan_color: Optional[str] = None,
        basemap: Optional[str] = None,
        center: Optional[List[float]] = None,
        zoom: Optional[int] = None,
        show_search: Optional[bool] = None
    ) -> "QuebecMap":
        """Configure les parametres graphiques et textuels de la carte."""
        if title is not None:
            self.title = title
        if subtitle is not None:
            self.subtitle = subtitle
        if source is not None:
            self.source = source
        if palette is not None:
            self.palette_name = palette
        if reverse_palette is not None:
            self.reverse_palette = reverse_palette
        if discretization is not None:
            self.discretization = discretization
        if n_bins is not None:
            self.n_bins = n_bins
        if custom_bins is not None:
            self.custom_bins = custom_bins
        if unit is not None:
            self.unit = unit
        if decimals is not None:
            self.decimals = decimals
        if nan_color is not None:
            self.nan_color = nan_color
        if basemap is not None:
            self.basemap = basemap
        if center is not None:
            self.center = center
        if zoom is not None:
            self.zoom = zoom
        if show_search is not None:
            self.show_search = show_search

        return self

    def render_folium(self) -> folium.Map:
        """
        Construit et retourne une carte Leaflet/Folium interactive
        prete pour l'affichage ou l'exportation autonome.
        """
        if self.df_merged is None or self.value_col is None:
            raise RuntimeError("Veuillez d'abord apparier des donnees avec 'set_data()'.")

        vp = DEFAULT_VIEWPORTS.get(self.level, DEFAULT_VIEWPORTS["region"])
        center = self.center or vp["center"]
        zoom = self.zoom or vp["zoom"]

        bm = BASEMAP_TILES.get(self.basemap, BASEMAP_TILES["carto_positron"])

        if bm["tiles"] is not None:
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                tiles=bm["tiles"],
                attr=bm["attr"],
                subdomains=bm.get("subdomains", "abc"),
                control_scale=True,
                prefer_canvas=True
            )
        else:
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                tiles=None,
                control_scale=True,
                prefer_canvas=True
            )

        # Calcul des couleurs et des intervalles
        series_vals = self.df_merged[self.value_col]
        colors_assigned, bins, palette_colors = assign_colors(
            values=series_vals,
            palette_name=self.palette_name,
            method=self.discretization,
            n_bins=self.n_bins,
            custom_bins=self.custom_bins,
            reverse=self.reverse_palette,
            nan_color=self.nan_color
        )

        self.df_merged["_color"] = colors_assigned

        # Indexer les valeurs et couleurs par code officiel
        code_to_data = {}
        for _, r in self.df_merged.iterrows():
            code_to_data[str(r["code"]).strip()] = r

        # Enrichir le GeoJSON avec les valeurs formatees pour les infobulles
        geojson_to_render = json.loads(json.dumps(self.geojson))

        for feat in geojson_to_render["features"]:
            c = str(feat["properties"]["code"]).strip()
            row = code_to_data.get(c)
            if row is not None and pd.notna(row.get(self.value_col)):
                raw_val = row[self.value_col]
                formatted_val = format_quebec_number(raw_val, decimals=self.decimals, unit=self.unit)
                feat["properties"]["_val_raw"] = float(raw_val)
                feat["properties"]["_val_str"] = formatted_val
                feat["properties"]["_fill_color"] = row["_color"]
                feat["properties"]["_has_data"] = True
            else:
                feat["properties"]["_val_raw"] = None
                feat["properties"]["_val_str"] = "Donnée non disponible"
                feat["properties"]["_fill_color"] = self.nan_color
                feat["properties"]["_has_data"] = False

            # Ajouter colonnes d'infobulle
            extra_lines = []
            if row is not None:
                for ec in self.extra_cols:
                    if ec in row and pd.notna(row[ec]):
                        val_ec = format_quebec_number(row[ec], decimals=1)
                        extra_lines.append(f"<b>{ec} :</b> {val_ec}")
            feat["properties"]["_extra_info"] = "<br>".join(extra_lines)

        # Couche GeoJSON avec infobulles Datawrapper et surbrillance au survol
        style_function = lambda f: {
            "fillColor": f["properties"].get("_fill_color", self.nan_color),
            "color": "#ffffff",
            "weight": 1.2 if self.level in ["region", "mrc"] else 0.8,
            "fillOpacity": 0.82,
            "dashArray": ""
        }

        highlight_function = lambda f: {
            "weight": 2.5,
            "color": "#111111",
            "fillOpacity": 0.95
        }

        # Infobulle fluide Leaflet (Tooltip)
        tooltip = folium.GeoJsonTooltip(
            fields=["label", "_val_str"],
            aliases=["Territoire :", f"{self.value_col} :"],
            style=(
                "background-color: #ffffff; "
                "border: 1px solid #d0d7de; "
                "border-radius: 4px; "
                "box-shadow: 0 4px 12px rgba(0,0,0,0.15); "
                "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; "
                "font-size: 13px; "
                "padding: 8px 12px; "
                "color: #1f2328;"
            ),
            localize=True
        )

        # Popup au clic avec contenu etaille
        popup = folium.GeoJsonPopup(
            fields=["label", "_val_str", "_extra_info"],
            aliases=["", "Valeur :", ""],
            labels=True,
            style="font-family: sans-serif; font-size: 13px;"
        )

        geojson_layer = folium.GeoJson(
            geojson_to_render,
            name=LEVEL_LABELS.get(self.level, self.level),
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=tooltip,
            popup=popup
        )
        geojson_layer.add_to(m)

        # Recherche textuelle si demandee
        if self.show_search:
            plugins.Search(
                layer=geojson_layer,
                geom_type="Polygon",
                placeholder="Rechercher un territoire du Québec...",
                collapsed=True,
                search_label="label",
                search_zoom=8 if self.level == "region" else 10
            ).add_to(m)

        # Injection de l'en-tete Datawrapper (Titre, sous-titre) et de la legende en HTML/CSS pur
        legend_html = self._build_datawrapper_legend_html(bins, palette_colors)
        m.get_root().html.add_child(folium.Element(legend_html))

        # Ajout du controle plein ecran
        plugins.Fullscreen(position="topleft").add_to(m)

        return m

    def _build_datawrapper_legend_html(self, bins: List[float], palette_colors: List[str]) -> str:
        """Construit le bloc de legende et le cartouche de titre selon le design Datawrapper."""
        title_esc = self.title.replace('"', '&quot;')
        subtitle_esc = self.subtitle.replace('"', '&quot;')
        source_esc = self.source.replace('"', '&quot;')
        unit_str = f" ({self.unit})" if self.unit else ""

        # Construire les elements de legende
        legend_items_html = []
        if self.discretization == "continuous":
            # Barre continue de degrade
            grad_colors = ", ".join(palette_colors)
            min_fmt = format_quebec_number(bins[0], decimals=self.decimals, unit=self.unit)
            max_fmt = format_quebec_number(bins[-1], decimals=self.decimals, unit=self.unit)
            legend_items_html.append(f"""
            <div style="margin-top: 6px;">
                <div style="height: 12px; width: 100%; background: linear-gradient(to right, {grad_colors}); border-radius: 2px;"></div>
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #57606a; margin-top: 4px;">
                    <span>{min_fmt}</span>
                    <span>{max_fmt}</span>
                </div>
            </div>
            """)
        else:
            # Paves discrets
            legend_items_html.append('<div style="display: flex; flex-direction: column; gap: 4px; margin-top: 6px;">')
            for idx in range(len(bins) - 1):
                col = palette_colors[min(idx, len(palette_colors) - 1)]
                low_fmt = format_quebec_number(bins[idx], decimals=self.decimals)
                high_fmt = format_quebec_number(bins[idx + 1], decimals=self.decimals)
                label = f"{low_fmt} à {high_fmt} {self.unit}".strip()
                legend_items_html.append(f"""
                <div style="display: flex; align-items: center; gap: 6px; font-size: 11px; color: #24292f;">
                    <span style="display: inline-block; width: 16px; height: 12px; background-color: {col}; border-radius: 2px; border: 1px solid rgba(0,0,0,0.15);"></span>
                    <span>{label}</span>
                </div>
                """)

            # Entree donnee non disponible
            legend_items_html.append(f"""
            <div style="display: flex; align-items: center; gap: 6px; font-size: 11px; color: #6e7781; margin-top: 4px; border-top: 1px solid #eaeef2; padding-top: 4px;">
                <span style="display: inline-block; width: 16px; height: 12px; background-color: {self.nan_color}; border-radius: 2px; border: 1px solid rgba(0,0,0,0.15);"></span>
                <span>Donnée non disponible</span>
            </div>
            """)
            legend_items_html.append("</div>")

        items_rendered = "\n".join(legend_items_html)

        html = f"""
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(4px);
            padding: 14px 18px;
            border-radius: 6px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            max-width: 320px;
            border: 1px solid #d0d7de;
        ">
            <div style="font-size: 15px; font-weight: 700; color: #1f2328; line-height: 1.25; margin-bottom: 4px;">
                {title_esc}
            </div>
            {f'<div style="font-size: 12px; color: #57606a; margin-bottom: 8px; line-height: 1.35;">{subtitle_esc}</div>' if subtitle_esc else ''}
            
            <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #57606a; margin-top: 6px;">
                {self.value_col}{unit_str}
            </div>
            
            {items_rendered}
            
            <div style="font-size: 10px; color: #8c959f; margin-top: 10px; border-top: 1px solid #eaeef2; padding-top: 6px; line-height: 1.3;">
                Source : {source_esc}
            </div>
        </div>
        """
        return html

    def save_html(self, filepath: str) -> str:
        """
        Exporte la carte interactive sous forme d'un fichier HTML 100 % autonome,
        qui peut etre ouvert directement dans n'importe quel navigateur web
        ou heberge sur un serveur / GitHub Pages.
        """
        m = self.render_folium()
        abs_path = os.path.abspath(filepath)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        m.save(abs_path)
        return abs_path

    def get_embed_code(self, iframe_id: Optional[str] = None, height: int = 650) -> str:
        """
        Retourne le code HTML d'integration responsive iframe style Datawrapper,
        pret a copier-coller dans un site, un blogue, un intranet ou un document web.
        """
        id_str = iframe_id or f"qc-map-{self.level}"
        code = f"""<iframe
    id="{id_str}"
    title="{self.title}"
    aria-label="Carte interactive du Québec"
    src="carte.html"
    scrolling="no"
    frameborder="0"
    style="width: 100%; min-width: 100% !important; border: none; height: {height}px; border-radius: 6px;"
></iframe>"""
        return code

    def export_data(self, filepath: str) -> str:
        """Exporte le tableau des donnees appariees et enrichies en CSV ou Excel."""
        if self.df_merged is None:
            raise RuntimeError("Aucune donnee appariee a exporter.")
        abs_path = os.path.abspath(filepath)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if filepath.endswith(".xlsx"):
            self.df_merged.to_excel(abs_path, index=False)
        else:
            self.df_merged.to_csv(abs_path, index=False, encoding="utf-8")
        return abs_path
