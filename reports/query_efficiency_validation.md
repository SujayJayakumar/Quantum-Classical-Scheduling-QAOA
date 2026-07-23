# Phase 7E: Query-Efficiency Validation Report

This report evaluates the scientific validity of the query-efficiency claim for QAOA compared to Simulated Annealing (SA) Multi-Restarts.

---

## 1. Experimental Outcomes and Metrics

Based on the restart count sweep performed in Phase 7E:
*   **Minimum Sufficient SA Budget**: SA achieves the identical feasibility profile and solved window set as QAOA (`small_6`, `medium_3`, `large_1`, `large_3`) at **$R=5$ restarts**.
*   **Total Objective Evaluations (per window)**:
    *   **QAOA (p=1)**: **83.2 evaluations** (average iterations to convergence).
    *   **Simulated Annealing (R=5)**: $5 \times 1,000 = $ **5,000 evaluations**.
*   **Total Objective Evaluations (across all 15 windows)**:
    *   **QAOA (p=1)**: $83.2 \times 15 = $ **1,248 evaluations**.
    *   **Simulated Annealing (R=5)**: $5,000 \times 15 = $ **75,000 evaluations**.

---

## 2. Answers to Research Questions

### A. Does QAOA achieve the same success rate with fewer objective evaluations?
**Yes.** QAOA achieves a 26.7% feasibility rate (4/15 windows) with an average of 83.2 objective evaluations per window, whereas Simulated Annealing requires 5,000 evaluations per window to achieve the same feasibility rate.

### B. By what factor?
QAOA reduces the number of objective evaluations by a factor of:
$$\text{Factor} = \frac{5,000 \text{ evaluations}}{83.2 \text{ evaluations}} = \mathbf{60.1×}$$
QAOA is approximately $60×$ more query-efficient than Simulated Annealing in terms of the number of objective function calls.

### C. Is the factor large enough to justify a query-efficiency claim?
**No.** While a $60×$ query reduction is mathematically present, it is not practically significant when translated to computational overhead:
1.  **CPU Runtime Parity**: Running SA with 5 restarts takes only **0.0477 seconds per window** on a single classical CPU core. QAOA simulation on an Nvidia A100 GPU takes **2.15 seconds per window** for 1024 shots (45× slower).
2.  **Low Restart Threshold**: SA achieves maximum window coverage at only **$R=5$ restarts**, which is well below the threshold of $\ge 50$ restarts required to support a query-efficiency claim.

---

## 3. Query-Efficiency Verdict

**Verdict: REJECTED**

### Scientific Rationale:
Following the established interpretation rules, since Simulated Annealing achieves the identical 4/15 feasibility rate and solved set at **$R=5$ restarts (which is $\le 10$)**, we must reject the claim that QAOA possesses a meaningful query-efficiency advantage. 

Although QAOA evaluates the objective function fewer times, the classical cost of Simulated Annealing with 5 restarts is so trivial (under 50 milliseconds per window) that it renders any "quantum query-efficiency" claim practically negligible for near-term applications. 
The paper must be reframed to report these results transparently, acknowledging that classical stochastic search with very few restarts matches QAOA's feasibility profile.
