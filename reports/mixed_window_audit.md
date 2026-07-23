# Mixed Window Audit Report

This report audits the candidate node selection in mixed workload windows and investigates why they are restricted to GPU nodes.

---

## AUDIT ANALYSIS & FINDINGS

### 1. Is this behavior intentional?
**Yes.** In the source builder script [state_aware_source_builder.py](file:///home/sim/Desktop/Quantum/src/state_aware_source_builder.py), the code checks if any job in the window requires a GPU. If it does, the candidate node pool is restricted to available GPU nodes:
```python
has_gpu = any(job_is_gpu(job) for job in jobs)
if has_gpu:
    node_ids = cluster_state["available_gpu_nodes"] or cluster_state["busy_nodes"]
else:
    node_ids = cluster_state["available_cpu_nodes"] or cluster_state["busy_nodes"]
```
Since mixed windows consist of both CPU-only and GPU-requesting jobs, `has_gpu` evaluates to `True`, forcing the selection of available GPU nodes only.

### 2. Is this caused by compatibility filtering?
**Yes.** This restriction acts as a coarse-grained compatibility filter. Because GPU-requesting jobs cannot run on CPU-only nodes, but CPU jobs can run on GPU nodes (which possess standard CPU cores), selecting only GPU nodes guarantees that every node in the pool is compatible with every job in the window. 

If the candidate node set included CPU-only nodes, a GPU-requesting job could be mapped to a CPU-only node by a solver, which would violate physical GPU resource constraints. This simple "GPU-only node pool" constraint avoids having to enforce more complex job-node type-compatibility penalties or constraints during mapping, but at a high cost to system efficiency.

### 3. Are CPU-only jobs prevented from using CPU nodes?
**Yes.** In the generated candidate pool, CPU-only nodes are completely excluded. In the final QUBO variables, there are no variables representing the mapping of CPU-only jobs to CPU nodes. As a result, CPU-only jobs are restricted to running on GPU nodes and are prevented from utilizing the available CPU nodes in the cluster.

### 4. Does this artificially reduce the search space?
**Yes, significantly.**
1.  **Node Pool Shrinkage**: In the active cluster snapshot, there are **116 available CPU nodes** and only **3 available GPU nodes**. By restricting the pool to GPU nodes, the candidate node space for mixed windows is reduced from 119 nodes to just 3 nodes.
2.  **Resource Contention**: CPU-only jobs (which are numerous) are forced to compete with GPU-requiring jobs for resources on the 3 scarce GPU nodes. This increases local contention metrics artificially.
3.  **Large Bucket Generation Obstruction**: Because the pool is restricted to 3 nodes, the reducer cannot select 4 or 5 nodes for a Large budget window, which originally led to 0 Large windows being generated. Capping the target node size (Task 1) recovered these windows, but the candidate node count remains limited to 3.

---

## CONCRETE EXAMPLE: `mixed_30`

Let's examine the source state-aware window file `mixed_30_8.json`:

*   **Total Jobs**: 30
    *   **GPU Jobs**: 8 jobs (e.g., job `205615.champ1` requiring 128 CPUs and 4 GPUs; job `205620.champ1` requiring 4 CPUs and 1 GPU)
    *   **CPU Jobs**: 22 jobs (e.g., job `205613.champ1` requiring 8 CPUs and 0 GPUs)
*   **Original Candidate Nodes**: 3 nodes (all of type `gpu`)
    *   `r04gn05` (128 CPUs, 4 GPUs)
    *   `r04gn06` (128 CPUs, 4 GPUs)
    *   `r05gn04` (128 CPUs, 4 GPUs)

### Impact
The 22 CPU-only jobs are mapped exclusively to `r04gn05`, `r04gn06`, and `r05gn04`. They cannot utilize any of the 116 available CPU nodes, which are idle in this snapshot. This represents a substantial artificial reduction of the scheduling search space.
