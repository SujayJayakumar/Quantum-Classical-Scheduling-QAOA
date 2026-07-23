# QAOA Medium Pilot Report

This report documents the performance metrics of the reformed QAOA solver ($p=2$, shots=0) against Simulated Annealing (SA) and CP-SAT baselines.

## Window: `gpu_30` (MEDIUM)

### Problem Parameters
- **Jobs**: 8
- **Candidate Nodes**: 3
- **Variables/Qubits**: 24 qubits
- **Q Matrix Size**: 24x24

### Side-by-Side Performance Comparison

| Solver | Feasible | Energy / Cost | Makespan (s) | Solver Runtime (s) |
| :--- | :---: | :---: | :---: | :---: |
| **QAOA** (p=2) | False | -80.0000 | 0 | 833.962 |
| **SA** | False | -80.0000 | 0 | 0.071 |
| **CP-SAT** | True | -80.0000 | 0 | 0.001 |

### Approximation & Overlap Metrics
- **Assignment Overlap vs CP-SAT**: 37.50%
- **Approximation Ratio vs SA**: 1.000000
- **Approximation Ratio vs CP-SAT**: 1.000000

---
