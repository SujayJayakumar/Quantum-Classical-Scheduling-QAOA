# QUBO Complexity Reduction Report

This report compares the complexity of the original QUBO formulation (with quadratic capacity penalties) against the new formulation (Option B: feasibility pruning and variable pruning) for the toy problems (`2x2`, `3x2`, and `4x3`).

---

## Complexity Metrics Comparison

| Toy Instance | Model | Variables | Qubits | Non-Zero Q Entries | Hamiltonian Terms | Execution Runtime |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **2x2** | OLD | 4 | 4 | 8 | 8 | 0.087s |
| **2x2** | NEW | 3 | 3 | 4 | 4 | 0.069s |
| **2x2** | **RED %** | **25.00%** | **25.00%** | **50.00%** | **50.00%** | **20.69%** |
| | | | | | | |
| **3x2** | OLD | 6 | 6 | 15 | 15 | 0.163s |
| **3x2** | NEW | 5 | 5 | 7 | 7 | 0.102s |
| **3x2** | **RED %** | **16.67%** | **16.67%** | **53.33%** | **53.33%** | **37.42%** |
| | | | | | | |
| **4x3** | OLD | 12 | 12 | 42 | 42 | 1.664s |
| **4x3** | NEW | 10 | 10 | 18 | 18 | 0.301s |
| **4x3** | **RED %** | **16.67%** | **16.67%** | **57.14%** | **57.14%** | **81.91%** |

---

## Detailed Complexity Reduction Insights

1. **Variables & Qubits Reduction**:
   * Pruning incompatible job-node pairs (such as GPU-demanding jobs mapped to CPU-only nodes) reduces the required variables by **16.6% to 25.0%**.
   * On quantum hardware, this corresponds to saving up to **2 qubits** on a 12-qubit problem, moving the hardware threshold for scheduling problems lower.
2. **Matrix Sparsity & Hamiltonian Term Reduction**:
   * Removing the quadratic capacity terms from the formulation leads to a **50% to 57.1%** reduction in the number of non-zero entries in the $Q$ matrix and individual terms in the Ising Hamiltonian.
   * This directly translates to **fewer entangling CNOT and RZ gates** in the QAOA ansatz circuit, dramatically reducing execution noise on real quantum processing units (QPUs).
3. **Execution Runtime Speedup**:
   * Due to the smaller Hilbert space dimension ($2^{10} = 1024$ states vs $2^{12} = 4096$ states for `4x3`) and simplified expectation calculation, optimizer search path is shortened.
   * This delivers up to **81.9%** runtime savings on `4x3` (from 1.66s to 0.30s), showing a **5.5x speedup**.
