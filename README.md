# carte-interactive-quebec

Systeme modulaire en Python concu comme un **Datawrapper quebecois** pour creer, personnaliser et diffuser des cartes choroplethes interactives selon les differents decoupages territoriaux officiels du Quebec : **regions administratives**, **MRC (et territoires equivalents)** et **villes / municipalites locales**.

Permet d'associer directement n'importe quel tableau de donnees (CSV, Excel ou DataFrame pandas), d'effectuer un appariement automatique et tolerant (codes officiels, noms avec ou sans accents, alias courants), d'appliquer des palettes professionnelles continues ou par quantiles, et d'exporter des visualisations interactives 100 % autonomes en HTML ou d'utiliser une interface web interactive dediee.

---

## Fonctionnalites cles

1. **Multi-echelles officielles du Quebec**
   - **17 regions administratives** (01 Bas-Saint-Laurent a 17 Centre-du-Quebec).
   - **104 MRC** et municipalites regionales de comte ou territoires equivalents.
   - **231 villes officielles** (villes a statut legal au sens du MAMH).
   - **1 289 municipalites locales** (repertoire complet du Quebec).

2. **Flux de travail style Datawrapper**
   - Etape 1 : Choix de l'echelle territoriale.
   - Etape 2 : Chargement des donnees (televersement CSV/Excel ou exemples officiels ISQ/StatCan).
   - Etape 3 : Appariement intelligent des territoires (reconnaissance par code ou par nom avec elimination automatique des prefixes "Ville de", "MRC de", insensibilite aux accents et gestion des alias).
   - Etape 4 : Personnalisation visuelle (palettes sequentielles et divergentes, classification par quantiles ou amplitudes egales, inversion de la palette, formatage des nombres avec separateur de milliers et virgule decimale quebecoise, infobulles enrichies).
   - Etape 5 : Exportation immediate en HTML autonome (hors ligne), en code iframe responsive ou en table de donnees enrichie.

3. **Double mode d'utilisation**
   - **Interface graphique web (Streamlit)** : interface sans code complete type Datawrapper (`streamlit run app.py`).
   - **Bibliotheque Python (qc_carto)** : classe orientee objet `QuebecMap` pour les analyses automatisees, les rapports reproductibles ou les chaines de traitement de donnees.

---

## Installation

Cloner le depot et installer les dependances requises :

```bash
git clone https://github.com/ulrich-e-r-djidonou/carte-interactive-quebec.git
cd carte-interactive-quebec
pip install -r requirements.txt
```

---

## Lancer l'application web interactive (Streamlit)

Pour lancer le studio cartographique interactif localement :

```bash
streamlit run app.py
```

L'application s'ouvre automatiquement dans votre navigateur par defaut (generalement sur `http://localhost:8501`). Vous pouvez y tester les jeux d'exemples officiels ou glisser-deposer vos propres fichiers Excel ou CSV.

---

## Utilisation programmatique en Python

### 1. Carte des 17 regions administratives

```python
from qc_carto import QuebecMap

# Initialisation
qm = QuebecMap(level="region")

# Chargement des donnees (chemin CSV ou DataFrame pandas)
qm.set_data(
    data="data/examples/demo_regions_quebec.csv",
    key_col="code_region",
    value_col="taux_chomage",
    extra_cols=["population", "revenu_median"]
)

# Configuration du style
qm.configure_style(
    title="Taux de chomage par region administrative au Quebec",
    subtitle="Estimation annuelle (2026). Source : ISQ / StatCan.",
    source="Institut de la statistique du Quebec",
    palette="YlOrRd",
    discretization="quantiles",
    n_bins=5,
    unit="%",
    decimals=1,
    basemap="carto_positron"
)

# Exportation HTML autonome
qm.save_html("carte_regions.html")

# Recuperation du code d'integration iframe pour site web ou CMS
print(qm.get_embed_code())
```

### 2. Carte des 104 MRC

```python
from qc_carto import QuebecMap

qm = QuebecMap(level="mrc")
qm.set_data(
    data="data/examples/demo_mrc_quebec.csv",
    key_col="code_mrc",
    value_col="vitalite_economique"
)
qm.configure_style(
    title="Indice de vitalite economique par MRC",
    palette="Greens",
    unit="pts"
)
qm.save_html("carte_mrc.html")
```

### 3. Carte avec DataFrame cree a la volee et noms tolerants

```python
import pandas as pd
from qc_carto import QuebecMap

# Noms avec ecritures variees (avec/sans accents, avec "Ville de", code)
df = pd.DataFrame([
    {"territoire": "Capitale-Nationale", "taux": 42.5},
    {"territoire": "Montreal", "taux": 46.1},        # Sans accent
    {"territoire": "Ville de Laval", "taux": 34.8},   # Avec prefixe
    {"territoire": "Gaspesie", "taux": 28.2},         # Alias
    {"territoire": "02", "taux": 31.0}                # Code
])

qm = QuebecMap(level="region")
qm.set_data(data=df, key_col="territoire", value_col="taux")
print(qm.match_report.summary_text())
qm.save_html("carte_personnalisee.html")
```

---

## Structure du projet

```
carte-interactive-quebec/
|-- app.py                     # Application web interactive Streamlit (Datawrapper local)
|-- qc_carto/                  # Moteur cartographique modulaire
|   |-- core.py                # Classe principale QuebecMap
|   |-- matcher.py             # Moteur d'appariement tolerant (codes, noms, alias)
|   |-- palettes.py            # Palettes Datawrapper et classification statistique
|   |-- data_loader.py         # Chargeur des decoupages officiels et referentiel
|-- data/
|   |-- geojson/               # Decoupages officiels WGS84 optimises (regions, mrc, villes)
|   |-- references/            # Referentiel geographique tabulaire complet (CSV)
|   |-- examples/              # Jeux de donnees socio-economiques de demonstration
|-- examples/                  # Scripts Python complets et autonomes
|-- tests/                     # Suite de tests unitaires automatises
|-- scripts/                   # Scripts de preparation des geometries et de demo
|-- CHANGELOG.md               # Historique des modifications (Keep a Changelog)
`-- requirements.txt           # Dependances logicielles
```

---

## Sources des donnees officielles

- **Decoupages territoriaux** : Ministere des Ressources naturelles et des Forets (MRNF) et Ministere des Affaires municipales et de l'Habitation (MAMH), via Donnees Quebec (Licence Creative Commons Attribution CC-BY 4.0).
- **Projections et normes** : Geometries converties en coordonnees mondiales WGS84 (EPSG:4326) avec simplification topologique controlee pour un chargement web ultra-fluide.
