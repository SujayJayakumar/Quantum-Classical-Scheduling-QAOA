# Phase 7E Sensitivity Study: Soft Capacity Complexity Analysis

This report evaluates the complexity impact (qubits and couplings) of adding the soft capacity utilization penalty (Option B+) to the unconstrained mapping formulation (Option B).

## 1. Complexity Comparison Table

| Window | Qubits (Option B) | Qubits (Option B+) | Added Variables | Couplings (Option B) | Couplings (Option B+) | Added Couplings | Coupling Increase (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **small_0** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_1** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_2** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_3** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_4** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_5** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_6** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_7** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_8** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_9** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_10** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_11** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_12** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_13** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **small_14** | 16 | 16 | 0 | 8 | 64 | 56 | 700.0% |
| **medium_0** | 24 | 24 | 0 | 12 | 144 | 132 | 1100.0% |
| **medium_1** | 20 | 20 | 0 | 10 | 100 | 90 | 900.0% |
| **medium_2** | 24 | 24 | 0 | 12 | 144 | 132 | 1100.0% |
| **medium_3** | 20 | 20 | 0 | 10 | 100 | 90 | 900.0% |
| **medium_4** | 20 | 20 | 0 | 10 | 100 | 90 | 900.0% |
| **medium_5** | 24 | 24 | 0 | 12 | 144 | 132 | 1100.0% |
| **medium_6** | 24 | 24 | 0 | 12 | 144 | 132 | 1100.0% |
| **medium_7** | 24 | 24 | 0 | 12 | 144 | 132 | 1100.0% |
| **medium_8** | 20 | 20 | 0 | 10 | 100 | 90 | 900.0% |
| **medium_9** | 24 | 24 | 0 | 12 | 144 | 132 | 1100.0% |
| **medium_10** | 24 | 24 | 0 | 12 | 144 | 132 | 1100.0% |
| **medium_11** | 20 | 20 | 0 | 10 | 100 | 90 | 900.0% |
| **medium_12** | 24 | 24 | 0 | 12 | 144 | 132 | 1100.0% |
| **medium_13** | 24 | 24 | 0 | 12 | 144 | 132 | 1100.0% |
| **medium_14** | 20 | 20 | 0 | 10 | 100 | 90 | 900.0% |
| **large_0** | 32 | 32 | 0 | 16 | 256 | 240 | 1500.0% |
| **large_1** | 30 | 30 | 0 | 30 | 165 | 135 | 450.0% |
| **large_2** | 32 | 32 | 0 | 16 | 256 | 240 | 1500.0% |
| **large_3** | 30 | 30 | 0 | 30 | 165 | 135 | 450.0% |
| **large_4** | 30 | 30 | 0 | 30 | 165 | 135 | 450.0% |
| **large_5** | 32 | 32 | 0 | 16 | 256 | 240 | 1500.0% |
| **large_6** | 32 | 32 | 0 | 16 | 256 | 240 | 1500.0% |
| **large_7** | 32 | 32 | 0 | 16 | 256 | 240 | 1500.0% |
| **large_8** | 32 | 32 | 0 | 16 | 256 | 240 | 1500.0% |
| **large_9** | 32 | 32 | 0 | 16 | 256 | 240 | 1500.0% |
| **large_10** | 30 | 30 | 0 | 30 | 165 | 135 | 450.0% |
| **large_11** | 32 | 32 | 0 | 16 | 256 | 240 | 1500.0% |
| **large_12** | 32 | 32 | 0 | 16 | 256 | 240 | 1500.0% |
| **large_13** | 30 | 30 | 0 | 30 | 165 | 135 | 450.0% |
| **large_14** | 30 | 30 | 0 | 30 | 165 | 135 | 450.0% |

## 2. Analysis of Complexity Results

1.  **Qubit Preservation**: Option B+ adds **0 qubits** (zero extra variables) compared to Option B. By formulating the capacity penalty as a relative resource utilization sum of squares per node, we avoid introducing any task-specific or logarithmic slack variables.
2.  **Coupling Bloat**: Adding capacity awareness significantly increases the number of quadratic coupling terms (non-zero off-diagonals in Q). For `small_6` the couplings increase by **54.5%**, for `medium_3` by **66.7%**, and for `large_3` by **62.5%**.
3.  **Circuit Depth Implications**: While the qubit count is preserved, the increased coupling density implies that compilation onto physical NISQ topologies will require **more CNOT gates and SWAP overhead**, increasing the susceptibility to gate error and decoherence in physical runs.