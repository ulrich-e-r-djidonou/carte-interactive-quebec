"""
app.py
------
Application web interactive Streamlit concue comme un Datawrapper quebecois :
permet de charger des donnees par region administrative, MRC ou ville,
d'apparier automatiquement les entites geographiques officielles,
de personnaliser la visualisation choroplethe et d'exporter la carte HTML autonome.
"""

import os
import io
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px

from qc_carto import QuebecMap, format_quebec_number, get_referentiel
from qc_carto.data_loader import LEVEL_LABELS
from qc_carto.palettes import PALETTES, format_quebec_number

# Configuration de la page
st.set_page_config(
    page_title="QC Carto : Cartographie interactive du Québec",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS epure et sobre
st.markdown("""
<style>
    .main-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1f2328;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #57606a;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #57606a;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1f2328;
    }
</style>
""", unsafe_allow_html=True)

# Repertoire de base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(BASE_DIR, "data", "examples")

# Titre principal
st.markdown("<div class='main-header'>QC Carto : Datawrapper pour le Québec</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-header'>Génération de cartes choroplèthes interactives par région administrative, MRC ou ville du Québec.</div>",
    unsafe_allow_html=True
)

# --- SIDEBAR : LE WORKFLOW DATAWRAPPER ---
st.sidebar.markdown("### 1. Échelle géographique")
level_options = {
    "region": "17 Régions administratives",
    "mrc": "104 MRC et équivalents",
    "ville": "231 Villes officielles",
    "municipalite": "1 289 Municipalités complètes"
}
selected_level = st.sidebar.selectbox(
    "Choisir l'échelle territoriale :",
    options=list(level_options.keys()),
    format_func=lambda x: level_options[x],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 2. Données")
data_source_mode = st.sidebar.radio(
    "Source des données :",
    options=["Exemple officiel intégré", "Téléverser un fichier (CSV / Excel)"],
    index=0
)

df_loaded = None
default_key_col = None

if data_source_mode == "Exemple officiel intégré":
    example_files = {
        "region": "demo_regions_quebec.csv",
        "mrc": "demo_mrc_quebec.csv",
        "ville": "demo_villes_quebec.csv",
        "municipalite": "demo_villes_quebec.csv"
    }
    ex_filename = example_files.get(selected_level, "demo_regions_quebec.csv")
    ex_path = os.path.join(EXAMPLES_DIR, ex_filename)
    if os.path.exists(ex_path):
        df_loaded = pd.read_csv(ex_path)
        st.sidebar.success(f"Données de démonstration chargées ({len(df_loaded)} lignes).")
    else:
        st.sidebar.error("Fichier de démonstration introuvable.")
else:
    uploaded_file = st.sidebar.file_uploader(
        "Déposer un fichier CSV ou Excel (.xlsx) :",
        type=["csv", "xlsx", "xls"]
    )
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_loaded = pd.read_csv(uploaded_file)
            else:
                df_loaded = pd.read_excel(uploaded_file)
            st.sidebar.success(f"Fichier chargé avec succès ({len(df_loaded)} lignes).")
        except Exception as e:
            st.sidebar.error(f"Erreur de lecture : {e}")

if df_loaded is None:
    st.info("Veuillez sélectionner ou téléverser un jeu de données dans le panneau latéral pour commencer.")
    st.stop()

# --- ETAPE 3 : SELECTION DES COLONNES ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 3. Variables")

columns = list(df_loaded.columns)

# Colonne cle geographique
from qc_carto.matcher import auto_detect_key_column
detected_key = auto_detect_key_column(df_loaded, level=selected_level)
key_index = columns.index(detected_key) if detected_key in columns else 0
key_col = st.sidebar.selectbox("Colonne géographique (code ou nom) :", options=columns, index=key_index)

# Colonne valeur numerique a cartographier
numeric_cols = [c for c in df_loaded.select_dtypes(include=["number"]).columns if c != key_col]
if not numeric_cols:
    st.sidebar.error("Aucune colonne numérique détectée dans votre tableau.")
    st.stop()

value_col = st.sidebar.selectbox("Variable à cartographier (couleur) :", options=numeric_cols, index=0)

# Colonnes d'infobulles supplementaires
remaining_cols = [c for c in columns if c not in [key_col, value_col]]
extra_cols = st.sidebar.multiselect(
    "Variables additionnelles dans l'infobulle :",
    options=remaining_cols,
    default=remaining_cols[:2] if len(remaining_cols) >= 2 else remaining_cols
)

# --- ETAPE 4 : STYLE & PALETTES DATAWRAPPER ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 4. Style cartographique")

available_palettes = [p for p in PALETTES.keys() if p != "Neutre"]
palette_choice = st.sidebar.selectbox("Palette de couleurs :", options=available_palettes, index=available_palettes.index("YlOrRd") if "YlOrRd" in available_palettes else 0)
reverse_pal = st.sidebar.checkbox("Inverser la palette (valeurs basses plus foncées)", value=False)

discretization_mode = st.sidebar.selectbox(
    "Méthode de discrétisation :",
    options=["quantiles", "equal", "continuous"],
    format_func=lambda x: {
        "quantiles": "Quantiles (répartition égale des entités)",
        "equal": "Intervalles réguliers (amplitudes égales)",
        "continuous": "Dégradé continu (linéaire)"
    }[x],
    index=0
)

n_bins = 5
if discretization_mode in ["quantiles", "equal"]:
    n_bins = st.sidebar.slider("Nombre de classes :", min_value=3, max_value=7, value=5)

unit_label = st.sidebar.text_input("Unité de mesure (ex: %, $, k$, hab.) :", value="%")
decimals = st.sidebar.slider("Nombre de décimales :", min_value=0, max_value=3, value=1)

basemap_choice = st.sidebar.selectbox(
    "Fond de carte :",
    options=["carto_positron", "carto_dark", "osm", "blanc"],
    format_func=lambda x: {
        "carto_positron": "Clair épuré (Datawrapper Positron)",
        "carto_dark": "Sombre (Dark Matter)",
        "osm": "OpenStreetMap standard",
        "blanc": "Neutre sans tuiles (Fond blanc)"
    }[x],
    index=0
)

# --- ETAPE 5 : METADONNEES ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 5. Titre et source")
map_title = st.sidebar.text_input("Titre de la carte :", value=f"{value_col} par {LEVEL_LABELS.get(selected_level, selected_level)}")
map_subtitle = st.sidebar.text_input("Sous-titre explicatif :", value="Données officielles comparatives à l'échelle québécoise.")
map_source = st.sidebar.text_input("Mention de source :", value="Institut de la statistique du Québec / Statistique Canada")

# --- CONSTRUCTION DU MODELE QUEBEC MAP ---
qm = QuebecMap(level=selected_level)
qm.set_data(data=df_loaded, key_col=key_col, value_col=value_col, extra_cols=extra_cols)
qm.configure_style(
    title=map_title,
    subtitle=map_subtitle,
    source=map_source,
    palette=palette_choice,
    reverse_palette=reverse_pal,
    discretization=discretization_mode,
    n_bins=n_bins,
    unit=unit_label,
    decimals=decimals,
    basemap=basemap_choice
)

report = qm.match_report

# --- ONGLETS PRINCIPAUX ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Carte interactive",
    "Données et appariement",
    "Distribution statistique",
    "Exporter et publier"
])

