import math
import unittest

import numpy as np

from swappy.model import CircuitRealization, SectorBasis, u1_gate


class ModelTests(unittest.TestCase):
    def test_gate_is_unitary_and_charge_conserving(self):
        gate = u1_gate(2.551, np.pi, 0.3, -1.1, 0.7)
        np.testing.assert_allclose(gate.conj().T @ gate, np.eye(4), atol=1e-12)
        charge = np.diag([-1.0, 0.0, 0.0, 1.0])
        np.testing.assert_allclose(gate @ charge, charge @ gate, atol=1e-12)

    def test_swap_line_has_only_off_diagonal_mixed_block(self):
        gate = u1_gate(np.pi, np.pi, 0.1, 0.2, -0.4)
        self.assertAlmostEqual(abs(gate[1, 1]), 0.0, places=12)
        self.assertAlmostEqual(abs(gate[2, 2]), 0.0, places=12)
        self.assertAlmostEqual(abs(gate[1, 2]), 1.0, places=12)
        self.assertAlmostEqual(abs(gate[2, 1]), 1.0, places=12)

    def test_sector_dimension_and_norm_conservation(self):
        basis = SectorBasis(8, 0.0)
        self.assertEqual(basis.dimension, math.comb(8, 4))
        rng = np.random.default_rng(7)
        state = basis.typical_initial_state(rng)
        circuit = CircuitRealization.sample(basis, 1.374, np.pi, rng)
        evolved = circuit.apply_cycle(basis, state)
        self.assertAlmostEqual(np.linalg.norm(evolved), 1.0, places=11)
        self.assertAlmostEqual(basis.magnetization_profile(evolved).sum(), 0.0, places=11)

    def test_bond_application_matches_dense_local_update(self):
        basis = SectorBasis(4, 0.0)
        rng = np.random.default_rng(11)
        state = rng.normal(size=basis.dimension) + 1j * rng.normal(size=basis.dimension)
        state /= np.linalg.norm(state)
        gate = u1_gate(0.9, 1.2, 0.2, -0.5, 0.8)
        result = basis.apply_gate(state, gate, 1)

        full = np.zeros(2**4, dtype=complex)
        full[basis.states] = state
        tensor = full.reshape(2, 2, 2, 2)
        expected = np.einsum("abij,xijy->xaby", gate.reshape(2, 2, 2, 2), tensor)
        expected = expected.reshape(-1)[basis.states]
        np.testing.assert_allclose(result, expected, atol=1e-12)


if __name__ == "__main__":
    unittest.main()

