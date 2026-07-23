# Capacity Penalty Decision Check

This report evaluates whether the Phase 5.8 capacity penalty recommendations (Option B: Feasibility-only penalties + variable pruning) have been implemented.

## Classification

**Current Implementation: A) Capacity penalty still active**

---

## Detailed Code Audit

### 1. Active Penalty Calculation in `qubo_builder.py`
The capacity penalty terms are calculated and added to the QUBO matrix in [qubo_builder.py](file:///home/sim/Desktop/Quantum/src/qubo_builder.py#L226-L248):
```python
    # C. Capacity penalties:
    #    alpha_capacity * (sum_i cpu_i x_ij - cpu_cap_j)^2
    #    alpha_capacity * (sum_i gpu_i x_ij - gpu_cap_j)^2
    for j, node in enumerate(nodes):
        cap_cpu = node["cpu_capacity"]
        cap_gpu = node["gpu_capacity"]
        for i, job in enumerate(jobs):
            idx_i_j = index_map[(i, j)]
            cpu_demand = job["cpu_req"]
            gpu_demand = job["gpu_req"]
            add_to_q(Q, idx_i_j, idx_i_j, alpha_capacity * (cpu_demand * cpu_demand - 2.0 * cap_cpu * cpu_demand))
            add_to_q(Q, idx_i_j, idx_i_j, alpha_capacity * (gpu_demand * gpu_demand - 2.0 * cap_gpu * gpu_demand))
            ...
```

### 2. Active Invocation in the Benchmark Pipeline
In [real_trace_qaoa_benchmark.py](file:///home/sim/Desktop/Quantum/src/real_trace_qaoa_benchmark.py#L58-L65), `build_qubo` is called with a non-zero `alpha_capacity=10.0`:
```python
    qubo = build_qubo(
        jobs,
        nodes,
        alpha_assign=10.0,
        alpha_capacity=10.0,
        alpha_gpu_compat=10.0,
        objective_scale=0.1,
    )
```
And in [validate_qaoa.py](file:///home/sim/Desktop/Quantum/src/validate_qaoa.py#L132-L139), it is also called with `alpha_capacity=10.0`.

### 3. Missing Variable-Level Pruning
In [qubo_builder.py](file:///home/sim/Desktop/Quantum/src/qubo_builder.py#L132-L148), `build_variable_map` still maps every job to every node without pruning incompatible job-node pairs:
```python
    for i, job in enumerate(jobs):
        for j, node in enumerate(nodes):
            name = variable_name(i, j, job["job_id"], node["node_id"])
            ...
```

---

## Conclusion & Gating Decision

Because the capacity penalty remains fully active, we must trigger the **STOP CONDITION** and halt all benchmarking actions. We will not run Stage A, Stage B, or Stage C benchmarks at this time.

> [!CAUTION]
> **GATE TRIGGERED: STOP BENCHMARK EXECUTION**
>
> We are halting progress here to allow for model alignment before benchmark execution.
