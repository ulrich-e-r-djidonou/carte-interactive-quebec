"""
tests/test_qc_carto.py
----------------------
Suite de tests unitaires et d'integration pour qc_carto.
"""

import os
import sys
import unittest
import pandas as pd

# Ajouter la racine du projet au PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from qc_carto import QuebecMap, normalize_name, format_quebec_number, load_geojson
from qc_carto.matcher import match_data_to_geo, auto_detect_key_column
from qc_carto.palettes import assign_colors, compute_bins, get_palette


class TestDataLoading(unittest.TestCase):
    def test_load_regions(self):
        geo = load_geojson("region")
        self.assertEqual(geo["type"], "FeatureCollection")
        self.assertEqual(len(geo["features"]), 17)

    def test_load_mrc(self):
        geo = load_geojson("mrc")
        self.assertEqual(geo["type"], "FeatureCollection")
        self.assertEqual(len(geo["features"]), 104)

    def test_load_villes(self):
        geo = load_geojson("ville")
        self.assertEqual(geo["type"], "FeatureCollection")
        self.assertTrue(len(geo["features"]) >= 200)


class TestNormalizationAndMatching(unittest.TestCase):
    def test_normalize_name(self):
        self.assertEqual(normalize_name("Montréal"), "montreal")
        self.assertEqual(normalize_name("Ville de Québec"), "quebec")
        self.assertEqual(normalize_name("MRC de Memphrémagog"), "memphremagog")
        self.assertEqual(normalize_name("Gaspésie-Îles-de-la-Madeleine"), "gaspesie iles de la madeleine")

    def test_match_regions_by_name_and_code(self):
        test_df = pd.DataFrame([
            {"region": "Capitale-Nationale", "taux": 3.7},
            {"region": "montreal", "taux": 5.9},
            {"region": "01", "taux": 5.1},  # Bas-Saint-Laurent par code
            {"region": "Saguenay", "taux": 5.4}  # Alias
        ])
        df_merged, report = match_data_to_geo(test_df, key_col="region", level="region")
        self.assertEqual(report.total_geo, 17)
        self.assertEqual(report.matched_geo, 4)
        self.assertAlmostEqual(report.user_match_rate, 100.0)

    def test_auto_detect_key_col(self):
        df1 = pd.DataFrame({"code_region": ["01", "02"], "valeur": [10, 20]})
        self.assertEqual(auto_detect_key_column(df1, level="region"), "code_region")

        df2 = pd.DataFrame({"nom_mrc": ["Kativik", "Québec"], "densite": [0.1, 1200]})
        self.assertEqual(auto_detect_key_column(df2, level="mrc"), "nom_mrc")


class TestPalettesAndFormatting(unittest.TestCase):
    def test_format_quebec_number(self):
        self.assertEqual(format_quebec_number(1234567.89, decimals=1), "1 234 567,9")
        self.assertEqual(format_quebec_number(74800, decimals=0, unit="$"), "74 800 $")
        self.assertEqual(format_quebec_number(5.4, decimals=1, unit="%"), "5,4 %")
        self.assertEqual(format_quebec_number(None), "Non documenté")

    def test_assign_colors_quantiles(self):
        s = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        colors, bins, palette = assign_colors(s, palette_name="Blues", method="quantiles", n_bins=5)
        self.assertEqual(len(colors), 10)
        self.assertEqual(len(bins), 6)
        self.assertEqual(len(palette), 5)


class TestQuebecMapEndToEnd(unittest.TestCase):
    def test_region_map_export(self):
        sample_path = os.path.join(PROJECT_ROOT, "data", "examples", "demo_regions_quebec.csv")
        out_html = os.path.join(PROJECT_ROOT, "data", "cache", "test_carte_regions.html")

        qm = QuebecMap(level="region")
        qm.set_data(sample_path, key_col="code_region", value_col="taux_chomage")
        qm.configure_style(
            title="Taux de chômage par région administrative",
            unit="%",
            palette="YlOrRd"
        )

        saved = qm.save_html(out_html)
        self.assertTrue(os.path.exists(saved))
        self.assertGreater(os.path.getsize(saved), 50000)

        # Tester le code d'integration iframe
        embed = qm.get_embed_code()
        self.assertIn("<iframe", embed)
        self.assertIn("qc-map-region", embed)


if __name__ == "__main__":
    unittest.main()
