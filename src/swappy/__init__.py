"""Reproducible tools for the swappy-regime paper."""

from .model import REGIMES, CircuitRealization, SectorBasis, u1_gate
from .transport import (
    EnsembleResult,
    Trajectory,
    analyze_profiles,
    fit_power_law,
    simulate_ensemble,
    simulate_trajectory,
)

__all__ = [
    "REGIMES",
    "CircuitRealization",
    "EnsembleResult",
    "SectorBasis",
    "Trajectory",
    "analyze_profiles",
    "fit_power_law",
    "simulate_ensemble",
    "simulate_trajectory",
    "u1_gate",
]

__version__ = "0.1.0"

