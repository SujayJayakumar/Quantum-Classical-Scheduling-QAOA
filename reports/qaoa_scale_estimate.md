# QAOA Scale and Feasibility Estimate

This report details the dimensions, estimated qubit counts, statevector memory requirements, and runtime safety classifications for every window in the frozen benchmark suite.

---

## Frozen Benchmark Scale Statistics

Memory requirements are calculated assuming double precision complex numbers (`complex128`, 16 bytes per amplitude): $\text{Memory} = 2^N \times 16 \text{ bytes}$.

| Bucket | Window | Jobs | Candidate Nodes | Variables | Q Matrix Dim | Estimated Qubits | Estimated Memory | Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Small** | `gpu_30` | 5 | 3 | 15 | 15x15 | 15 | 0.50 MB | **LAPTOP_SAFE** |
| **Small** | `mixed_30` | 5 | 3 | 15 | 15x15 | 15 | 0.50 MB | **LAPTOP_SAFE** |
| **Small** | `mixed_20` | 5 | 3 | 15 | 15x15 | 15 | 0.50 MB | **LAPTOP_SAFE** |
| **Medium** | `gpu_30` | 8 | 3 | 24 | 24x24 | 24 | 256.00 MB | **LAPTOP_SAFE** |
| **Medium** | `mixed_30` | 8 | 3 | 24 | 24x24 | 24 | 256.00 MB | **LAPTOP_SAFE** |
| **Medium** | `mixed_20` | 8 | 3 | 24 | 24x24 | 24 | 256.00 MB | **LAPTOP_SAFE** |
| **Large** | `gpu_30` | 10 | 3 | 30 | 30x30 | 30 | 16.00 GB | **A100_SAFE** |
| **Large** | `mixed_30` | 10 | 3 | 30 | 30x30 | 30 | 16.00 GB | **A100_SAFE** |
| **Large** | `mixed_20` | 10 | 3 | 30 | 30x30 | 30 | 16.00 GB | **A100_SAFE** |

---

## Classification Definitions
*   **LAPTOP_SAFE**: $\le 25$ qubits, $< 512 \text{ MB}$ memory. Executable on any standard laptop CPU simulator in a few seconds.
*   **A100_SAFE**: $26 - 32$ qubits, $512 \text{ MB} - 64 \text{ GB}$ memory. Executable on CPU/GPU accelerators or high-memory instances. Runs efficiently on local A100.
*   **TOO_LARGE**: $> 32$ qubits, $> 64 \text{ GB}$ memory. Exceeds standard single-node simulation boundaries.
