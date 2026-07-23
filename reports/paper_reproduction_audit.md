# Paper-to-Code Mapping Audit

This report analyzes how closely the current repository reproduces the reference QUBO-based HPC/workflow scheduling paper. It maps the paper's mathematical components and methodology to the implementation.

## Audit of Components

### 1. Assignment Constraint
* **Classification**: `IMPLEMENTED`
* **Source File**: `src/qubo_builder.py` (Section B, Assignment uniqueness penalty)
* **Deviation**: None. The standard $\alpha (1 - \sum x_{ij})^2$ penalty is used to ensure each job is mapped to exactly one node.

### 2. Capacity Constraint
* **Classification**: `IMPLEMENTED`
* **Source File**: `src/qubo_builder.py` (Section C, Capacity penalties)
* **Deviation**: Expanded. Instead of a single generic resource, the implementation explicitly models both `CPU` and `GPU` capacities as separate penalty terms. This is an intentional extension to handle real heterogeneous cluster architectures.

### 3. Compatibility Constraint
* **Classification**: `IMPLEMENTED`
* **Source File**: `src/qubo_builder.py` (`gpu_compatibility_penalty`)
* **Deviation**: Adapted for GPUs. The implementation explicitly penalizes assigning GPU-requiring jobs to CPU-only nodes. This is an intentional domain-specific adaptation.

### 4. Communication Cost Term
* **Classification**: `NOT IMPLEMENTED`
* **Source File**: Listed under `excluded_terms` in `src/qubo_builder.py` metadata.
* **Deviation**: Excluded. Intentional deviation. To keep variable counts feasible for near-term quantum hardware (and the 12-32 qubit QAOA budgets), the model prioritizes spatial mapping without interconnect-aware communication terms.

### 5. Dependency Term
* **Classification**: `NOT IMPLEMENTED`
* **Source File**: Listed under `excluded_terms` in `src/qubo_builder.py` metadata.
* **Deviation**: Excluded. Intentional deviation. Currently focusing on independent batch HPC jobs rather than strictly dependent tasks.

### 6. Workflow/DAG Constraints
* **Classification**: `NOT IMPLEMENTED`
* **Source File**: N/A
* **Deviation**: Excluded. The repository handles jobs from real PBS traces (`merged_all_jobs.jsonl`). Complex workflow DAG topologies from the reference paper are not currently modeled.

### 7. QUBO Formulation
* **Classification**: `MODIFIED`
* **Source File**: `src/qubo_builder.py`, `src/schedule_decoder.py`
* **Deviation**: Highly modified. The paper likely formulates a joint optimization of spatial assignment and temporal scheduling (start times/time bins). This implementation explicitly uses a **mapping-only QUBO**. The QUBO handles the NP-hard spatial assignment (job-to-node), while temporal scheduling is relegated to a deterministic classical decoder (`decode_exclusive`).
* **Intentionality**: Yes. Joint space-time QUBOs require $O(J \times N \times T)$ variables, which is impossible to simulate on QAOA. The spatial-only abstraction is required to fit the problem into $<32$ qubits.

### 8. Simulated Annealing Solver
* **Classification**: `IMPLEMENTED`
* **Source File**: `src/qubo_sa_solver.py`, `src/real_trace_sa_benchmark.py`
* **Deviation**: None. The pipeline successfully executes the SA solver on the generated QUBOs as a classical heuristic baseline.

### 9. Benchmark Methodology
* **Classification**: `MODIFIED`
* **Source File**: `src/real_trace_sa_benchmark.py`, `src/cp_sat_mapping_baseline.py`
* **Deviation**: Massively extended and improved. 
  1. Instead of synthetic data, it uses real HPC PBS traces sliced into state-aware windows.
  2. It introduces a rigorous, exact classical ground truth (`CP-SAT`) to evaluate the QUBO formulations, checking both makespan gaps and assignment overlap.
* **Intentionality**: Yes. This elevates the scientific rigor of the paper's original methodology, moving from synthetic PoC to real-world viability testing.

## Conclusion

Based on this audit, we are:

**(B) Building a different scheduling formulation inspired by the paper.**

While the core QUBO mapping constraints (assignment, capacity) are directly reproduced, the repository fundamentally alters the architecture of the problem. By dropping DAG/communication constraints, dropping the temporal dimension from the QUBO, and pairing a mapping-only QUBO with a classical schedule decoder, this project is designing a **hybrid QAOA-ready heuristic**, rather than strictly reproducing the original joint-scheduling paper. 

This deviation is scientifically defensible and necessary given the strict `<32` qubit budget limitations of current QAOA simulators and hardware.