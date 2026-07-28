# 🌀 Anomalous Transport in U(1)-Symmetric Quantum Circuits

[![Paper](https://img.shields.io/badge/paper-npj%20Quantum%20Information-6f42c1)](https://doi.org/10.1038/s41534-025-01178-8)
[![arXiv](https://img.shields.io/badge/arXiv-2411.14357-b31b1b)](https://arxiv.org/abs/2411.14357)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Reproducible](https://img.shields.io/badge/reproducibility-tested-2e8b57)](docs/REPRODUCIBILITY.md)

Notebooks and reproduction code accompanying:

> Alessandro Summer, Alexander Nico-Katz, Shane Dooley, and John Goold,
> **“Anomalous transport in U(1)-symmetric quantum circuits,”**
> *npj Quantum Information* **12**, 32 (2026).
> [doi:10.1038/s41534-025-01178-8](https://doi.org/10.1038/s41534-025-01178-8)

**TL;DR.** We study transport in a disordered, U(1)-symmetric Floquet quantum circuit. Between its localized and ergodic regions, and close to a generalized-SWAP line, we find a genuinely discrete-time **swappy regime**: local excitations move coherently and ballistically despite strong disorder before eventually thermalizing. Its lifetime grows approximately as
$(\pi-J)^{-2}$. We introduce a complex **circular moment** that separates directed motion from spreading using only local Z-basis measurements. This repository provides a short route from the two-qubit gate to the central figures and transport diagnostics.

**Keywords:** quantum transport · Floquet circuits · U(1) symmetry · disorder · statistics · localization · digital quantum simulation.

## 🎯 Main points

1. **🧭 One model connects several transport regimes.**

   A generic disordered U(1)-symmetric circuit can be tuned between localized-like, ergodic, swappy, and near-SWAP behavior. The static entanglement and level statistics identify localization,ergodicity, and integrable lines, but do not by themselves reveal the swappy regime.
   [Walkthrough](notebooks/01_from_gate_to_swappy.ipynb)

2. **🌀 Strong disorder does not prevent transient ballistic motion.**

   Near the generalized-SWAP line, a local magnetization packet propagates coherently through the circuit before decohering. This produces faster transport than in the ordinary ergodic regime and is visible in individual trajectories as a moving, long-lived peak.
   [Dynamical reproduction](notebooks/01_from_gate_to_swappy.ipynb)

3. **⏳ The swappy regime is prethermal and Floquet-specific.**

   The thermalization time grows approximately as $t_{\mathrm{th}}\sim(\pi-J)^{-2}$ near the SWAP point. The regime is dynamical, stable over the investigated parameters and system sizes, and disappears in the continuous-time limit. It therefore has no direct
   counterpart in the ordinary continuous-time disordered XXZ chain.
   [Reproducibility map](docs/REPRODUCIBILITY.md)

4. **🎯 A circular moment separates drift from spreading.**

   The magnetization profile is mapped to a quasi-probability distribution and compressed into one complex number $R(t)$. Its phase tracks directed motion around the periodic chain, while its magnitude tracks spreading.
   Localized, diffusive, swappy, and near-SWAP dynamics become immediately distinguishable as trajectories in the complex plane.
   [Analysis walkthrough](notebooks/02_circular_moment_and_reproduction.ipynb)

5. **🔬 The diagnostic is experimentally accessible.**

   The circular moment uses only local Z-basis expectation values rather than full state tomography. This gives digital quantum simulators a direct way to probe transport, drift, and prethermal dynamics.

## 📓 The notebooks

1. [`01_from_gate_to_swappy.ipynb`](notebooks/01_from_gate_to_swappy.ipynb)
   Construct the U(1)-symmetric gate and watch the four regimes emerge.

2. [`02_circular_moment_and_reproduction.ipynb`](notebooks/02_circular_moment_and_reproduction.ipynb)
   Build the circular moment and reproduce the transport analysis.

Execute both:

```bash
make setup
make notebooks
```

## ▶️ Reproduce the results

For a laptop-scale reproduction:

```bash
make setup
make quick
```

This generates:

| Paper result | Output |
|---|---|
| Static localization and ergodicity diagnostics | `static_diagnostics.png` |
| Four dynamical regimes | `magnetization_regimes.png` |
| Circular-moment trajectories | `circular_moment.png` |
| Spread, drift, peak decay, and coupling scan | `transport_observables.png`, `phase_scan.png` |

The figures are written to `artifacts/quick/`. Verify the implementation with:

```bash
make test
```

For the published main dynamical settings:

```bash
make paper
```

The paper profile uses `N=20`, 100 disorder realizations, 10,000 Floquet cycles, and 33 values of $J$. It is an HPC-scale, resumable calculation.
See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for the exact figure map, conventions, and computational scope.

## 📁 Repository contents

```text
notebooks/   guided explanation
src/swappy/  supported simulation and analysis
tests/       physics and reproducibility checks
docs/        detailed methods and figure map
data/        two archived static-data tables
```
