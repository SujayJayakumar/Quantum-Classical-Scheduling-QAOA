# QUBO Reformulation Report (Option B)

This report documents the implementation of Option B (feasibility-only constraints + variable pruning) in `qubo_builder.py` and its impact on variable counts.

---

## Key Changes in `qubo_builder.py`

1. **Removed Capacity Penalty**:
   * Removed all quadratic capacity penalty calculations and terms from the Q matrix.
   * Keeps `alpha_capacity` parameter for signature compatibility but sets capacity term counts to `0` in metadata.
2. **Added Variable Pruning**:
   * Added `is_compatible(job, node)` check verifying GPU requirements, GPU node type, and node capacity limits.
   * In [qubo_builder.py](file:///home/sim/Desktop/Quantum/src/qubo_builder.py#L132), variables are created *only* for compatible job-node pairs.
3. **Variable-Map-Driven QUBO Building**:
   * Modified objective and assignment uniqueness penalty loops to iterate over active compatible variables instead of assuming a full job-node grid.

---

## Variable Count Impact Study

The following table reports the variable counts before and after pruning:

### Toy Instances

| Toy Instance | Jobs | Nodes | Variables Before | Variables After | Variable Reduction % | Incompatible Variables Pruned |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `2x2` | 2 | 2 | 4 | 3 | **25.0%** | `x(1,1)_j1_n1` (GPU job `j1` mapped to CPU node `n1`) |
| `3x2` | 3 | 2 | 6 | 5 | **16.7%** | `x(1,1)_j1_n1` (GPU job `j1` mapped to CPU node `n1`) |

### Frozen Benchmark Suite

| Bucket | Windows | Jobs | Nodes | Variables Before | Variables After | Variable Reduction % | Reason for 0% Reduction |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Small** | `gpu_30`, `mixed_30`, `mixed_20` | 5 | 3 | 15 | 15 | **0.0%** | Candidates pre-filtered to high-capacity GPU nodes |
| **Medium** | `gpu_30`, `mixed_30`, `mixed_20` | 8 | 3 | 24 | 24 | **0.0%** | Candidates pre-filtered to high-capacity GPU nodes |
| **Large** | `gpu_30`, `mixed_30`, `mixed_20` | 10 | 3 | 30 | 30 | **0.0%** | Candidates pre-filtered to high-capacity GPU nodes |

> [!NOTE]
> **Why Benchmark Windows have 0% variable reduction**:
> The candidate node reducer (Phase 5.8) pre-filters the available cluster nodes to a pool of 3 candidate nodes. These nodes are selected specifically because they are GPU-type nodes (compatible with all jobs) and have large individual capacities (128 CPUs, 4 GPUs) exceeding any individual job request. Consequently, every job in each window is compatible with all 3 candidate nodes in its pool.