with tab1:
    # Rendu de la carte interactive Folium
    folium_map = qm.render_folium()
    map_html = folium_map.get_root().render()
    components.html(map_html, height=660, scrolling=False)

with tab2:
    st.markdown("#### Diagnostic de couverture territoriale")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Entités géographiques</div>
            <div class='metric-value'>{report.matched_geo} / {report.total_geo}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Taux de couverture</div>
            <div class='metric-value'>{report.coverage_rate} %</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Lignes utilisateurs appariées</div>
            <div class='metric-value'>{report.matched_user_rows} / {report.total_user_rows}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>Taux de reconnaissance</div>
            <div class='metric-value'>{report.user_match_rate} %</div>
        </div>
        """, unsafe_allow_html=True)

    if report.unmatched_user_keys:
        st.warning(f"Lignes du tableau non associées à un territoire officiel ({len(report.unmatched_user_keys)}) : {report.unmatched_user_keys[:10]}")

    st.markdown("#### Tableau complet des données géographiques")
    cols_to_show = ["code", "nom", value_col] + extra_cols + ["_matched"]
    st.dataframe(qm.df_merged[cols_to_show], use_container_width=True)

with tab3:
    st.markdown("#### Analyse de distribution de la variable cartographiée")
    vals = qm.df_merged[value_col].dropna().astype(float)
    if len(vals) > 0:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Moyenne", format_quebec_number(vals.mean(), decimals=decimals, unit=unit_label))
        col_m2.metric("Médiane", format_quebec_number(vals.median(), decimals=decimals, unit=unit_label))
        col_m3.metric("Minimum", format_quebec_number(vals.min(), decimals=decimals, unit=unit_label))
        col_m4.metric("Maximum", format_quebec_number(vals.max(), decimals=decimals, unit=unit_label))

        fig = px.histogram(
            qm.df_merged.dropna(subset=[value_col]),
            x=value_col,
            nbins=15,
            title=f"Distribution de : {value_col}",
            labels={value_col: f"{value_col} ({unit_label})", "count": "Nombre d'entités"},
            color_discrete_sequence=["#1f77b4"]
        )
        fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune valeur numérique disponible pour cette variable.")

with tab4:
    st.markdown("#### Options d'exportation prêtes à l'emploi")
    st.write("Téléchargez la carte interactive sous forme de fichier HTML autonome pour l'ouvrir hors ligne, la partager par courriel, ou copiez le code d'intégration iframe pour votre site ou intranet.")

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        st.markdown("##### 1. Fichier HTML 100 % autonome")
        st.write("Le fichier produit contient l'ensemble des polygones, styles, infobulles et scripts nécessaires. Il ne nécessite aucun serveur web pour fonctionner.")

        # Generer le HTML en memoire
        html_buffer = qm.render_folium().get_root().render()
        st.download_button(
            label="Télécharger la carte interactive (.html)",
            data=html_buffer.encode("utf-8"),
            file_name=f"carte_quebec_{selected_level}_{value_col}.html",
            mime="text/html"
        )

    with col_exp2:
        st.markdown("##### 2. Données enrichies (.csv)")
        st.write("Exportez la table de données combinant les codes officiels, noms, variables utilisateurs et classifications.")
        csv_buffer = qm.df_merged.to_csv(index=False, encoding="utf-8")
        st.download_button(
            label="Télécharger les données fusionnées (.csv)",
            data=csv_buffer.encode("utf-8"),
            file_name=f"donnees_quebec_{selected_level}_{value_col}.csv",
            mime="text/csv"
        )

    st.markdown("---")
    st.markdown("##### 3. Code d'intégration Web (iframe)")
    st.write("Copiez ce code pour intégrer la carte dans WordPress, Ghost, Notion, Power BI ou un portail web interne :")
    embed_snippet = qm.get_embed_code(height=650)
    st.code(embed_snippet, language="html")
