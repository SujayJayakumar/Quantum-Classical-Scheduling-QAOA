# Large Bucket Recovery Report

This report documents the recovery of the Large budget windows in the candidate node reduction pipeline.

---

## RECOVERY STATISTICS

*   **Previous Large Count**: 0 windows
*   **New Large Count**: 3 windows
*   **Recovered Windows**:
    1.  `gpu_30` (30 variables / qubits)
    2.  `mixed_30` (30 variables / qubits)
    3.  `mixed_20` (30 variables / qubits)

---

## RECOVERY METHODOLOGY

### The Problem
Previously, the candidate reducer requested a fixed number of target nodes for the Large budget (specifically 4 or 5 nodes). However, in the cluster state snapshots corresponding to the GPU and Mixed workload windows, only 3 GPU nodes were available. Because the reducer attempted to select 4 or 5 nodes from a pool of only 3 available nodes, the validation suite rejected them (`Reduced candidate set is larger than original state-aware node set`). CPU-only windows were skipped because they contain no GPU-requiring jobs.

### The Solution: Capped Node Counts & Dynamic Job Subsets
To resolve this, we modified the reduction logic in [candidate_node_reducer.py](file:///home/sim/Desktop/Quantum/src/candidate_node_reducer.py):

1.  **Capping Node Sizes**: We cap the requested target node counts to the size of the original candidate node pool of the window:
    ```python
    node_counts = [min(nc, orig_node_count) for nc in node_counts]
    node_counts = sorted(list(set(node_counts)))
    ```
    For GPU and Mixed windows, this caps the target node count for Large to exactly `3` nodes.

2.  **Dynamic Job Subset Sizing**: If the node count is reduced, the job subset size ($N$) must be increased to ensure that the resulting qubit count ($N \times M$) still falls within the budget target bounds ($[lo, hi]$). We compute the valid range of job subset sizes dynamically for each node count:
    ```python
    min_size = (lo + node_count - 1) // node_count
    max_size = hi // node_count
    ```
    For the Large budget ($lo=25, hi=32$) and $M=3$ nodes:
    *   $\text{min\_size} = \lceil 25 / 3 \rceil = 9$ jobs
    *   $\text{max\_size} = \lfloor 32 / 3 \rfloor = 10$ jobs

    The reducer iterates over job sizes of 9 and 10. For each of the three windows, a job count of 10 was selected as it maximizes the selection score and estimated qubits, resulting in exactly $10 \text{ jobs} \times 3 \text{ nodes} = 30 \text{ qubits}$ (which fits perfectly inside the Large budget of 25–32 qubits).
