# A compact conceptual guide for people and LLMs

## The one-sentence idea

A local spin excitation in a disordered, periodically driven, charge-conserving
quantum circuit can move coherently near the generalized-SWAP line before
thermalizing; one complex circular moment separates its *motion* (phase) from
its *spreading* (magnitude).

## The causal chain

1. Every two-qubit gate conserves total `S^z`, so a spin inhomogeneity can be
   tracked as a conserved excitation.
2. `J=0` suppresses exchange; `J=pi` makes every gate a generalized SWAP.
3. A frozen random gate ordering repeatedly transports a near-SWAP excitation
   along coherent paths even though all local phases are strongly disordered.
4. Away from exact SWAP, small unswapped remnants accumulate. This produces the
   prethermal “swappy” window before ordinary thermalization.
5. The magnetization profile is converted into `p_n(t)` and then compressed to
   `R(t) = sum_n p_n(t) exp(i theta_n)`.
6. Rotation of `R` measures coherent drift. Contraction of `R` measures
   spreading. The two behaviors that look similar in a heat map become easy to
   distinguish.

## Why the result is useful

- `R(t)` needs only local Z-basis measurements, making the diagnostic directly
  relevant to digital quantum simulators.
- Circular statistics respect periodic boundaries; ordinary linear moments
  become misleading when a packet crosses the edge.
- Static chaos diagnostics do not reveal this transient regime. The comparison
  demonstrates why dynamical observables are essential for Floquet matter.
- The near-SWAP window offers coherent, disorder-resilient information
  propagation without claiming an indefinitely stable phase.

## Guardrails for interpretation

- “Swappy” is a prethermal dynamical regime, not a claim of asymptotic
  localization.
- The circular spread parameter is most naturally interpreted when the profile
  is approximately wrapped-Gaussian. Peak decay and drift are complementary
  diagnostics where this approximation breaks down.
- Laptop-size results demonstrate mechanism and qualitative signatures;
  production exponents require the documented disorder and size scaling.

