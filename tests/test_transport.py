import unittest

import numpy as np

from swappy.transport import (
    analyze_profiles,
    fit_power_law,
    quasi_probability,
    simulate_trajectory,
)


class TransportTests(unittest.TestCase):
    def test_quasi_probability_is_normalized(self):
        profile = np.array([[0.5, -1 / 6, -1 / 6, -1 / 6]])
        probability = quasi_probability(profile, total_magnetization=0.0)
        np.testing.assert_allclose(probability, [[1.0, 0.0, 0.0, 0.0]], atol=1e-12)
        np.testing.assert_allclose(probability.sum(axis=1), 1.0, atol=1e-12)

    def test_circular_mean_identifies_localized_profile(self):
        profile = np.array([[-1 / 6, -1 / 6, 0.5, -1 / 6]])
        result = analyze_profiles(profile, np.array([0.0]))
        self.assertAlmostEqual(abs(result.circular_mean[0]), 1.0, places=12)
        self.assertAlmostEqual(result.spread[0], 0.0, places=12)
        self.assertAlmostEqual(result.peak[0], 1.0, places=12)

    def test_seeded_simulation_is_reproducible(self):
        first = simulate_trajectory(6, 2.551, cycles=2, seed=123)
        second = simulate_trajectory(6, 2.551, cycles=2, seed=123)
        np.testing.assert_allclose(first.magnetization, second.magnetization)

    def test_paper_sampling_switches_to_cycles_after_100(self):
        result = simulate_trajectory(4, 1.374, cycles=103, seed=123, record="paper")
        self.assertEqual(len(result.times), 1 + 100 * 4 + 3)
        self.assertAlmostEqual(result.times[-1], 103.0)

    def test_power_law_fit(self):
        times = np.linspace(1, 20, 100)
        fit = fit_power_law(times, 3 * times**0.5, (2, 18))
        self.assertAlmostEqual(fit["exponent"], 0.5, places=10)
        self.assertAlmostEqual(fit["amplitude"], 3.0, places=10)


if __name__ == "__main__":
    unittest.main()
