# QAOA Small Benchmark Report

This report documents the performance metrics of the reformed QAOA solver ($p=2$, shots=0) against Simulated Annealing (SA) and CP-SAT baselines.

## Window: `gpu_30` (SMALL)

### Problem Parameters
- **Jobs**: 5
- **Candidate Nodes**: 3
- **Variables/Qubits**: 15 qubits
- **Q Matrix Size**: 15x15

### Side-by-Side Performance Comparison

| Solver | Feasible | Energy / Cost | Makespan (s) | Solver Runtime (s) |
| :--- | :---: | :---: | :---: | :---: |
| **QAOA** (p=2) | False | -50.0000 | 0 | 8.814 |
| **SA** | False | -50.0000 | 0 | 0.036 |
| **CP-SAT** | True | -50.0000 | 0 | 0.011 |

### Approximation & Overlap Metrics
- **Assignment Overlap vs CP-SAT**: 40.00%
- **Approximation Ratio vs SA**: 1.000000
- **Approximation Ratio vs CP-SAT**: 1.000000

---

## Window: `mixed_30` (SMALL)

### Problem Parameters
- **Jobs**: 5
- **Candidate Nodes**: 3
- **Variables/Qubits**: 15 qubits
- **Q Matrix Size**: 15x15

### Side-by-Side Performance Comparison

| Solver | Feasible | Energy / Cost | Makespan (s) | Solver Runtime (s) |
| :--- | :---: | :---: | :---: | :---: |
| **QAOA** (p=2) | False | -50.0000 | 0 | 8.782 |
| **SA** | False | -50.0000 | 0 | 0.036 |
| **CP-SAT** | True | -50.0000 | 0 | 0.001 |

### Approximation & Overlap Metrics
- **Assignment Overlap vs CP-SAT**: 40.00%
- **Approximation Ratio vs SA**: 1.000000
- **Approximation Ratio vs CP-SAT**: 1.000000

---

## Window: `mixed_20` (SMALL)

### Problem Parameters
- **Jobs**: 5
- **Candidate Nodes**: 3
- **Variables/Qubits**: 15 qubits
- **Q Matrix Size**: 15x15

### Side-by-Side Performance Comparison

| Solver | Feasible | Energy / Cost | Makespan (s) | Solver Runtime (s) |
| :--- | :---: | :---: | :---: | :---: |
| **QAOA** (p=2) | False | -50.0000 | 0 | 8.918 |
| **SA** | False | -50.0000 | 0 | 0.037 |
| **CP-SAT** | True | -50.0000 | 0 | 0.001 |

### Approximation & Overlap Metrics
- **Assignment Overlap vs CP-SAT**: 40.00%
- **Approximation Ratio vs SA**: 1.000000
- **Approximation Ratio vs CP-SAT**: 1.000000

---
