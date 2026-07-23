# Phase 5.8 Audit: Candidate Node Reduction Pipeline

This report audits the existing `candidate_node_reducer.py` and `reduction_validator.py` scripts.

## 1. Reduction Strategy

The implemented strategy is a sophisticated heuristic search, not a simple random sampling. It aims to find small, but highly contentious, scheduling problems that are suitable for quantum solvers.

The process is as follows:

1.  **Job Sub-setting**: The script iterates through all possible contiguous subsets of jobs (sorted by submit time) that fit within the size constraints (`min_jobs`, `max_jobs`) of the target quantum budget (Small, Medium, Large).
2.  **Node Scoring**: For each job subset, it scores all available cluster nodes using a `node_similarity_score`. This score prioritizes nodes that are:
    *   **Available**: Nodes marked as "available" in the cluster state snapshot receive a higher score.
    *   **Historically Relevant**: Nodes where jobs from the window were historically allocated are preferred.
    *   **Type-Compatible**: GPU nodes are preferred for GPU-requiring job sets.
3.  **Node Selection**: The top-scoring nodes are selected to form the candidate node set for that job subset.
4.  **Budget & Feasibility Check**: The script calculates the required qubits (`jobs` x `nodes`) and ensures the number is within the `target_bounds` for the specified budget. It also ensures that the resulting problem is feasible (i.e., every job can be placed on at least one node in the candidate set).
5.  **Best Window Selection**: Among all valid (job subset, node subset) combinations, the script selects the one that maximizes a `selection_score` based on CPU pressure, GPU pressure, and job density. This actively seeks out the most resource-constrained sub-problems.

## 2. Preservation of Scheduling Characteristics

*   **CPU/GPU Pressure & Contention**: The reducer does more than preserve pressure; it actively **concentrates** it. By selecting for high pressure and density within a much smaller node pool, the resulting reduced windows often have higher pressure ratios than the original, larger window, creating a challenging scheduling problem.
*   **Feasibility**: The process guarantees that every job in the reduced window has at least one feasible candidate node. This is explicitly checked by `reduction_validator.py`.
*   **Connection to Real Data**: The pipeline remains strongly connected to the source data.
    *   **Real Jobs**: Jobs are taken directly from the real trace windows.
    *   **Real Cluster State**: The reducer uses the `cluster_state` snapshot (available/busy nodes) from the state-aware window to inform its node scoring, grounding the decision in a realistic view of the cluster at that time.
    *   **Real Constraints**: It correctly uses the `cpu_req`, `gpu_req` of jobs and the `cpu_capacity`, `gpu_capacity` of nodes.

## Conclusion

The existing reduction pipeline is robust and scientifically sound. It correctly translates large, state-aware scheduling windows into small, high-conflict, quantum-ready problem instances. The `reduction_validator.py` script provides an essential cross-check to guarantee the integrity of the output.