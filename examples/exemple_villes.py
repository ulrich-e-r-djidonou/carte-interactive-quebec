"""
exemple_villes.py
-----------------
Exemple d'utilisation de qc_carto pour cartographier
les 231 villes officielles du Quebec.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qc_carto import QuebecMap

def main():
    print("Generation de la carte des 231 villes officielles du Quebec...")

    qm = QuebecMap(level="ville")
    data_path = os.path.join("data", "examples", "demo_villes_quebec.csv")

    qm.set_data(
        data=data_path,
        key_col="code_ville",
        value_col="taux_proprietaires_pct",
        extra_cols=["population", "revenu_median", "age_median"]
    )

    qm.configure_style(
        title="Taux de ménages propriétaires par ville au Québec",
        subtitle="Proportion des logements occupés par leur propriétaire (%).",
        source="Statistique Canada / Profil du recensement",
        palette="Blues",
        reverse_palette=False,
        discretization="quantiles",
        n_bins=5,
        unit="%",
        decimals=1,
        basemap="carto_positron"
    )

    out_file = "carte_villes_proprietaires.html"
    qm.save_html(out_file)
    print(f"Carte interactive des villes enregistree : {os.path.abspath(out_file)}")

if __name__ == "__main__":
    main()
