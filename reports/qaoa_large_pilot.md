# QAOA Large Pilot Report

This report documents the performance metrics of the reformed QAOA solver ($p=2$, shots=0) against Simulated Annealing (SA) and CP-SAT baselines on a 30-qubit Large window.
Note: The QAOA simulation on 30 qubits has been deferred to an Nvidia A100 card (80GB VRAM) due to CPU memory capacity constraints on the local workstation.

## Window: `gpu_30` (LARGE)

### Problem Parameters
- **Jobs**: 10
- **Candidate Nodes**: 3
- **Variables/Qubits**: 30 qubits
- **Q Matrix Size**: 30x30

### Side-by-Side Performance Comparison (Pilot Run: 1 iteration)

| Solver | Feasible | Energy / Cost | Makespan (s) | Solver Runtime (s) |
| :--- | :---: | :---: | :---: | :---: |
| **QAOA** (p=2, 1 iter) | Deferred (A100) | N/A | N/A | N/A |
| **SA** | False | -100.0000 | 0 | 0.099 |
| **CP-SAT** | True | -100.0000 | 0 | 0.003 |

### Approximation & Overlap Metrics
- **Assignment Overlap vs CP-SAT**: N/A (Deferred)
- **Approximation Ratio vs SA**: N/A (Deferred)
- **Approximation Ratio vs CP-SAT**: N/A (Deferred)

### Large Simulation Hardware Metrics
- **Peak RAM Usage (Process Total)**: 758.23 MB (SA & CP-SAT only)
- **Incremental Simulation RAM Overhead**: 7.12 MB
- **Simulation Runtime (1 iteration)**: Deferred (A100)
- **Estimated Runtime for 100 iterations**: N/A (Deferred to A100)
- **Optimization Method**: COBYLA (noiseless statevector expectation)
