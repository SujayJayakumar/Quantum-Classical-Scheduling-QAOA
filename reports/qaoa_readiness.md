# Phase 5.8: QAOA Readiness Report

This report assesses the practical feasibility of simulating the reduced quantum windows on available hardware, considering both noiseless (statevector) and noisy (density matrix) simulation.

## Simulation Memory Requirements

The memory required for simulation depends heavily on the chosen method:

*   **Statevector Simulation (Noiseless)**: Memory grows as O(2^N), where N is the number of qubits. This is suitable for initial QAOA validation and benchmarking makespan.
*   **Density Matrix Simulation (Noisy)**: Memory grows as O(4^N). This is required for studying the impact of noise (e.g., depolarization, bit-flips) but is only feasible for very small qubit counts.

## Classification for Statevector Simulation

This is the most likely starting point for QAOA benchmarking.

| Qubits | Memory (Approx) | Classification | Feasible On |
|:---|:---|:---|:---|
| <= 25 | < 512 MB | `LAPTOP_SAFE` | Standard Laptop (32 GB RAM) |
| 26 - 32 | 1 GB - 64 GB | `A100_SAFE` | A100 GPU (80 GB VRAM) |
| > 32 | > 64 GB | `TOO_LARGE` | Requires HPC cluster |

**Conclusion**: All `SMALL`, `MEDIUM`, and `LARGE` budget windows are ready for **noiseless statevector simulation** on appropriate hardware.

## Classification for Density Matrix Simulation

This is necessary for the noise-aware portion of the research.

| Qubits | Memory (Approx) | Classification | Feasible On |
|:---|:---|:---|:---|
| <= 14 | < 4 GB | `LAPTOP_SAFE` | Standard Laptop (32 GB RAM) |
| 15 - 16 | 16 GB - 64 GB | `A100_SAFE` | A100 GPU (80 GB VRAM) |
| >= 17 | > 256 GB | `TOO_LARGE` | Requires HPC cluster |

**Conclusion**: Only the `SMALL` budget windows (12-16 qubits) are ready for **noisy density matrix simulation**. The `MEDIUM` and `LARGE` windows are too large to be practically simulated with noise on a single A100 GPU.

## Recommendation

Begin QAOA benchmarking using statevector simulation across all budget sizes. Reserve density matrix simulation for a focused noise study on the `SMALL` budget windows only.