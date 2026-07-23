# Benchmark Validity Audit Report

This report audits the validity of the progressive benchmarks under the Option B QUBO formulation (feasibility pruning). It analyzes constraints, objectives, and solver assignments for all 9 frozen benchmark windows to identify the root causes of heuristic infeasibility and zero-makespan anomalies.

---

## 1. Feasibility and Violation Audit Table

For each window and solver, we report: the solver's internal model feasibility, the validated feasibility (which enforces capacity limits), and the exact count of violations.
Note: **Dup** = Duplicate-Assignment Violations, **Miss** = Missing-Job Violations, **Compat** = GPU Compatibility Violations, **Uniq** = Assignment Uniqueness Violations, **CPU Cap** = CPU Capacity Violations, **GPU Cap** = GPU Capacity Violations.

| Window | Solver | Model Feasible | Validator Feasible | Uniq | Compat | Miss | Dup | CPU Cap | GPU Cap |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `small_gpu_30` | **CP-SAT** | True | False | 0 | 0 | 0 | 0 | 1 | 1 |
| `small_gpu_30` | **SA** | False | False | 0 | 0 | 0 | 0 | 2 | 2 |
| `small_gpu_30` | **QAOA** | False | False | 0 | 0 | 0 | 0 | 2 | 2 |
| `small_mixed_30` | **CP-SAT** | True | False | 0 | 0 | 0 | 0 | 1 | 1 |
| `small_mixed_30` | **SA** | False | False | 0 | 0 | 0 | 0 | 1 | 0 |
| `small_mixed_30` | **QAOA** | False | False | 0 | 0 | 0 | 0 | 1 | 0 |
| `small_mixed_20` | **CP-SAT** | True | False | 0 | 0 | 0 | 0 | 1 | 1 |
| `small_mixed_20` | **SA** | False | False | 0 | 0 | 0 | 0 | 1 | 0 |
| `small_mixed_20` | **QAOA** | False | False | 0 | 0 | 0 | 0 | 1 | 0 |
| `medium_gpu_30` | **CP-SAT** | True | False | 0 | 0 | 0 | 0 | 1 | 1 |
| `medium_gpu_30` | **SA** | False | False | 0 | 0 | 0 | 0 | 3 | 3 |
| `medium_gpu_30` | **QAOA** | False | False | 0 | 0 | 0 | 0 | 3 | 3 |
| `medium_mixed_30` | **CP-SAT** | True | False | 0 | 0 | 0 | 0 | 1 | 1 |
| `medium_mixed_30` | **SA** | False | False | 0 | 0 | 0 | 0 | 2 | 0 |
| `medium_mixed_30` | **QAOA** | Not Run | Not Run | N/A | N/A | N/A | N/A | N/A | N/A |
| `medium_mixed_20` | **CP-SAT** | True | False | 0 | 0 | 0 | 0 | 1 | 1 |
| `medium_mixed_20` | **SA** | False | False | 0 | 0 | 0 | 0 | 1 | 0 |
| `medium_mixed_20` | **QAOA** | Not Run | Not Run | N/A | N/A | N/A | N/A | N/A | N/A |
| `large_gpu_30` | **CP-SAT** | True | False | 0 | 0 | 0 | 0 | 1 | 1 |
| `large_gpu_30` | **SA** | False | False | 0 | 0 | 0 | 0 | 3 | 3 |
| `large_gpu_30` | **QAOA** | Deferred | Deferred | Deferred | Deferred | Deferred | Deferred | Deferred | Deferred |
| `large_mixed_30` | **CP-SAT** | True | False | 0 | 0 | 0 | 0 | 1 | 1 |
| `large_mixed_30` | **SA** | False | False | 0 | 0 | 0 | 0 | 2 | 1 |
| `large_mixed_30` | **QAOA** | Not Run | Not Run | N/A | N/A | N/A | N/A | N/A | N/A |
| `large_mixed_20` | **CP-SAT** | True | False | 0 | 0 | 0 | 0 | 1 | 1 |
| `large_mixed_20` | **SA** | False | False | 0 | 0 | 0 | 0 | 2 | 0 |
| `large_mixed_20` | **QAOA** | Not Run | Not Run | N/A | N/A | N/A | N/A | N/A | N/A |

## 2. QUBO Energy Components Audit Table

This table details the energy contributions for each solver assignment: the assignment uniqueness penalty contribution, the surrogate objective contribution, and the total QUBO energy ($E_{\text{QUBO}} = E_{\text{assign}} + E_{\text{objective}}$).

