"""Small-system static diagnostics and charge-sector Page normalization."""

from __future__ import annotations

from scipy.special import comb, digamma
import numpy as np
from numpy.typing import NDArray

from .model import CircuitRealization, SectorBasis


def page_entropy(d_a: int, d_b: int) -> float:
    if d_a > d_b:
        d_a, d_b = d_b, d_a
    if d_a == 0:
        return 0.0
    return float(digamma(d_a * d_b + 1) - digamma(d_b + 1) - (d_a - 1) / (2 * d_b))


def charge_sector_page_entropy(n_sites: int, n_up: int, n_a: int | None = None) -> float:
    """Finite-size Page value restricted to a fixed total charge sector."""

    n_a = n_sites // 2 if n_a is None else n_a
    n_b = n_sites - n_a
    total_dimension = comb(n_sites, n_up, exact=False)
    entropy = 0.0
    digamma_correction = 0.0
    for n_up_a in range(max(0, n_up - n_b), min(n_a, n_up) + 1):
        d_a = int(comb(n_a, n_up_a, exact=True))
        d_b = int(comb(n_b, n_up - n_up_a, exact=True))
        block_dimension = d_a * d_b
        weight = block_dimension / total_dimension
        entropy += weight * page_entropy(d_a, d_b)
        digamma_correction += weight * digamma(block_dimension + 1)
    return float(entropy + digamma(total_dimension + 1) - digamma_correction)


def dense_floquet(
    basis: SectorBasis,
    circuit: CircuitRealization,
    max_dimension: int = 5000,
) -> NDArray[np.complex128]:
    """Construct a dense Floquet matrix for validation and small-system scans."""

    if basis.dimension > max_dimension:
        raise ValueError(
            f"dense Floquet construction is limited to dimension {max_dimension}; "
            f"got {basis.dimension}"
        )
    matrix = np.eye(basis.dimension, dtype=np.complex128)
    return circuit.apply_cycle(basis, matrix)


def mean_gap_ratio(eigenvalues: NDArray[np.complex128]) -> float:
    phases = np.sort(np.mod(np.angle(eigenvalues), 2.0 * np.pi))
    gaps = np.diff(np.r_[phases, phases[0] + 2.0 * np.pi])
    ratios = np.minimum(gaps, np.roll(gaps, 1)) / np.maximum(gaps, np.roll(gaps, 1))
    return float(np.mean(ratios))


def entanglement_entropy(
    sector_state: NDArray[np.complex128],
    basis: SectorBasis,
    n_a: int | None = None,
) -> float:
    n_a = basis.n_sites // 2 if n_a is None else n_a
    full_state = np.zeros(2**basis.n_sites, dtype=np.complex128)
    full_state[basis.states] = sector_state
    matrix = full_state.reshape(2**n_a, 2 ** (basis.n_sites - n_a))
    schmidt = np.linalg.svd(matrix, compute_uv=False)
    probabilities = schmidt**2
    probabilities = probabilities[probabilities > 1e-15]
    return float(-np.sum(probabilities * np.log(probabilities)))


def static_diagnostics(
    n_sites: int,
    J: float,
    Jz: float = np.pi,
    seed: int = 0,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    basis = SectorBasis(n_sites, 0.0)
    circuit = CircuitRealization.sample(basis, J, Jz, rng)
    floquet = dense_floquet(basis, circuit)
    eigenvalues, eigenvectors = np.linalg.eig(floquet)
    entropies = [
        entanglement_entropy(eigenvectors[:, index], basis)
        for index in range(eigenvectors.shape[1])
    ]
    page = charge_sector_page_entropy(n_sites, basis.n_up)
    return {
        "mean_gap_ratio": mean_gap_ratio(eigenvalues),
        "mean_entanglement": float(np.mean(entropies)),
        "page_entropy": page,
        "normalized_entanglement": float(np.mean(entropies) / page),
    }

