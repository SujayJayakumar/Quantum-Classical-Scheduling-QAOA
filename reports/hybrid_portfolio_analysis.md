# Phase 7D Audit: Hybrid Portfolio Analysis & Scientific Interpretation

This report evaluates hypothetical hybrid portfolio solvers combining CP-SAT, Simulated Annealing (SA), and QAOA, and discusses the scientific implications of their overlapping success profiles.

---

## 1. Hypothetical Portfolio Performance

We evaluate three hybrid portfolio solvers. A portfolio is defined as successful on a window if **at least one** of its constituent solvers discovers a capacity-feasible schedule.

### Portfolio A: QAOA $\lor$ SA
*   **Constituent Solvers**: QAOA (Selected State), Simulated Annealing Multi-Restarts (100 trials)
*   **Windows Solved**: **4** (`small_6`, `medium_3`, `large_1`, `large_3`)
*   **Feasibility Rate**: $4 / 15 =$ **26.7%**
*   **Marginal Gain**: **0 additional windows** (neither solver expands the solved set of the other, since both solve the identical set of 4 windows).

### Portfolio B: QAOA $\lor$ CP-SAT
*   **Constituent Solvers**: QAOA (Selected State), CP-SAT Solution Pool (100 solutions)
*   **Windows Solved**: **4** (`small_6`, `medium_3`, `large_1`, `large_3`)
*   **Feasibility Rate**: $4 / 15 =$ **26.7%**
*   **Marginal Gain**: **1 additional window** recovered beyond CP-SAT individually (QAOA recovers `large_3`, which CP-SAT pool fails to solve).

### Portfolio C: QAOA $\lor$ SA $\lor$ CP-SAT
*   **Constituent Solvers**: QAOA, SA, and CP-SAT
*   **Windows Solved**: **4** (`small_6`, `medium_3`, `large_1`, `large_3`)
*   **Feasibility Rate**: $4 / 15 =$ **26.7%**
*   **Marginal Gain**: **0 additional windows** beyond the best individual solvers (QAOA and SA).

---

## 2. Solver Uniqueness and Contributions

*   **QAOA Unique Contribution**: **0 windows**. (QAOA does not solve any window that SA restarts fails to solve).
*   **SA Unique Contribution**: **0 windows**. (SA restarts does not solve any window that QAOA fails to solve).
*   **CP-SAT Unique Contribution**: **0 windows**. (CP-SAT pool does not solve any window that QAOA/SA fails to solve).

### Overlap Interpretation
Because QAOA and SA restarts solve the exact same subset of windows, **the success of these solvers is driven by the structural characteristics of the benchmark windows** rather than solver-specific exploration behaviors. 

Specifically, windows where both succeed possess capacity-feasible configurations that lie within the low-energy region of the unconstrained space (close to the ground state). In contrast, the 11 windows where both fail are structurally constrained such that any valid schedule is located at an energy level far above the unconstrained global minimum, rendering them inaccessible to both quantum and classical stochastic sampling on the unconstrained QUBO model.

---

## 3. Scientific Interpretation

We evaluate two possible scenarios for the interaction of our solvers:

*   **Scenario A (Supported by Data)**:
    *   *Definition*: QAOA and SA solve essentially the same windows.
    *   *Interpretation*: **Instance structure explains solver success.** The optimization landscape of the unconstrained QUBO is the dominant factor. Probabilistic/superposition sampling (QAOA and SA restarts) behave similarly in how they explore the low-energy subspace, finding feasible states when they are nearby and failing when they are not.
*   **Scenario B (Not Supported by Data)**:
    *   *Definition*: QAOA and SA solve different windows.
    *   *Interpretation*: Complementary search behavior exists. One solver is able to exploit specific landscape features that the other cannot.

### Conclusion:
**Our experimental results strongly support Scenario A.**
The Jaccard similarity $J(\text{QAOA}, \text{SA}) = 1.0$ indicates that QAOA and SA have identical window-level feasibility profiles. The scientific value of QAOA in this context is not that it searches a different mathematical subspace than SA, but rather that **it achieves parity with classical multi-restart Simulated Annealing using 1,200× fewer objective evaluations (83 vs. 100,000)**, demonstrating high query efficiency.
