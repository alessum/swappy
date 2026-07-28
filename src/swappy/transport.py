"""Transport simulation and the circular-moment observables of the paper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
from numpy.typing import NDArray

from .model import CircuitRealization, SectorBasis


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass
class Trajectory:
    times: FloatArray
    magnetization: FloatArray
    quasi_probability: FloatArray
    circular_mean: ComplexArray
    mean_angle: FloatArray
    spread: FloatArray
    speed: FloatArray
    peak: FloatArray
    metadata: dict[str, Any]


@dataclass
class EnsembleResult:
    times: FloatArray
    trajectories: tuple[Trajectory, ...]
    mean_magnetization: FloatArray
    std_magnetization: FloatArray
    mean_spread: FloatArray
    std_spread: FloatArray
    mean_speed: FloatArray
    std_speed: FloatArray
    mean_peak: FloatArray
    std_peak: FloatArray
    metadata: dict[str, Any]


def quasi_probability(magnetization: FloatArray, total_magnetization: float = 0.0) -> FloatArray:
    """Map local ``<S^z_n>`` to Eq. (8)'s quasi-probability profile."""

    magnetization = np.asarray(magnetization, dtype=np.float64)
    n_sites = magnetization.shape[-1]
    background = (total_magnetization - 0.5) / (n_sites - 1)
    return 2.0 * (magnetization - background) / (1.0 - 2.0 * background)


def circular_observables(
    probabilities: FloatArray,
    times: FloatArray,
    center: int | None = None,
) -> tuple[ComplexArray, FloatArray, FloatArray, FloatArray, FloatArray]:
    """Return ``R``, ``mu``, ``sigma``, drift speed, and ``p_max``.

    Speed follows the boundary-safe angle in the paper's footnote and is
    converted from radians to lattice sites per Floquet cycle.
    """

    probabilities = np.asarray(probabilities, dtype=np.float64)
    times = np.asarray(times, dtype=np.float64)
    n_sites = probabilities.shape[-1]
    center = n_sites // 2 if center is None else center
    theta = 2.0 * np.pi * (np.arange(n_sites) - center) / n_sites

    # ``sum`` avoids spurious floating-point warnings emitted by some BLAS
    # builds for real-by-complex matrix multiplication near exact cancellation.
    circular_mean = np.sum(probabilities * np.exp(1j * theta), axis=-1)
    mean_angle = np.angle(circular_mean)
    radius = np.clip(np.abs(circular_mean), np.finfo(float).tiny, 1.0)
    spread = np.sqrt(np.maximum(0.0, -2.0 * np.log(radius)))

    reflected_mean = np.sum(probabilities * np.exp(1j * np.abs(theta)), axis=-1)
    reflected_angle = np.unwrap(np.angle(reflected_mean))
    if len(times) > 1:
        speed = np.abs(np.gradient(reflected_angle, times)) * n_sites / (2.0 * np.pi)
    else:
        speed = np.zeros_like(times)
    peak = np.max(probabilities, axis=-1)
    return circular_mean, mean_angle, spread, speed, peak


