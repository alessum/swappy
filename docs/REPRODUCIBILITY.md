# Reproducibility map

This repository accompanies:

> Alessandro Summer, Alexander Nico-Katz, Shane Dooley, and John Goold,
> “Anomalous transport in U(1)-symmetric quantum circuits,”
> *npj Quantum Information* **12**, 32 (2026).
> DOI: `10.1038/s41534-025-01178-8`; arXiv: `2411.14357`.

## What is reproduced

| Paper result | Repository output | Source |
|---|---|---|
| Figure 2: entropy along `Jz=pi` and the 2D gap-ratio phase diagram | `static_diagnostics.png` | Archived POLFED CSV data, with the old coupling convention converted by `J_paper = 4 J_stored` |
| Figure 3: four dynamical regimes | `magnetization_regimes.png` | Fresh fixed-charge time evolution |
| Figure 4: circular moment trajectories | `circular_moment.png` | Fresh time evolution and Eqs. (8)-(10) |
| Figure 5: spread, speed, and peak decay | `transport_observables.png` | Fresh disorder ensembles |
| Figure 6: transport exponents and integrated speed | `phase_scan.png` | Fresh seeded scan and documented log-log fits |

The laptop profiles are finite-size reproductions of the qualitative physics.
The `paper` profile uses the main published dynamical settings (`N=20`, 100
realizations, 10,000 Floquet cycles, 33 values of `J` along `Jz=pi`). It is an
HPC-scale calculation and writes one compressed, resumable file per `J`.

## Exact commands

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -e ".[notebooks]"

# Fast wiring and invariant check
make test
make smoke

# Laptop-scale end-to-end reproduction
make quick

# Published dynamical settings; expect an HPC-scale run
make paper

# Execute and save both pedagogical notebooks
make notebooks
```

All profiles are deterministic by default (`seed=241114357`). Existing
per-parameter `.npz` results are loaded rather than recomputed, so interrupted
paper-scale scans resume naturally.

## Numerical conventions

- Bit `1` denotes spin up and local `S^z=+1/2`.
- Dynamics is restricted to the `M=0` sector of dimension `binom(N, N/2)`.
- A realization freezes three disorder phases per bond and one random
  permutation of the `N` periodic nearest-neighbor gates.
- Time is measured in Floquet cycles. Early dynamics is sampled after every
  gate, at increments of `1/N`. The paper profile becomes increasingly
  stroboscopic after cycle 100, matching the production strategy and keeping
  long-time files tractable.
- The initial state is a typical random state in the fixed-charge sector,
  projected to have the central spin up.
- The quasi-probability and circular moment follow the final published
  equations. Drift is reported in lattice sites per Floquet cycle.

## Honest scope

The complete published data generation used MeluXina and includes finite-size
and long-time sweeps that are intentionally expensive. The quick profile is
not a numerical substitute for those production sweeps. Its purpose is to:

1. prove that the model and analysis are executable end to end;
2. expose the localized, ergodic, swappy, and near-SWAP mechanisms;
3. validate conservation laws and gate conventions;
4. give readers and LLMs a compact path from the gate to the paper’s claims.

The original exploratory and cluster scripts remain available in Git history.
They are not part of the supported interface because they depend on absent
lookup/output trees, contain machine-specific assumptions, and mix older
coupling conventions.

