"""End-to-end generation of paper-like figures and machine-readable results."""

from __future__ import annotations

from dataclasses import dataclass
import gc
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .model import REGIMES
from .published_data import load_published_static_data
from .transport import (
    EnsembleResult,
    fit_power_law,
    integrated_speed,
    paper_j_grid,
    simulate_ensemble,
)


PROFILES: dict[str, dict[str, Any]] = {
    "smoke": {
        "n_sites": 8,
        "cycles": 6,
        "realizations": 2,
        "record": "gates",
        "scan_js": np.array([0.395, 1.374, 2.551, 3.138]),
    },
    "quick": {
        "n_sites": 10,
        "cycles": 20,
        "realizations": 8,
        "record": "gates",
        "scan_js": np.array([0.395, 0.78, 1.18, 1.374, 1.77, 2.15, 2.551, 2.90, 3.138]),
    },
    "paper": {
        "n_sites": 20,
        "cycles": 10_000,
        "realizations": 100,
        "record": "paper",
        "scan_js": paper_j_grid(),
    },
}


@dataclass
class CompactTrajectory:
    magnetization: np.ndarray
    circular_mean: np.ndarray


@dataclass
class CompactEnsemble:
    times: np.ndarray
    trajectories: tuple[CompactTrajectory, ...]
    mean_magnetization: np.ndarray
    mean_spread: np.ndarray
    mean_speed: np.ndarray
    mean_peak: np.ndarray
    metadata: dict[str, Any]


def _compact(result: EnsembleResult, keep_trajectories: bool) -> CompactEnsemble:
    """Discard large per-trajectory arrays once their aggregates are computed."""

    if keep_trajectories:
        trajectories = tuple(
            CompactTrajectory(
                magnetization=(
                    trajectory.magnetization
                    if index == 0
                    else np.empty((0, 0), dtype=np.float64)
                ),
                circular_mean=trajectory.circular_mean,
            )
            for index, trajectory in enumerate(result.trajectories)
        )
        mean_magnetization = result.mean_magnetization
    else:
        trajectories = ()
        mean_magnetization = np.empty((0, 0), dtype=np.float64)
    return CompactEnsemble(
        times=result.times,
        trajectories=trajectories,
        mean_magnetization=mean_magnetization,
        mean_spread=result.mean_spread,
        mean_speed=result.mean_speed,
        mean_peak=result.mean_peak,
        metadata=result.metadata,
    )


def _save_ensemble(path: Path, result: EnsembleResult) -> None:
    np.savez_compressed(
        path,
        times=result.times,
        magnetization=np.stack([item.magnetization for item in result.trajectories]),
        circular_mean=np.stack([item.circular_mean for item in result.trajectories]),
        spread=np.stack([item.spread for item in result.trajectories]),
        speed=np.stack([item.speed for item in result.trajectories]),
        peak=np.stack([item.peak for item in result.trajectories]),
        metadata=json.dumps(result.metadata, sort_keys=True),
    )


def _load_ensemble(path: Path) -> EnsembleResult:
    with np.load(path, allow_pickle=False) as data:
        metadata = json.loads(str(data["metadata"]))
        times = data["times"]
        magnetization = data["magnetization"]
        circular_mean = data["circular_mean"]
        spread = data["spread"]
        speed = data["speed"]
        peak = data["peak"]

    trajectories = []
    for index in range(len(magnetization)):
        from .transport import analyze_profiles

        trajectory = analyze_profiles(
            magnetization[index],
            times,
            total_magnetization=metadata["magnetization"],
            metadata={"loaded_from": str(path), "index": index},
        )
        # Preserve the exact archived arrays rather than recomputing roundoff.
        trajectory.circular_mean = circular_mean[index]
        trajectory.spread = spread[index]
        trajectory.speed = speed[index]
        trajectory.peak = peak[index]
        trajectories.append(trajectory)
    profiles = magnetization
    return EnsembleResult(
        times=times,
        trajectories=tuple(trajectories),
        mean_magnetization=profiles.mean(axis=0),
        std_magnetization=profiles.std(axis=0),
        mean_spread=spread.mean(axis=0),
        std_spread=spread.std(axis=0),
        mean_speed=speed.mean(axis=0),
        std_speed=speed.std(axis=0),
        mean_peak=peak.mean(axis=0),
        std_peak=peak.std(axis=0),
        metadata=metadata,
    )


def _simulate_cached(
    output_dir: Path,
    n_sites: int,
    cycles: int,
    realizations: int,
    J: float,
    seed: int,
    record: str,
) -> EnsembleResult:
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / (
        f"N{n_sites}_J{J:.6f}_Jz{np.pi:.6f}_R{realizations}_T{cycles}_{record}.npz"
    )
    if path.exists():
        return _load_ensemble(path)
    result = simulate_ensemble(
        n_sites=n_sites,
        J=J,
        Jz=np.pi,
        cycles=cycles,
        realizations=realizations,
        seed=seed,
        record=record,
    )
    _save_ensemble(path, result)
    return result


