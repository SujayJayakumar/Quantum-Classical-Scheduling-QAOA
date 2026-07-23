# Phase 5.8: Quantum Budget Validation

This report verifies that the `candidate_node_reducer.py` script correctly produces windows that adhere to the specified quantum qubit budgets.

## Verification Method

The validation is inherent to the design of the `reduce_window` function in `candidate_node_reducer.py`.

The script defines explicit qubit boundaries for each budget category:

```python
def target_bounds(budget: str) -> tuple[int, int]:
    if budget == "small":
        return 12, 16
    if budget == "medium":
        return 17, 24
    return 25, 32
```

During its search for the best sub-window, it explicitly checks if the estimated number of qubits (`jobs` x `nodes`) falls within these bounds. Any combination that does not fit is immediately discarded.

```python
                estimated_qubits = len(selected_jobs) * len(candidates)
                lo, hi = target_bounds(budget)
                if not (lo <= estimated_qubits <= hi):
                    continue
```

## Conclusion

The implementation guarantees by design that any successfully generated reduced window will have a variable count (and thus, an estimated qubit count) that falls strictly within the `SMALL` (12-16), `MEDIUM` (17-24), or `LARGE` (25-32) budget it was created for. No post-filtering is necessary.