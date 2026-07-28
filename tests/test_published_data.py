import unittest

import numpy as np

from swappy.published_data import load_published_static_data
from swappy.spectral import charge_sector_page_entropy


class PublishedDataTests(unittest.TestCase):
    def test_page_entropy_is_positive(self):
        self.assertGreater(charge_sector_page_entropy(12, 6), 0)

    def test_legacy_angles_are_rescaled(self):
        entropy, gaps = load_published_static_data()
        self.assertGreater(entropy["J_paper"].max(), 3.0)
        self.assertGreater(gaps["J_paper"].max(), 3.0)
        self.assertGreater(gaps["Jz_paper"].nunique(), 10)
        self.assertTrue(np.isfinite(entropy["normalized_entanglement"]).all())


if __name__ == "__main__":
    unittest.main()