def plot_static_diagnostics(output_dir: Path) -> Path:
    entropy, gaps = load_published_static_data()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    colors = plt.cm.viridis(np.linspace(0.08, 0.92, entropy["N"].nunique()))

    for color, n_sites in zip(colors, sorted(entropy["N"].unique())):
        subset = entropy[entropy["N"] == n_sites].sort_values("J_paper")
        axes[0].errorbar(
            subset["J_paper"],
            subset["normalized_entanglement"],
            yerr=subset["sem"],
            marker="o",
            ms=3,
            lw=1,
            color=color,
            label=f"N={n_sites}",
        )
    axes[0].axhline(1.0, color="black", ls="--", lw=0.8)
    axes[0].set(ylabel=r"$\langle S\rangle/S_{\rm Page}$", xlabel=r"$J$")
    axes[0].legend(ncol=2, fontsize=8)

    gap_phase = gaps[gaps["N"] == 15]
    grid = gap_phase.pivot(index="J_paper", columns="Jz_paper", values="gap_ratio_mean")
    heatmap = axes[1].pcolormesh(
        grid.columns,
        grid.index,
        grid.values,
        shading="auto",
        cmap="Blues_r",
        vmin=0.3863,
        vmax=0.6027,
    )
    axes[1].scatter(
        np.full(len(REGIMES), np.pi),
        list(REGIMES.values()),
        color="black",
        s=18,
        zorder=3,
    )
    axes[1].set(ylabel=r"$J$", xlabel=r"$J_z$", xlim=(0, np.pi), ylim=(0, np.pi))
    colorbar = fig.colorbar(heatmap, ax=axes[1], label=r"$\langle r\rangle$")
    colorbar.set_ticks([0.3863, 0.6027], labels=["Poisson", "CUE"])
    fig.suptitle("Published static diagnostics")
    fig.tight_layout()
    path = output_dir / "static_diagnostics.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_regime_profiles(output_dir: Path, results: dict[str, CompactEnsemble]) -> Path:
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharex=True, sharey=True)
    image = None
    for column, (name, result) in enumerate(results.items()):
        for row, profile in enumerate(
            (result.trajectories[0].magnetization, result.mean_magnetization)
        ):
            image = axes[row, column].imshow(
                profile,
                origin="lower",
                aspect="auto",
                extent=(0, result.metadata["n_sites"] - 1, 0, result.times[-1]),
                cmap="RdBu_r",
                vmin=-0.5,
                vmax=0.5,
            )
            axes[row, column].axhline(1, color="black", lw=0.5)
            axes[row, column].axhline(result.metadata["n_sites"] / 2, color="black", lw=0.5, ls="--")
        axes[0, column].set_title(f"{name.replace('_', ' ')}\nJ={result.metadata['J']:.3f}")
        axes[1, column].set_xlabel("site")
    axes[0, 0].set_ylabel("time (single circuit)")
    axes[1, 0].set_ylabel("time (ensemble mean)")
    fig.colorbar(image, ax=axes, label=r"$\langle S_n^z\rangle$", shrink=0.8)
    fig.suptitle("Figure-3-like spin-inhomogeneity dynamics")
    path = output_dir / "magnetization_regimes.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_circular_moment(output_dir: Path, results: dict[str, CompactEnsemble]) -> Path:
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.7))
    unit_angle = np.linspace(0, 2 * np.pi, 400)
    for axis, (name, result) in zip(axes, results.items()):
        axis.plot(np.cos(unit_angle), np.sin(unit_angle), color="black", lw=0.6)
        early_time = result.times <= 100
        for trajectory in result.trajectories:
            circular_mean = trajectory.circular_mean[early_time]
            axis.plot(
                circular_mean.real,
                circular_mean.imag,
                color="0.75",
                lw=0.6,
                alpha=0.6,
            )
        selected = result.trajectories[0].circular_mean[early_time]
        axis.scatter(
            selected.real,
            selected.imag,
            c=result.times[early_time],
            cmap="plasma",
            s=5,
            zorder=3,
        )
        axis.set_title(name.replace("_", " "))
        axis.set_aspect("equal")
        axis.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05), xlabel="Re R")
    axes[0].set_ylabel("Im R")
    fig.suptitle("Figure-4-like circular moment: rotation is drift, contraction is spreading")
    fig.tight_layout()
    path = output_dir / "circular_moment.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_scan(
    output_dir: Path,
    scan: dict[float, CompactEnsemble],
) -> tuple[Path, Path, dict[str, Any]]:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3))
    cmap = plt.cm.magma
    j_values = np.array(sorted(scan))
    normalizer = plt.Normalize(0, np.pi)
    summary: dict[str, Any] = {}

    for J in j_values:
        result = scan[float(J)]
        color = cmap(normalizer(J))
        axes[0].plot(result.times[1:], result.mean_spread[1:], color=color, lw=1)
        speed_window = (result.times > 0) & (result.times <= 100)
        axes[1].plot(
            result.times[speed_window],
            result.mean_speed[speed_window],
            color=color,
            lw=1,
        )
        axes[2].plot(result.times[1:], result.mean_peak[1:], color=color, lw=1)
        fit_window = (max(0.5, result.times[-1] * 0.1), max(1.0, result.times[-1] * 0.45))
        spread_fit = fit_power_law(result.times, result.mean_spread, fit_window)
        peak_fit = fit_power_law(result.times, result.mean_peak, fit_window, decay=True)
        summary[f"{J:.6f}"] = {
            "alpha_sigma": spread_fit["exponent"],
            "alpha_p": peak_fit["exponent"],
            "integrated_speed": integrated_speed(result),
            "fit_window": list(fit_window),
        }

    axes[0].set(xlabel="time", ylabel=r"$\langle\sigma(t)\rangle$", xscale="log")
    axes[1].set(xlabel="time", ylabel=r"$\langle\nu(t)\rangle$", xscale="log")
    axes[2].set(
        xlabel="time",
        ylabel=r"$\langle p_{\max}(t)\rangle$",
        xscale="log",
        yscale="log",
    )
    scalar = plt.cm.ScalarMappable(norm=normalizer, cmap=cmap)
    fig.colorbar(scalar, ax=axes, label=r"$J$", shrink=0.8)
    fig.suptitle(r"Figure-5-like transport observables along $J_z=\pi$")
    path_observables = output_dir / "transport_observables.png"
    fig.savefig(path_observables, dpi=180, bbox_inches="tight")
    plt.close(fig)

    alpha_sigma = [summary[f"{J:.6f}"]["alpha_sigma"] for J in j_values]
    alpha_peak = [summary[f"{J:.6f}"]["alpha_p"] for J in j_values]
    speeds = [summary[f"{J:.6f}"]["integrated_speed"] for J in j_values]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(j_values, alpha_sigma, "o-", label=r"$\alpha_\sigma$")
    axes[0].plot(j_values, alpha_peak, "s-", label=r"$\alpha_p$")
    axes[0].axhline(0.5, color="black", ls="--", lw=0.8, label="diffusive")
    axes[0].axhline(1.0, color="gray", ls=":", lw=0.8, label="ballistic")
    axes[0].set(xlabel=r"$J$", ylabel="fitted exponent")
    axes[0].legend(fontsize=8)
    axes[1].plot(j_values, speeds, "o-")
    axes[1].axhline(2.0, color="black", ls="--", lw=0.8, label="typical SWAP drift")
    axes[1].set(xlabel=r"$J$", ylabel="time-averaged speed (sites/cycle)")
    axes[1].legend(fontsize=8)
    fig.suptitle("Figure-6-like phase scan (finite-size reference)")
    fig.tight_layout()
    path_scan = output_dir / "phase_scan.png"
    fig.savefig(path_scan, dpi=180)
    plt.close(fig)
    return path_observables, path_scan, summary


