# QAOA Toy Validation Report

This report documents the validation of the CUDA-Q QAOA solver on toy problems, comparing it against classical exact (Brute Force, CP-SAT) and heuristic (Simulated Annealing) baselines.

---

## STAGE 1: QUBO-TO-ISING VALIDATION

We verify that the classical QUBO energy matches the quantum expectation value of the Ising Hamiltonian (plus the offset) for all possible computational basis states: $E_{\text{QUBO}}(x) = \langle z | H_{\text{Ising}} | z \rangle + \text{offset}$.

| Instance | Qubits | Total States | Passed Matches | Failed Matches | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `2x2` | 3 | 8 | 8 | 0 | **PASSED** |
| `3x2` | 5 | 32 | 32 | 0 | **PASSED** |
| `4x3` | 10 | 1024 | 1024 | 0 | **PASSED** |

---

## STAGE 2: QAOA SOLVER TOY VALIDATION

We evaluate the QAOA solver (using $p=2$ and noiseless COBYLA optimization, followed by 1000 sampling shots) against SA, CP-SAT, and exact Brute Force search.

### Toy Instance: `2x2`
- **Qubits**: 3 qubits
- **Runtime**: 0.069 seconds
- **Feasible Assignment Rate (Sampled)**: 95.80%
- **Energy Gap**: 0.0900 (QAOA: -29.5950 vs Brute Force: -29.6850, Gap %: 0.30%)
- **Optimal Assignment Match**: CP-SAT: `False`, Brute Force: `False`

| Solver | Feasible | Assignment | Energy / Cost |
| :--- | :---: | :--- | :---: |
| **QAOA** (p=2) | True | `{'j0': 'n1', 'j1': 'n0'}` | -29.5950 |
| **SA** | True | `{'j0': 'n0', 'j1': 'n0'}` | - |
| **CP-SAT** | True | `{'j0': 'n0', 'j1': 'n0'}` | - |
| **Brute Force** | True | `{'j0': 'n0', 'j1': 'n0'}` | -29.6850 |

### Toy Instance: `3x2`
- **Qubits**: 5 qubits
- **Runtime**: 0.124 seconds
- **Feasible Assignment Rate (Sampled)**: 76.40%
- **Energy Gap**: 0.2100 (QAOA: -43.8200 vs Brute Force: -44.0300, Gap %: 0.48%)
- **Optimal Assignment Match**: CP-SAT: `False`, Brute Force: `False`

| Solver | Feasible | Assignment | Energy / Cost |
| :--- | :---: | :--- | :---: |
| **QAOA** (p=2) | True | `{'j0': 'n1', 'j1': 'n0', 'j2': 'n0'}` | -43.8200 |
| **SA** | True | `{'j0': 'n0', 'j1': 'n0', 'j2': 'n0'}` | - |
| **CP-SAT** | True | `{'j0': 'n0', 'j1': 'n0', 'j2': 'n0'}` | - |
| **Brute Force** | True | `{'j0': 'n0', 'j1': 'n0', 'j2': 'n0'}` | -44.0300 |

### Toy Instance: `4x3`
- **Qubits**: 10 qubits
- **Runtime**: 0.266 seconds
- **Feasible Assignment Rate (Sampled)**: 44.70%
- **Energy Gap**: 0.1500 (QAOA: -49.1650 vs Brute Force: -49.3150, Gap %: 0.30%)
- **Optimal Assignment Match**: CP-SAT: `False`, Brute Force: `False`

| Solver | Feasible | Assignment | Energy / Cost |
| :--- | :---: | :--- | :---: |
| **QAOA** (p=2) | True | `{'j0': 'n1', 'j1': 'n0', 'j2': 'n1', 'j3': 'n2'}` | -49.1650 |
| **SA** | True | `{'j0': 'n2', 'j1': 'n2', 'j2': 'n2', 'j3': 'n0'}` | - |
| **CP-SAT** | True | `{'j0': 'n2', 'j1': 'n2', 'j2': 'n2', 'j3': 'n2'}` | - |
| **Brute Force** | True | `{'j0': 'n0', 'j1': 'n2', 'j2': 'n2', 'j3': 'n0'}` | -49.3150 |
