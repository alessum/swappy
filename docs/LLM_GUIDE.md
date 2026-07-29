# A compact conceptual guide for people and LLMs

## The one-sentence idea

A strongly disordered, discrete-time, U(1)-symmetric quantum circuit hosts a prethermal *swappy regime* near the generalized-SWAP line in which a local spin excitation spreads *faster than in the ordinary ergodic regime* — an imperfect SWAP hands off most of the excitation while leaving a small remnant behind, so a coherent peak moves almost ballistically while remnants diffuse locally, a mechanism with no continuous-time XXZ analog; one complex circular moment separates its *motion* (phase) from its *spreading* (magnitude) using only local Z-basis measurements.

## The five points, restated

1. **The model is digital, not a Trotter approximation.** Every two-qubit gate has an XXZ-like exchange $J$, an Ising term $J_z$, and three order-one random phases $(h, h', \phi)$. The disorder is *not* scaled down with the kick strength, so small $J$ or $J_z$ do not silently reduce to a weak continuous-time step. The same circuit covers localized-like, ergodic, swappy, and generalized-SWAP transport.
2. **Periodic evolution needs circular statistics.** Site $N-1$ and site $0$ are neighbors, so a linear mean would misread a packet that crosses the seam. Map the magnetization profile to a quasi-probability $p_n(t)$, then compress it to $R(t)=\sum_n p_n(t)\,e^{2\pi i n/N}$. The phase of $R$ tracks drift on the ring; the magnitude of $R$ tracks spreading. The diagnostic uses only local $\langle S^z_n\rangle$ measurements.
3. **The key observation is super-ergodic diffusion.** Near the generalized-SWAP line, each gate transfers most of the local magnetization to its neighbor but keeps a small remnant. A coherent peak therefore travels almost ballistically while remnants leak behind, and the resulting global spreading is *faster* than in the ordinary ergodic regime, even under strong disorder. Static chaos indicators (entanglement, level statistics) miss this — the swappy regime lives only in the dynamics.
4. **Swappy transport is prethermal and purely discrete-time.** It relies on the finite duration of a near-$\pi$ exchange pulse: the almost-SWAP gate is what does the transfer and the splitting. There is no continuous-time XXZ analog. Thermalization time scales as $t_\mathrm{th}\sim(\pi-J)^{-2}$ as the SWAP point is approached.
5. **Generalized SWAPs defeat disorder but are sensitive to detuning.** On the $J=\pi$ line, random phases do not stop the ballistic hand-off and the excitation keeps circulating without thermalizing. Any detuning makes each hand-off slightly incomplete; accumulating remnants eventually erase the coherent peak. The swappy window is therefore long-lived and robust over finite $(J, J_z)$ and $N$ ranges, but not an asymptotically stable phase.

## Guardrails for interpretation

- "Swappy" is a *prethermal dynamical regime*, not a claim of asymptotic localization or of an indefinitely stable phase.
- The circular spread $\sigma(t)$ is most naturally interpreted when the profile is approximately wrapped-Gaussian; the peak decay $p_\mathrm{max}(t)$ and the drift speed $\nu(t)$ are complementary diagnostics where this approximation breaks down.
- Static diagnostics alone cannot detect the swappy regime; dynamical observables are essential for Floquet matter.
- Laptop-size reproductions demonstrate the mechanism and qualitative signatures; extracting production exponents requires the documented disorder and size scaling from the paper profile.