def run_reproduction(
    profile_name: str = "quick",
    output_dir: str | Path | None = None,
    seed: int = 241114357,
) -> dict[str, Any]:
    if profile_name not in PROFILES:
        raise ValueError(f"unknown profile {profile_name!r}; choose from {sorted(PROFILES)}")
    profile = PROFILES[profile_name]
    output = Path(output_dir or Path("artifacts") / profile_name)
    output.mkdir(parents=True, exist_ok=True)

    regime_results: dict[str, CompactEnsemble] = {}
    for index, (name, J) in enumerate(REGIMES.items()):
        full_result = _simulate_cached(
            output,
            n_sites=profile["n_sites"],
            cycles=profile["cycles"],
            realizations=profile["realizations"],
            J=J,
            seed=seed + 1000 * index,
            record=profile["record"],
        )
        regime_results[name] = _compact(full_result, keep_trajectories=True)
        del full_result
        gc.collect()

    scan_results: dict[float, CompactEnsemble] = {}
    for index, J in enumerate(profile["scan_js"]):
        full_result = _simulate_cached(
            output,
            n_sites=profile["n_sites"],
            cycles=profile["cycles"],
            realizations=profile["realizations"],
            J=float(J),
            seed=seed + 100_000 + 1000 * index,
            record=profile["record"],
        )
        scan_results[float(J)] = _compact(full_result, keep_trajectories=False)
        del full_result
        gc.collect()

    figure_paths = [
        plot_static_diagnostics(output),
        plot_regime_profiles(output, regime_results),
        plot_circular_moment(output, regime_results),
    ]
    observables_path, scan_path, scan_summary = plot_scan(output, scan_results)
    figure_paths.extend([observables_path, scan_path])

    summary = {
        "profile": profile_name,
        "seed": seed,
        "configuration": {
            "n_sites": profile["n_sites"],
            "cycles": profile["cycles"],
            "realizations": profile["realizations"],
            "scan_js": [float(value) for value in profile["scan_js"]],
            "Jz": float(np.pi),
            "record": profile["record"],
        },
        "paper_reference": {
            "doi": "10.1038/s41534-025-01178-8",
            "arxiv": "2411.14357",
        },
        "scan": scan_summary,
        "figures": [str(path) for path in figure_paths],
    }
    with (output / "summary.json").open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return summary
