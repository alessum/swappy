# Swappy: reproducible anomalous transport in U(1)-symmetric circuits

This is the code-and-data companion to:

> Alessandro Summer, Alexander Nico-Katz, Shane Dooley, and John Goold,
> “Anomalous transport in U(1)-symmetric quantum circuits,”
> *npj Quantum Information* **12**, 32 (2026).
>
> [DOI 10.1038/s41534-025-01178-8](https://doi.org/10.1038/s41534-025-01178-8) ·
> [arXiv:2411.14357](https://arxiv.org/abs/2411.14357)

The repository now contains a deterministic reference implementation,
end-to-end figure generation, invariant tests, and two executable walkthrough
notebooks. The original research scripts and archived data remain at the
top level for provenance.

## Five-minute reproduction

Python 3.10-3.13 is recommended.

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -e ".[notebooks]"

make test
make smoke
```

The smoke run writes five checked outputs under `artifacts/smoke/`:

- `static_diagnostics.png`: the published entanglement and gap-ratio data;
- `magnetization_regimes.png`: localized, ergodic, swappy, and near-SWAP dynamics;
- `circular_moment.png`: the paper’s central complex transport diagnostic;
- `transport_observables.png`: spread, drift speed, and peak decay;
- `phase_scan.png`: finite-size transport exponents and integrated speed.

For a clearer laptop-scale reproduction:

```bash
make quick
```

For the published main dynamical settings (`N=20`, 100 disorder
realizations, 10,000 cycles, 33 values of `J`):

```bash
MPLCONFIGDIR=.cache/matplotlib \
  .venv/bin/swappy-reproduce --profile paper
```

That last command is intentionally HPC-scale. It saves one compressed file per
`J` and reuses completed files, so it can resume after interruption.

## Walkthrough notebooks

- [`01_from_gate_to_swappy.ipynb`](notebooks/01_from_gate_to_swappy.ipynb)
  builds the U(1)-symmetric gate, verifies conservation, and exposes the four
  dynamical regimes from the raw magnetization profile.
- [`02_circular_moment_and_reproduction.ipynb`](notebooks/02_circular_moment_and_reproduction.ipynb)
  explains why the circular moment is novel and experimentally useful, then
  reproduces the static diagnostics and finite-size transport scan.

Run and save both:

```bash
make notebooks
```

## The central idea

The local magnetization profile is mapped to a quasi-probability,

```text
p_n(t) = 2 [M_n(t) - M_B] / [1 - 2 M_B],
```

and compressed into one complex circular moment,

```text
R(t) = sum_n p_n(t) exp(i theta_n).
```

Its phase tracks coherent motion around the periodic chain; its magnitude
tracks spreading. This separates two effects that are difficult to distinguish
in raw heat maps:

- ergodic diffusion contracts `R` toward the origin without sustained rotation;
- swappy transport rotates `R` rapidly while it eventually contracts;
- near the generalized-SWAP point, `R` keeps rotating close to the unit circle.

Because `R` uses only local Z-basis expectation values, the diagnostic maps
cleanly onto present-day digital quantum simulators.

## Supported code

```python
import numpy as np
from swappy import simulate_ensemble

result = simulate_ensemble(
    n_sites=10,
    J=2.551,
    Jz=np.pi,
    cycles=20,
    realizations=8,
    seed=241114357,
)

print(result.mean_spread)
print(result.mean_speed)  # lattice sites per Floquet cycle
```

The supported implementation is under `src/swappy/`. It:

- works directly in a fixed-magnetization sector;
- applies each local gate without constructing the full Floquet matrix;
- freezes disorder and gate ordering within each Floquet realization;
- records the early-time dynamics after every gate;
- uses explicit published coupling units (`J=pi` is generalized SWAP);
- seeds every ensemble reproducibly;
- checks norm and total-magnetization conservation.

See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for the figure map,
numerical conventions, exact commands, and honest computational scope.
[`docs/LLM_GUIDE.md`](docs/LLM_GUIDE.md) gives a compact causal explanation
designed for both new readers and machine-assisted analysis.

## Why the old scripts are not the entry point

The historical top-level scripts document the research process, but several
expect missing cluster lookup/output trees, use older quarter-angle coupling
units, or contain machine-specific assumptions. The archived static CSV files
are still used; the new loader converts them explicitly via
`J_paper = 4 J_stored`.

The reference package leaves those files untouched while providing a clean,
tested path that a new machine can actually execute.
