# Changelog

Toutes les modifications notables apportees a ce projet seront documentees dans ce fichier. Le format est base sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [1.0.0] - 2026-11-07

### Resume
Creation du systeme complet de cartographie interactive pour le Quebec (qc_carto) fonctionnant a la maniere de Datawrapper. Prise en charge des trois echelles administratives officielles : regions administratives, MRC et villes. Deploiement d'une application web interactive Streamlit et d'un package Python modulaire avec export HTML autonome et code d'integration iframe.

### Ajoute
- Module `qc_carto.data_loader` : chargement et mise en cache memoire des decoupages territoriaux officiels du Quebec.
- Module `qc_carto.matcher` : moteur d'appariement tolerant prenant en charge les codes officiels, les noms sans accents, les prefixes administratifs et les alias territoriaux.
- Module `qc_carto.palettes` : 14 palettes professionnelles style Datawrapper, classification par quantiles, amplitudes egales et continu, et formateur de nombres conforme a la norme quebecoise (espace pour les milliers, virgule decimale).
- Module `qc_carto.core` : classe `QuebecMap` permettant la creation, le stylage, le rendu Leaflet interactif, l'exportation HTML 100 % autonome et la generation de balises iframe responsives.
- Application web interactive `app.py` (Streamlit) : interface studio complete permettant de televerser ses donnees, d'apparier les territoires, de personnaliser les couleurs et d'exporter en un clic.
- Scripts de preparation spatiale (`scripts/prepare_geometries.py`) : telechargement, conversion et simplification topologique des shapefiles officiels MRNF / Donnees Quebec.
- Decoupages officiels generes en WGS84 sous `data/geojson/` :
  - 17 regions administratives (204 KB)
  - 104 MRC (482 KB)
  - 231 villes officielles (235 KB)
  - 1 289 municipalites completes (2.24 MB)
- Referentiel geographique tabulaire complet sous `data/references/referentiel_geographique_quebec.csv`.
- Jeux de donnees socio-economiques de demonstration sous `data/examples/` (regions, MRC, villes).
- Quatre scripts d'exemples programmatiques prets a l'emploi sous `examples/`.
- Suite de tests unitaires automatises sous `tests/test_qc_carto.py`.

### Modifie
- Configuration des tuiles CartoDB Positron pour utiliser les endpoints XYZ sans cle d'API obligatoire.
- Documentation `README.md` enrichie avec guide d'installation, commandes Streamlit et exemples de code Python.
