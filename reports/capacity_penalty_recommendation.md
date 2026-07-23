# Capacity Penalty Reformulation Report

This report evaluates and compares three options for reformulating the capacity penalty constraint (`alpha_capacity`) in the QUBO model.

---

## CONTEXT & CURRENT FORMULATION

The current QUBO formulation implements a sum-based capacity penalty:
$$H_{\text{capacity}} = \alpha_{\text{capacity}} \sum_{j} \left( \sum_{i} \text{cpu\_req}_{i} x_{ij} - \text{cpu\_capacity}_{j} \right)^2$$
This term penalizes the mapping if the sum of CPU requests of all jobs mapped to node $j$ exceeds the node's capacity.

However, the decoder (`src/schedule_decoder.py`) uses a sequential exclusive scheduling model (`decode_exclusive`), running jobs on each node one by one. Since jobs do not execute concurrently, the cumulative resource demand is irrelevant. The only physical constraint is that **each individual job must fit on its assigned node**.

---

## EVALUATION OF OPTIONS

### Option A: Remove `alpha_capacity` entirely
*   **Description**: Remove the capacity penalty term from the QUBO.
*   **CP-SAT assumptions**: CP-SAT enforces strict resource capacities. If capacity penalties are removed from the QUBO, the solvers optimize different problems, breaking the validity of CP-SAT vs. QAOA comparison.
*   **SA assumptions**: Simulated Annealing will assign all jobs to the single fastest node to minimize the execution time objective, leading to massive resource overloading.
*   **Decoder assumptions**: The decoder will accept the overloaded mapping but will schedule jobs that exceed the physical capacity of the node (e.g., mapping a job requiring 128 cores to a 64-core node), which is physically impossible.
*   **QAOA implications**: Reduces qubit gate counts, but yields physically infeasible scheduling solutions.

### Option B: Replace with feasibility-only penalties
*   **Description**: Enforce only that the resource requirement of each individual job does not exceed the capacity of the node to which it is mapped:
    $$H_{\text{feasibility}} = \sum_{i, j} P_{ij} x_{ij}$$
    where $P_{ij} = \beta$ (a large penalty weight) if $\text{cpu\_req}_{i} > \text{cpu\_capacity}_{j}$ or $\text{gpu\_req}_{i} > \text{gpu\_capacity}_{j}$, and $0$ otherwise.
*   **CP-SAT assumptions**: Aligns with CP-SAT's requirement that jobs must be placed on compatible/feasible nodes.
*   **Decoder assumptions**: Aligns perfectly. Since the decoder is sequential, any mapping where every job fits its node individually is a physically valid schedule.
*   **SA assumptions**: Since the penalty is a single-variable term, it only adds to the diagonal of the $Q$ matrix. SA will easily find feasible mappings.
*   **QAOA implications**: **Extremely beneficial.** The feasibility term is linear ($x_{ij}^2 = x_{ij}$), which eliminates all quadratic (off-diagonal) capacity terms from the $Q$ matrix. This reduces the number of two-qubit (CNOT) gates in the QAOA ansatz, improving gate fidelity and reducing circuit depth—critical for NISQ-era simulation and execution.
*   **Variable Pruning**: We can prune variables $x_{ij}$ for infeasible pairs, directly reducing the number of qubits.

### Option C: Introduce a proper inequality formulation
*   **Description**: Formulate the capacity constraint as an inequality $\sum_{i} \text{cpu\_req}_{i} x_{ij} \le C_j$ using slack variables.
*   **Inequality in QUBO**: Requires introducing slack variables:
    $$\sum_{i} \text{cpu\_req}_{i} x_{ij} + \sum_{k=0}^{M} 2^k s_k = C_j$$
    where $s_k$ are auxiliary binary variables.
*   **CP-SAT assumptions**: Matches CP-SAT's inequality capacity constraints.
*   **Decoder assumptions**: Over-constrained because the decoder does not execute jobs concurrently, so a sum-of-demands capacity inequality is physically unnecessary.
*   **SA assumptions**: The energy landscape becomes significantly larger and more difficult to optimize due to slack variables.
*   **QAOA implications**: **Highly detrimental.** Adding slack variables increases the qubit count by $O(K \log(C_j))$ qubits. For a 128-core node, we need 7-8 extra qubits per node. This would explode the qubit requirement, making the problem too large for NISQ computers.

---

## COMPARATIVE SUMMARY

| Metric / Aspect | Option A (Remove) | Option B (Feasibility-Only) | Option C (Inequality) |
| :--- | :---: | :---: | :---: |
| **Physical Correctness** | No | **Yes** (Sequential) | Yes (Concurrent) |
| **Decoder Alignment** | No | **Yes** | No (Over-constrained) |
| **QUBO Variable Overhead**| None | **None** | High (Slack variables) |
| **QAOA Gate Count** | Low | **Low** (No quadratic terms) | Very High |
| **Solving Difficulty** | Low | **Low** | High |
| **Hardware Feasibility** | High | **High** | Very Low |

---

## FINAL RECOMMENDATION

We recommend **Option B: Feasibility-Only Penalties** (combined with **Variable Pruning**).

### Scientific Justification
1.  **Decoder Alignment**: The sequential exclusive decoder (`decode_exclusive`) schedules jobs one by one. Thus, there is no resource sharing over time, and a mapping is physically valid as long as each job can run on its node individually. 
2.  **Quantum Hardware Efficiency**: Option B eliminates the quadratic capacity terms from the QUBO, removing the need for corresponding two-qubit entangling gates in the QAOA circuit. Furthermore, by pruning the variables $x_{ij}$ where job $i$ cannot fit on node $j$ (Variable Pruning), we directly reduce the number of qubits required, maximizing the feasibility of running QAOA on NISQ hardware.
3.  **Optimization Landscape**: Removing unnecessary quadratic penalties simplifies the energy landscape, enabling both classical heuristic solvers (SA) and quantum solvers (QAOA) to find optimal solutions more efficiently.