def analyze_profiles(
    magnetization: FloatArray,
    times: FloatArray,
    total_magnetization: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> Trajectory:
    probabilities = quasi_probability(magnetization, total_magnetization)
    circular_mean, mean_angle, spread, speed, peak = circular_observables(
        probabilities, times
    )
    return Trajectory(
        times=np.asarray(times, dtype=np.float64),
        magnetization=np.asarray(magnetization, dtype=np.float64),
        quasi_probability=probabilities,
        circular_mean=circular_mean,
        mean_angle=mean_angle,
        spread=spread,
        speed=speed,
        peak=peak,
        metadata={} if metadata is None else metadata,
    )


def simulate_trajectory(
    n_sites: int,
    J: float,
    Jz: float = np.pi,
    cycles: int = 20,
    seed: int = 0,
    magnetization: float = 0.0,
    record: str = "gates",
) -> Trajectory:
    """Simulate one frozen-disorder Floquet realization.

    ``record="gates"`` records after every local gate at increments ``1/N``;
    this is the convention used for the early-time paper plots.  ``"cycles"``
    records only after complete Floquet cycles.  ``"paper"`` is gate-resolved
    through cycle 100 and increasingly stroboscopic thereafter, mirroring the
    production workflow while avoiding unnecessarily large long-time arrays.
    """

    _validate_sampling(cycles, record)
    basis = SectorBasis(n_sites, magnetization)
    return _simulate_trajectory_in_basis(basis, J, Jz, cycles, seed, record)


def _validate_sampling(cycles: int, record: str) -> None:
    if cycles < 1:
        raise ValueError("cycles must be positive")
    if record not in {"gates", "cycles", "paper"}:
        raise ValueError("record must be 'gates', 'cycles', or 'paper'")


def _simulate_trajectory_in_basis(
    basis: SectorBasis,
    J: float,
    Jz: float,
    cycles: int,
    seed: int,
    record: str,
) -> Trajectory:
    """Internal trajectory implementation that reuses sector lookup tables."""

    rng = np.random.default_rng(seed)
    circuit = CircuitRealization.sample(basis, J, Jz, rng)
    state = basis.typical_initial_state(rng)

    times = [0.0]
    profiles = [basis.magnetization_profile(state)]
    for cycle in range(cycles):
        for gate_number, bond in enumerate(circuit.order, start=1):
            state = basis.apply_gate(state, circuit.gates[bond], bond)
            if record == "gates" or (record == "paper" and cycle < 100):
                times.append(cycle + gate_number / basis.n_sites)
                profiles.append(basis.magnetization_profile(state))
        if record == "cycles":
            times.append(float(cycle + 1))
            profiles.append(basis.magnetization_profile(state))
        elif record == "paper" and cycle >= 100 and _paper_cycle_is_sampled(cycle + 1):
            times.append(float(cycle + 1))
            profiles.append(basis.magnetization_profile(state))

    metadata = {
        "n_sites": basis.n_sites,
        "dimension": basis.dimension,
        "magnetization": basis.magnetization,
        "J": float(J),
        "Jz": float(Jz),
        "cycles": cycles,
        "seed": int(seed),
        "record": record,
        "gate_order": list(circuit.order),
    }
    trajectory = analyze_profiles(
        np.asarray(profiles),
        np.asarray(times),
        total_magnetization=basis.magnetization,
        metadata=metadata,
    )

    final_norm = np.linalg.norm(state)
    if not np.isclose(final_norm, 1.0, atol=1e-10):
        raise RuntimeError(f"state norm drifted to {final_norm}")
    return trajectory


def _paper_cycle_is_sampled(completed_cycle: int) -> bool:
    """Long-time sampling schedule used by the paper profile."""

    if completed_cycle <= 200:
        stride = 1
    elif completed_cycle <= 500:
        stride = 2
    elif completed_cycle <= 1_000:
        stride = 5
    elif completed_cycle <= 2_000:
        stride = 10
    elif completed_cycle <= 5_000:
        stride = 20
    elif completed_cycle <= 10_000:
        stride = 50
    else:
        stride = 100
    return completed_cycle % stride == 0


def simulate_ensemble(
    n_sites: int,
    J: float,
    Jz: float = np.pi,
    cycles: int = 20,
    realizations: int = 8,
    seed: int = 0,
    magnetization: float = 0.0,
    record: str = "gates",
) -> EnsembleResult:
    if realizations < 1:
        raise ValueError("realizations must be positive")
    _validate_sampling(cycles, record)
    basis = SectorBasis(n_sites, magnetization)
    seeds = np.random.SeedSequence(seed).spawn(realizations)
    trajectories = tuple(
        _simulate_trajectory_in_basis(
            basis=basis,
            J=J,
            Jz=Jz,
            cycles=cycles,
            seed=int(child.generate_state(1, dtype=np.uint32)[0]),
            record=record,
        )
        for child in seeds
    )
    times = trajectories[0].times
    if not all(np.array_equal(item.times, times) for item in trajectories):
        raise RuntimeError("ensemble trajectories have inconsistent time grids")

    profiles = np.stack([item.magnetization for item in trajectories])
    spread = np.stack([item.spread for item in trajectories])
    speed = np.stack([item.speed for item in trajectories])
    peak = np.stack([item.peak for item in trajectories])
    return EnsembleResult(
        times=times,
        trajectories=trajectories,
        mean_magnetization=profiles.mean(axis=0),
        std_magnetization=profiles.std(axis=0, ddof=0),
        mean_spread=spread.mean(axis=0),
        std_spread=spread.std(axis=0, ddof=0),
        mean_speed=speed.mean(axis=0),
        std_speed=speed.std(axis=0, ddof=0),
        mean_peak=peak.mean(axis=0),
        std_peak=peak.std(axis=0, ddof=0),
        metadata={
            "n_sites": n_sites,
            "magnetization": magnetization,
            "J": float(J),
            "Jz": float(Jz),
            "cycles": cycles,
            "realizations": realizations,
            "seed": int(seed),
            "record": record,
        },
    )


def fit_power_law(
    times: FloatArray,
    values: FloatArray,
    window: tuple[float, float],
    decay: bool = False,
) -> dict[str, float]:
    """Fit ``values ~ amplitude * times**exponent`` on a log-log window."""

    times = np.asarray(times, dtype=np.float64)
    values = np.asarray(values, dtype=np.float64)
    mask = (
        (times >= window[0])
        & (times <= window[1])
        & np.isfinite(values)
        & (times > 0)
        & (values > 0)
    )
    if mask.sum() < 3:
        return {"exponent": float("nan"), "amplitude": float("nan"), "r2": float("nan")}

    x = np.log(times[mask])
    y = np.log(values[mask])
    slope, intercept = np.polyfit(x, y, deg=1)
    predicted = slope * x + intercept
    denominator = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - np.sum((y - predicted) ** 2) / denominator if denominator else 1.0
    exponent = -slope if decay else slope
    return {
        "exponent": float(exponent),
        "amplitude": float(np.exp(intercept)),
        "r2": float(r2),
    }


def paper_j_grid() -> FloatArray:
    first_half = np.linspace(0.001, 0.999 * np.pi / 2.0, 17)
    return np.append(first_half, np.pi - first_half[:-1][::-1])


def integrated_speed(result: EnsembleResult, max_time: float | None = None) -> float:
    max_time = result.metadata["n_sites"] / 2 if max_time is None else max_time
    mask = result.times <= max_time
    if mask.sum() < 2:
        return float("nan")
    duration = result.times[mask][-1] - result.times[mask][0]
    return float(np.trapezoid(result.mean_speed[mask], result.times[mask]) / duration)
