"""
exemple_regions.py
------------------
Exemple d'utilisation programmatique de qc_carto pour generer
une carte choroplethe interactive du Quebec a l'echelle des
17 regions administratives.
"""

import os
import sys

# Ajouter la racine du projet au chemin d'importation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qc_carto import QuebecMap

def main():
    print("Generation de la carte des 17 regions administratives du Quebec...")

    # 1. Initialiser le constructeur pour l'echelle 'region'
    qm = QuebecMap(level="region")

    # 2. Associer les donnees (CSV ou DataFrame)
    data_path = os.path.join("data", "examples", "demo_regions_quebec.csv")
    qm.set_data(
        data=data_path,
        key_col="code_region",
        value_col="taux_chomage",
        extra_cols=["population", "revenu_median", "croissance_demographique_pct"]
    )

    # 3. Configurer le style graphique et les textes
    qm.configure_style(
        title="Taux de chômage par région administrative au Québec",
        subtitle="Moyenne annuelle estimée (2026). Source : ISQ / StatCan.",
        source="Institut de la statistique du Québec",
        palette="YlOrRd",
        reverse_palette=False,
        discretization="quantiles",
        n_bins=5,
        unit="%",
        decimals=1,
        basemap="carto_positron"
    )

    # 4. Exporter la carte au format HTML autonome
    out_file = "carte_regions_chomage.html"
    qm.save_html(out_file)
    print(f"Carte interactive enregistree avec succes : {os.path.abspath(out_file)}")

    # 5. Afficher le code d'integration iframe
    print("\nCode d'integration iframe pret a l'emploi :")
    print(qm.get_embed_code())

if __name__ == "__main__":
    main()
