"""
exemple_dataframe_personnalise.py
---------------------------------
Exemple demontrant comment injecter directement un DataFrame pandas
cree a la volee avec seulement quelques territoires : qc_carto gere
automatiquement la normalisation des noms, l'appariement et la mise
en valeur neutre des territoires sans donnees.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qc_carto import QuebecMap

def main():
    # Creer un tableau personnalise avec differents formats de noms et d'accents
    df_custom = pd.DataFrame([
        {"territoire": "Capitale-Nationale", "taux_diplomes": 42.5},
        {"territoire": "Montreal", "taux_diplomes": 46.1},        # Sans accent
        {"territoire": "Ville de Laval", "taux_diplomes": 34.8},   # Avec prefixe
        {"territoire": "Gaspesie", "taux_diplomes": 28.2},         # Alias
        {"territoire": "02", "taux_diplomes": 31.0},               # Code (Saguenay-Lac-Saint-Jean)
        {"territoire": "Estrie", "taux_diplomes": 36.4}
    ])

    print("Tableau d'entree personnalise :")
    print(df_custom)

    qm = QuebecMap(level="region")
    qm.set_data(
        data=df_custom,
        key_col="territoire",
        value_col="taux_diplomes"
    )

    print("\nRapport d'appariement :")
    print(qm.match_report.summary_text())

    qm.configure_style(
        title="Diplômés universitaires par région administrative",
        subtitle="Démonstration avec appariement souple et gestion des données partielles.",
        unit="%",
        palette="Teal"
    )

    out_file = "carte_donnees_personnalisees.html"
    qm.save_html(out_file)
    print(f"\nCarte generee avec succes : {os.path.abspath(out_file)}")

if __name__ == "__main__":
    main()
