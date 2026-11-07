"""
exemple_mrc.py
--------------
Exemple d'utilisation de qc_carto pour generer une carte
a l'echelle des 104 MRC et territoires equivalents du Quebec.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qc_carto import QuebecMap

def main():
    print("Generation de la carte des 104 MRC du Quebec...")

    qm = QuebecMap(level="mrc")
    data_path = os.path.join("data", "examples", "demo_mrc_quebec.csv")

    qm.set_data(
        data=data_path,
        key_col="code_mrc",
        value_col="vitalite_economique",
        extra_cols=["population", "densite_km2", "taux_activite_pct"]
    )

    qm.configure_style(
        title="Indice de vitalité économique par MRC au Québec",
        subtitle="Score composite sur une échelle de 1 à 10. Verts foncés = vitalité élevée.",
        source="Données Québec / MAMH",
        palette="Greens",
        reverse_palette=False,
        discretization="quantiles",
        n_bins=5,
        unit="pts",
        decimals=1,
        basemap="carto_positron"
    )

    out_file = "carte_mrc_vitalite.html"
    qm.save_html(out_file)
    print(f"Carte interactive MRC enregistree : {os.path.abspath(out_file)}")

if __name__ == "__main__":
    main()
