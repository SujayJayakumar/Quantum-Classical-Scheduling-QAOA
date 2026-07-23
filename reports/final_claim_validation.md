# Phase 7E: Final Claim Validation Report

This report presents the final scientific validation and sensitivity analysis of the quantum-classical scheduling campaign. It synthesizes the findings from Phase 7B (Sensitivity Sweeps), Phase 7C (Fair Baselines), Phase 7D (Set Overlaps), and Phase 7E (Query-Efficiency & Soft-Capacity Study).

---

## 1. Answers to Core Research Questions

### Q1. Is solver success primarily driven by instance structure?
**Yes.** The Jaccard similarity $J(\text{QAOA}, \text{SA}) = 1.0$ indicates that the solved window sets of the two stochastic solvers are identical. This demonstrates that feasibility is governed by the underlying optimization landscape of the trace window. If an instance has capacity-feasible configurations close to the unconstrained ground-state energy, both solvers find them; if not, both fail.

### Q2. Does QAOA provide unique feasible solutions?
**No.** There are no windows solved by QAOA that are not also solved by Simulated Annealing Multi-Restarts.

### Q3. Is query efficiency supported?
**No.** Although QAOA evaluates the objective function fewer times (83 vs. 5,000), Simulated Annealing matches QAOA's coverage at only **$R=5$ restarts** (with a trivial CPU runtime of 0.047 seconds per window). Under the established audit criteria, a budget of $R \le 10$ restarts to match QAOA requires us to reject the query-efficiency claim.

### Q4. Does adding lightweight capacity awareness (Option B+) materially change conclusions?
**No.** Under Option B+, the soft capacity penalty shifts the QUBO ground state so that exact optimization (via CP-SAT) successfully locates capacity-feasible mappings, increasing its feasibility rate. However, Simulated Annealing and QAOA also converge to feasible configurations, maintaining their parity. The primary impact of Option B+ is **circuit complexity** rather than solver hierarchy: it increases coupling density by **~60%**, which dramatically increases compile and entangling gate (CNOT) overhead on physical quantum processors.

### Q5. Which formulation should be presented as the main paper result?
**Option B (Main Text) + Option B+ (Sensitivity Appendix)**.
*   **Rationale**: Option B is the most viable formulation for NISQ-era quantum hardware because it preserves the lowest possible coupling density (minimizing entangling gate overhead). Option B+ should be presented in the appendix to show that capacity constraints can be integrated without adding qubits, but at the cost of a ~60% coupling bloat that degrades circuit depth.

---

## 2. Scientific Verdicts Summary

*   **Query-Efficiency Verdict**: **REJECTED**. The classical restart overhead to match QAOA is negligible (5 restarts, <50ms CPU time).
*   **Soft-Capacity Verdict**: **SATISFIED**. Option B+ successfully enforces capacity constraints without adding slack qubits, but introduces significant coupling density.
*   **Narrative Recommendation**: Frame the results as a study of **NISQ-tractable hybrid optimization-decoding models**, showing that QAOA achieves parity with classical SA multi-restarts under highly constrained qubit budgets, and discuss the coupling density trade-offs of capacity-aware QUBOs.
*   **Further Simulations**: **No additional simulations are necessary**. The 45-window results provide a statistically complete and scientifically honest picture for the paper draft.
