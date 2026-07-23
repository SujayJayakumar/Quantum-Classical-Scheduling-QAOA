# Repository Audit Report: Quantum-HPC Scheduling Pipeline

This report audits the current architecture, data model, and solver status of the research repository to verify it against the project goals and identify any inconsistencies or bugs.

---

## 1. Architectural Overview

The repository implements a **mapping-only hybrid scheduling pipeline** designed to compare classical solvers and Simulated Annealing against a CUDA-Q QAOA proof-of-concept. The scheduling problem is divided into two distinct parts:
1. **Spatial Mapping (QUBO / CP-SAT)**: Assigns jobs to compatible cluster nodes while respecting resource constraints (such as CPU, GPU, and compatibility).
2. **Temporal Scheduling (Classical Decoder)**: Takes the spatial mapping and schedules jobs sequentially on each node in release-time order using `decode_exclusive`.

This split keeps the QUBO size manageable ($O(J \times N)$ variables instead of $O(J \times N \times T)$), fitting within near-term quantum simulator budgets ($12\text{--}32$ qubits).

---

## 2. Key Audit Findings & Inconsistencies

We have identified several critical bugs, architectural inconsistencies, and performance bottlenecks:

### Finding A: State-Aware Window Node Slicing Bug (Critical blocker for Phase 5.8)
* **Location**: [state_aware_source_builder.py](file:///home/sim/Desktop/Quantum/src/state_aware_source_builder.py#L66)
* **Inconsistency**: In `build_window`, the list of candidate nodes is sliced to `nodes = nodes[:1]`. This leaves only a single node in the `"nodes"` list of the generated JSON files in [data/windows/state_aware_windows/](file:///home/sim/Desktop/Quantum/data/windows/state_aware_windows/).
* **Consequence**: The candidate node reducer [candidate_node_reducer.py](file:///home/sim/Desktop/Quantum/src/candidate_node_reducer.py#L202) rejects any window with fewer than 2 nodes:
  ```python
  if len(jobs) < 3 or len(nodes) < 2:
      return None
  ```
  Consequently, `reduce_window` returns `None` for all 9 windows. The candidate node reduction pipeline generates **0 windows** (manifesting as empty `small.json`, `medium.json`, and `large.json` files with `count: 0`), blocking the QAOA benchmark pipeline.
* **Secondary Effect**: The original scheduling pressure is computed incorrectly because it assumes the entire trace was run on a single node rather than the actual 100+ available nodes of the cluster.

### Finding B: CUDA-Q Solver `exp_pauli` Multi-Term Exception (Critical solver bug)
* **Location**: [qaoa_cudaq_solver.py](file:///home/sim/Desktop/Quantum/src/qaoa_cudaq_solver.py#L81)
* **Inconsistency**: The QAOA ansatz kernel attempts to exponentiate the entire multi-term Hamiltonian at once:
  ```python
  kernel.exp_pauli(2.0 * gamma, q_hamiltonian)
  ```
* **Consequence**: In CUDA-Q, `kernel.exp_pauli` only accepts a `SpinOperator` that consists of a *single* Pauli term. Passing the multi-term cost Hamiltonian causes a runtime crash:
  ```
  RuntimeError: error: exp_pauli operation requires a SpinOperator composed of a single term.
  ```
* **Fix**: The solver must loop over individual terms in `q_hamiltonian`, extract their active qubit targets (using `elem.target` for each element), build the appropriate Pauli string (e.g., `"ZIZ"`), extract the real coefficient of the term, and scale the parameter accordingly:
  ```python
  for term in q_hamiltonian:
      coeff = term.evaluate_coefficient().real
      pauli_list = ["I"] * n_qubits
      for elem in term:
          pauli_list[elem.target] = "Z"
      pauli_str = "".join(pauli_list)
      kernel.exp_pauli(2.0 * gamma * coeff, qubits, pauli_str)
  ```

### Finding C: Performance Bottleneck in State-Aware Window Builder
* **Location**: [state_aware_source_builder.py](file:///home/sim/Desktop/Quantum/src/state_aware_source_builder.py#L46)
* **Inconsistency**: `build_window` instantiates `NodeStateLoader(tolerance_minutes=60)` on every call (9 times). Each instantiation reads, parses, and sorts the 183MB `node_status.csv` file from disk.
* **Consequence**: This causes the window builder script to take almost 2 minutes to run.
* **Fix**: Instantiate `NodeStateLoader` once in `main()` and reuse it across all `build_window` calls, reducing execution time to a few seconds.

### Finding D: Capacity Constraint vs. Decoder Mismatch & Equality Constraint
* **Location**: [qubo_builder.py](file:///home/sim/Desktop/Quantum/src/qubo_builder.py#L226) and [real_trace_sa_benchmark.py](file:///home/sim/Desktop/Quantum/src/real_trace_sa_benchmark.py#L100)
* **Inconsistency 1**: The capacity penalty is modeled as `alpha_capacity * (sum_i cpu_i x_ij - cpu_cap_j)^2`. Since it lacks slack variables, it functions as an **equality** constraint, penalizing underloaded nodes.
* **Inconsistency 2**: The schedule decoder runs jobs **sequentially** on each node. Therefore, the *sum* of resources of all jobs assigned to a node can exceed capacity without causing a physical conflict (as long as each individual job fits).
* **Consequence**: To bypass this mismatch, the Simulated Annealing benchmark sets `alpha_capacity = 0.0`. However, the QAOA benchmark harness sets `alpha_capacity = 10.0`, which will severely distort QAOA optimizations on non-fully-packed nodes.

### Finding E: Stale Status Reports
* **Location**: [reports/phase58_status.md](file:///home/sim/Desktop/Quantum/reports/phase58_status.md) and [reports/quantum_solver_audit.md](file:///home/sim/Desktop/Quantum/reports/quantum_solver_audit.md)
* **Inconsistency**: These reports claim `qaoa_cudaq_solver.py` is absent, whereas the proof-of-concept script has been implemented (but currently crashes due to the `exp_pauli` bug).

---

## 3. Recommendation for Phase 5.8

 we recommend that Phase 5.8 **proceed with modifications**:
1. **Fix state-aware window generation**: Remove the `nodes = nodes[:1]` slice and optimize `NodeStateLoader` reuse.
2. **Rebuild the source and reduced windows**: Run the updated scripts to verify that `small`, `medium`, and `large` windows are correctly generated and validated (producing non-zero counts).
3. **Fix the CUDA-Q solver**: Implement the single-term Pauli term decomposition and parameter scaling in `qaoa_cudaq_solver.py` so that it runs successfully.
4. **Align `alpha_capacity` values**: Standardize `alpha_capacity = 0.0` or model proper individual compatibility in QUBO.
