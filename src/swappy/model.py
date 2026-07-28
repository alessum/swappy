"""The disordered U(1)-symmetric Floquet circuit used in the paper.

The implementation deliberately favors transparent, testable NumPy over the
machine-specific lookup-file workflow in the legacy scripts.  It works
directly in a fixed-magnetization sector and never constructs the full
Floquet matrix for dynamical simulations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from itertools import combinations
from math import comb

import numpy as np
from numpy.typing import NDArray


REGIMES = {
    "localized": 0.395,
    "ergodic": 1.374,
    "swappy": 2.551,
    "near_swap": 3.138,
}


ComplexArray = NDArray[np.complex128]
FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def u1_gate(J: float, Jz: float, h_left: float, h_right: float, phi: float) -> ComplexArray:
    """Return the paper's most-general disordered U(1)-symmetric two-site gate.

    The local basis is ``|↓↓>, |↓↑>, |↑↓>, |↑↑>`` (bit ``1`` means spin up).
    ``J`` and ``Jz`` use the published convention, so ``J = pi`` is the
    generalized-SWAP line.  The closed-form entries match the numerical gate
    used for the published spin-profile simulations.
    """

    c = np.cos(0.5 * J)
    s = np.sin(0.5 * J)
    common_mixed = np.exp(0.25j * Jz)

    gate = np.zeros((4, 4), dtype=np.complex128)
    gate[0, 0] = np.exp(1j * (-0.25 * Jz + 0.5 * h_left + 0.5 * h_right))
    gate[3, 3] = np.exp(1j * (-0.25 * Jz - 0.5 * h_left - 0.5 * h_right))
    gate[1, 1] = c * common_mixed * np.exp(0.5j * (h_left - h_right))
    gate[2, 2] = c * common_mixed * np.exp(-0.5j * (h_left - h_right))
    gate[1, 2] = -1j * s * common_mixed * np.exp(0.5j * (h_left - h_right) + 1j * phi)
    gate[2, 1] = -1j * s * common_mixed * np.exp(-0.5j * (h_left - h_right) - 1j * phi)
    return gate


@dataclass
class SectorBasis:
    """Computational basis and gate lookup tables for one charge sector."""

    n_sites: int
    magnetization: float = 0.0
    _bond_pairs: dict[int, tuple[IntArray, IntArray, IntArray, IntArray]] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        n_up_float = self.n_sites / 2 + self.magnetization
        n_up = int(round(n_up_float))
        if self.n_sites < 2:
            raise ValueError("n_sites must be at least 2")
        if not np.isclose(n_up, n_up_float) or not 0 <= n_up <= self.n_sites:
            raise ValueError(
                "magnetization is incompatible with n_sites; "
                "n_sites/2 + magnetization must be an integer in [0, n_sites]"
            )

    @cached_property
    def n_up(self) -> int:
        return int(round(self.n_sites / 2 + self.magnetization))

    @cached_property
    def states(self) -> IntArray:
        states = []
        for occupied_sites in combinations(range(self.n_sites), self.n_up):
            value = 0
            for site in occupied_sites:
                value |= self.bit_mask(site)
            states.append(value)
        return np.array(sorted(states), dtype=np.int64)

    @cached_property
    def dimension(self) -> int:
        expected = comb(self.n_sites, self.n_up)
        if len(self.states) != expected:
            raise RuntimeError("internal basis construction error")
        return expected

    @cached_property
    def spin_z(self) -> FloatArray:
        """Diagonal values of every local S^z in this sector."""

        values = np.empty((self.dimension, self.n_sites), dtype=np.float64)
        for site in range(self.n_sites):
            up = (self.states & self.bit_mask(site)) != 0
            values[:, site] = np.where(up, 0.5, -0.5)
        return values

    def bit_mask(self, site: int) -> int:
        """Return the bit mask for a site, with site 0 the most-significant bit."""

        if not 0 <= site < self.n_sites:
            raise IndexError(f"site {site} is outside [0, {self.n_sites})")
        return 1 << (self.n_sites - 1 - site)

    def bond_pairs(self, left_site: int) -> tuple[IntArray, IntArray, IntArray, IntArray]:
        """Indices for the 00, 01, 10, and 11 sectors of one periodic bond."""

        left_site %= self.n_sites
        if left_site not in self._bond_pairs:
            right_site = (left_site + 1) % self.n_sites
            left_up = (self.states & self.bit_mask(left_site)) != 0
            right_up = (self.states & self.bit_mask(right_site)) != 0

            idx00 = np.flatnonzero(~left_up & ~right_up).astype(np.int64)
            idx01 = np.flatnonzero(~left_up & right_up).astype(np.int64)
            idx11 = np.flatnonzero(left_up & right_up).astype(np.int64)

            flipped_states = self.states[idx01] ^ (
                self.bit_mask(left_site) | self.bit_mask(right_site)
            )
            idx10 = np.searchsorted(self.states, flipped_states).astype(np.int64)
            if not np.array_equal(self.states[idx10], flipped_states):
                raise RuntimeError("failed to pair the |down up> and |up down> states")

            self._bond_pairs[left_site] = idx00, idx01, idx10, idx11
        return self._bond_pairs[left_site]

    def apply_gate(self, state: ComplexArray, gate: ComplexArray, left_site: int) -> ComplexArray:
        """Apply one local gate to a state or a stack of state-vector columns."""

        state = np.asarray(state, dtype=np.complex128)
        if state.shape[0] != self.dimension:
            raise ValueError(
                f"state leading dimension {state.shape[0]} != sector dimension {self.dimension}"
            )
        if gate.shape != (4, 4):
            raise ValueError("gate must have shape (4, 4)")

        idx00, idx01, idx10, idx11 = self.bond_pairs(left_site)
        out = np.empty_like(state)
        out[idx00, ...] = gate[0, 0] * state[idx00, ...]
        out[idx11, ...] = gate[3, 3] * state[idx11, ...]

        old01 = state[idx01, ...]
        old10 = state[idx10, ...]
        out[idx01, ...] = gate[1, 1] * old01 + gate[1, 2] * old10
        out[idx10, ...] = gate[2, 1] * old01 + gate[2, 2] * old10
        return out

    def typical_initial_state(self, rng: np.random.Generator, site: int | None = None) -> ComplexArray:
        """Draw a typical state in the sector and project one site to spin up."""

        site = self.n_sites // 2 if site is None else site
        allowed = (self.states & self.bit_mask(site)) != 0
        state = rng.normal(size=self.dimension) + 1j * rng.normal(size=self.dimension)
        state = np.where(allowed, state, 0.0)
        norm = np.linalg.norm(state)
        if norm == 0:
            raise ValueError("the requested sector contains no state with the selected site up")
        return np.asarray(state / norm, dtype=np.complex128)

    def magnetization_profile(self, state: ComplexArray) -> FloatArray:
        """Return local ``<S^z_n>`` values."""

        probabilities = np.abs(np.asarray(state)) ** 2
        if probabilities.ndim != 1:
            raise ValueError("magnetization_profile expects a single state vector")
        # Avoid spurious floating-point warnings from a few accelerated BLAS
        # builds when a dot product cancels close to zero.
        return np.asarray(np.sum(probabilities[:, None] * self.spin_z, axis=0), dtype=np.float64)


@dataclass(frozen=True)
class CircuitRealization:
    """One frozen-disorder Floquet circuit, repeated every cycle."""

    J: float
    Jz: float
    gates: tuple[ComplexArray, ...]
    order: tuple[int, ...]
    disorder_parameters: FloatArray

    @classmethod
    def sample(
        cls,
        basis: SectorBasis,
        J: float,
        Jz: float,
        rng: np.random.Generator,
    ) -> "CircuitRealization":
        disorder = rng.uniform(-np.pi, np.pi, size=(basis.n_sites, 3))
        gates = tuple(u1_gate(J, Jz, *parameters) for parameters in disorder)
        order = tuple(int(x) for x in rng.permutation(basis.n_sites))
        return cls(J=J, Jz=Jz, gates=gates, order=order, disorder_parameters=disorder)

    def apply_cycle(self, basis: SectorBasis, state: ComplexArray) -> ComplexArray:
        for bond in self.order:
            state = basis.apply_gate(state, self.gates[bond], bond)
        return state
