# Real-Window Complexity Impact Report

This report documents the complexity impact of the Option B QUBO reformulation on the representative frozen real-trace benchmark windows (`gpu_30` for Small, Medium, and Large).

---

## Benchmark Suite Complexity Comparison

| Bucket | Representative Window | Model | Variables | Non-Zero Q Entries | Hamiltonian Terms | Complexity Reduction % |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Small** | `gpu_30` | OLD | 15 | 60 | 60 | - |
| **Small** | `gpu_30` | NEW | 15 | 30 | 30 | **50.00%** |
| | | | | | | |
| **Medium** | `gpu_30` | OLD | 24 | 132 | 132 | - |
| **Medium** | `gpu_30` | NEW | 24 | 48 | 48 | **63.64%** |
| | | | | | | |
| **Large** | `gpu_30` | OLD | 30 | 195 | 195 | - |
| **Large** | `gpu_30` | NEW | 30 | 60 | 60 | **69.23%** |

---

## Analysis & Explanations

### 1. Why the Variable (Qubit) Count Did Not Change
In all real-trace benchmark windows, the variable and qubit count remained identical between the OLD and NEW models (15, 24, and 30 qubits respectively).
* **Explanation**: The candidate node reducer (Phase 5.8) pre-filters the available cluster nodes to a pool of 3 candidate nodes. These nodes are selected because they are GPU-type nodes (fully compatible with all job types) and have high capacities (128 CPUs, 4 GPUs) exceeding any individual job request. As a result, all jobs in the window are compatible with every candidate node in the pool. Therefore, no job-node pair variables are pruned during the `is_compatible` check.

### 2. Quantifying the Hamiltonian Complexity Reduction
Even though the number of qubits remains the same, the complexity of the quantum circuit represents a dramatic improvement:
* **Entangling Couplings (CNOT Gates)**:
  * For **Small (15 qubits)**: The number of Hamiltonian terms drops from 60 to 30. This removes **30 Z-Z quadratic terms**, saving **60 CNOT gates** per layers of QAOA.
  * For **Medium (24 qubits)**: Drops from 132 to 48. Removes **84 Z-Z quadratic terms**, saving **168 CNOT gates** per layer of QAOA.
  * For **Large (30 qubits)**: Drops from 195 to 60. Removes **135 Z-Z quadratic terms**, saving **270 CNOT gates** per layer of QAOA.
* **Optimization Benefits**: Removing these entangling interactions simplifies the parameter landscape for classical optimizers (like COBYLA) by eliminating large quadratic penalty valleys, allowing for faster convergence in fewer function evaluations.