| Window | Solver | Assignment Penalty | Objective Contribution | Total QUBO Energy |
| :--- | :--- | :---: | :---: | :---: |
| `small_gpu_30` | **CP-SAT** | 0.0 | 0.0000 | -50.0000 |
| `small_gpu_30` | **SA** | 0.0 | 0.0000 | -50.0000 |
| `small_gpu_30` | **QAOA** | 0.0 | 0.0000 | -50.0000 |
| `small_mixed_30` | **CP-SAT** | 0.0 | 0.0000 | -50.0000 |
| `small_mixed_30` | **SA** | 0.0 | 0.0000 | -50.0000 |
| `small_mixed_30` | **QAOA** | 0.0 | 0.0000 | -50.0000 |
| `small_mixed_20` | **CP-SAT** | 0.0 | 0.0000 | -50.0000 |
| `small_mixed_20` | **SA** | 0.0 | 0.0000 | -50.0000 |
| `small_mixed_20` | **QAOA** | 0.0 | 0.0000 | -50.0000 |
| `medium_gpu_30` | **CP-SAT** | 0.0 | 0.0000 | -80.0000 |
| `medium_gpu_30` | **SA** | 0.0 | 0.0000 | -80.0000 |
| `medium_gpu_30` | **QAOA** | 0.0 | 0.0000 | -80.0000 |
| `medium_mixed_30` | **CP-SAT** | 0.0 | 0.0000 | -80.0000 |
| `medium_mixed_30` | **SA** | 0.0 | 0.0000 | -80.0000 |
| `medium_mixed_30` | **QAOA** | N/A | N/A | N/A |
| `medium_mixed_20` | **CP-SAT** | 0.0 | 0.0000 | -80.0000 |
| `medium_mixed_20` | **SA** | 0.0 | 0.0000 | -80.0000 |
| `medium_mixed_20` | **QAOA** | N/A | N/A | N/A |
| `large_gpu_30` | **CP-SAT** | 0.0 | 0.0000 | -100.0000 |
| `large_gpu_30` | **SA** | 0.0 | 0.0000 | -100.0000 |
| `large_gpu_30` | **QAOA** | Deferred | Deferred | Deferred |
| `large_mixed_30` | **CP-SAT** | 0.0 | 0.0000 | -100.0000 |
| `large_mixed_30` | **SA** | 0.0 | 0.0000 | -100.0000 |
| `large_mixed_30` | **QAOA** | N/A | N/A | N/A |
| `large_mixed_20` | **CP-SAT** | 0.0 | 0.0000 | -100.0000 |
| `large_mixed_20` | **SA** | 0.0 | 0.0000 | -100.0000 |
| `large_mixed_20` | **QAOA** | N/A | N/A | N/A |

---

## 3. Audit Diagnostics and Findings

Based on the tables above, we address the four potential system behaviors:

### A) Are assignment penalties too weak?
**NO**. The assignment uniqueness penalty is fully satisfied (0 uniqueness, missing-job, or duplicate-assignment violations) for all completed CP-SAT, SA, and QAOA assignments. The penalty coefficient ($\alpha_{\text{assign}} = 10.0$) is sufficiently strong to enforce uniqueness constraints.

### B) Is feasibility filtering not working / Evaluated Inconsistently?
**YES**. Feasibility filtering in the benchmark script is evaluated **inconsistently** between the baseline and the heuristics:
1. **CP-SAT Feasibility**: Evaluated using CP-SAT's model status (`feasible = True`), which only checks if the model's constraints are satisfied. Because capacity constraints were completely removed from the model under the Option B reformulation, CP-SAT trivially solves the mapping (placing all jobs on a single node) and reports `feasible = True`.
2. **SA and QAOA Feasibility**: Checked using `validate_assignment`, which enforces actual node CPU and GPU capacities. Since the heuristics place jobs on nodes without capacity knowledge (violating node limits), they are correctly flagged as `feasible = False`.
3. **Inconsistency**: If CP-SAT's assignments were run through the validator, they would also return `valid = False` due to severe capacity violations (e.g. using 1156 CPU on a node with 128 capacity). Thus, CP-SAT's reported 100% feasibility is a baseline evaluation error.

### C) Are decoded assignments being evaluated incorrectly?
**YES**. Under the Option B QUBO reformulation, node capacity penalties were completely removed from the QUBO builder. Consequently, the solvers (SA and QAOA) have no mathematical mechanism to penalize overloading. In addition, the surrogate objective runtime cost for all jobs in the frozen benchmark dataset is **0.00%** (see below). Therefore, the solvers simply return arbitrary unique assignments to compatible nodes, leading to capacity violations.

### D) Are benchmark reports treating invalid schedules as makespan=0?
**YES**. The schedule decoder (`decode_exclusive`) uses `estimated_runtime_seconds` of the jobs to construct the makespan. However, in the frozen benchmark dataset (`small.json`, `medium.json`, `large.json`), all jobs have `estimated_runtime_seconds = 0`. As a result, the makespan is mathematically decoded as **0s** for every single solver assignment, regardless of whether the schedule is valid or invalid. The reports treat invalid schedules as having a makespan of 0 because the jobs themselves have zero duration.

---

## 4. Key Takeaways and Path Forward

1. **Objective Cost Degeneracy**: Because all jobs in the frozen benchmark dataset have an estimated runtime of 0, the QUBO objective terms are completely zero. The QUBO matrix is purely comprised of assignment uniqueness penalties, leading to a flat, degenerate optimization landscape. All unique assignments have the exact same ground-state energy (e.g. $-50.0$ for Small).
2. **Capacity Penalty Restorations**: To resolve heuristic infeasibility, node capacity penalties must be restored to the QUBO builder, or a capacity-aware post-solver decoder must be implemented to partition job assignments.
3. **Dataset Re-Generation Required**: To enable makespan and objective-cost evaluation, the benchmark windows must be regenerated to populate the `estimated_runtime_seconds` field with the actual/estimated walltimes from the raw dataset, which are non-zero.