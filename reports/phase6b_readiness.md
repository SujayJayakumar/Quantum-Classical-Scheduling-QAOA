# Phase 6B Benchmarking Readiness Report

This report presents the final readiness assessment for launching Phase 6B benchmarking on the frozen real-trace benchmark suite.

---

## Final Readiness Checklist

| Readiness Criteria | Status | Details / Evidence |
| :--- | :---: | :--- |
| **Is QUBO mathematically valid?** | **YES** | Verified via `qubo_energy_test.py` and `brute_force_mapping_solver.py` under Option B. Valid assignments yield lowest energies. |
| **Is QUBO→Ising mapping validated?** | **YES** | Verified via `validate_qaoa.py` Stage 1. 100% of computational states across `2x2`, `3x2`, and `4x3` yielded exact matches ($E_{\text{QUBO}} = E_{\text{Ising}} + \text{offset}$). |
| **Does QAOA pass toy validation?** | **YES** | Verified via `validate_qaoa.py` Stage 2. QAOA solver ($p=2$, shots=0) successfully resolved feasible mappings for all toy instances with tiny energy gaps ($0.30\%$ - $0.48\%$). |
| **Do SA and CP-SAT baselines work?** | **YES** | Both baselines ran successfully during validation and matched exact optimums. |
| **Are frozen benchmark windows valid?** | **YES** | Frozen windows in `data/windows/quantum_windows_reduced/` are validated against Phase 5.8 constraints. |
| **Are Small windows laptop-safe?** | **YES** | All Small windows require 15 qubits (0.50 MB memory) and execute in less than 1 second. |
| **Is a Large pilot feasible?** | **YES** | The Large `gpu_30` window requires 30 qubits (16.00 GB memory). It is fully executable in noiseless statevector simulation mode (`qpp-cpu` or `qpp-cuda`). |

---

## Final Recommendation: GO

We recommend a **GO** for Phase 6B progressive benchmarking under the new Option B QUBO formulation.

### Execution Guidelines

1.  **Enforce Gating**: Maintain Option B (capacity penalty deactivated, variable pruning active) in all benchmarking scripts.
2.  **Noiseless Statevector Simulation**: Run all experiments in noiseless simulator mode (`shots=0` for optimizer expectation calculation, `shots_count=1000` for final bitstring sampling).
3.  **Progressive Order**:
    *   **Stage A**: Run all three Small windows (15 qubits).
    *   **Stage B**: Run one Medium pilot window (`gpu_30`, 24 qubits).
    *   **Stage C**: Run one Large pilot window (`gpu_30`, 30 qubits).
4.  **Halting Gate**: Stop immediately after Stage C and wait for review.
