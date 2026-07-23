# Deliverable B: CP-SAT Ground Truth

## Decision

CP-SAT should be implemented before QUBO/QAOA.

Reason: CP-SAT gives a classical exact baseline for each small real-trace window. Later QUBO/QAOA results should be reported as feasible/infeasible and compared against CP-SAT makespan, utilization, and runtime.

This matches the reference paper's methodology: CP-SAT is used as a classical baseline/ground-truth solver, while QUBO methods are evaluated against it.

## Implemented File

- `cp_sat_scheduler.py`
- `cp_sat_mapping_baseline.py`
- `schedule_decoder.py`

## Input

The scheduler consumes output from `real_trace_window_generator.py`:

- JSON payload containing `jobs`, `nodes`, and `metadata`
- or a Python module containing `jobs = [...]` and `nodes = [...]`

## Model

There are now two CP-SAT baselines with different purposes.

### Full CP-SAT Scheduler

File: `cp_sat_scheduler.py`

- Boolean assignment variable: job `i` assigned to node `j`
- Shared integer start/end time per job
- Optional interval per compatible job-node pair
- Release time constraint from `submit_offset_seconds`
- Runtime from `runtime_seconds`
- GPU/CPU compatibility from requested resources and node capacities
- Multi-chunk PBS allocations are normalized to unique physical nodes
- Default node capacity mode: `exclusive`, one job per node at a time
- Objective: minimize makespan

This is a stronger exact scheduling model because it optimizes assignment and start times jointly.
Use it as an upper-bound classical scheduler, not as the fair mapping-only QUBO comparator.

### Mapping-Only CP-SAT Baseline

File: `cp_sat_mapping_baseline.py`

- Boolean assignment variable: job `i` assigned to node `j`
- No CP-SAT start-time variables
- Objective: balance estimated runtime load across nodes
- Output: `{job_id: node_id}` assignment map
- Schedule/makespan computed afterward by `schedule_decoder.py`

This is the fair abstraction for the first QUBO/QAOA formulation:

```text
jobs -> node assignments -> schedule decoder -> makespan
```

The mapping-only baseline currently skips multi-node jobs by default because the first QUBO formulation should stay at task/job-to-single-node mapping level.

## Leakage Control

Trace-window jobs now separate fields into:

- `optimization`: scheduler inputs such as `cpu_req`, `gpu_req`, `node_req`, `submit_offset_seconds`, and `estimated_runtime_seconds`
- `history`: evaluation metadata such as `actual_start_time`, `actual_wait_seconds`, `actual_runtime_seconds`, and `actual_nodes`

The mapping-only CP-SAT output records:

```json
"history_fields_used_by_model": []
```

This is the contract QUBO/QAOA should follow too.

## Example Commands

Generate a small start-only real trace window:

```bash
python3 real_trace_window_generator.py \
  --window-start 2025-01-12T17:30:00 \
  --duration-minutes 180 \
  --queue gpu \
  --mode start \
  --max-jobs 12 \
  --output sample_trace_window_start_only.json \
  --pretty
```

Solve it with CP-SAT:

```bash
python3 cp_sat_scheduler.py \
  --input sample_trace_window_start_only.json \
  --output cp_sat_schedule_start_only.json \
  --time-limit-seconds 30 \
  --time-grain-seconds 60 \
  --pretty
```

Solve the fair mapping-only baseline:

```bash
python3 cp_sat_mapping_baseline.py \
  --input sample_trace_window_start_only.json \
  --output cp_sat_mapping_schedule_start_only.json \
  --time-limit-seconds 30 \
  --pretty
```

## Verified Sample Result

For `sample_trace_window_start_only.json`:

- Status: `OPTIMAL`
- Jobs: `7`
- Nodes: `7`
- Makespan: `181080` seconds
- Critical lower-bound job: `100016.champ1`
- Critical lower bound: release `8194` seconds + runtime `172845` seconds, rounded to `181080` seconds at 60-second time grain

For mapping-only `cp_sat_mapping_schedule_start_only.json`:

- Status: `OPTIMAL`
- Mapped single-node jobs: `6`
- Skipped multi-node jobs: `1`
- Decoded makespan: `181039` seconds
- Output includes direct assignment map, e.g. `{job_id: node_id}`

For `sample_trace_window.json`:

- Status: `OPTIMAL`
- Jobs: `9`
- Nodes: `9`
- Makespan: `181080` seconds

The identical makespan is expected for these two sample windows because both include the same dominant long-running job, `100016.champ1`. With 1-second time grain, the same start-only window solves to `181039` seconds, confirming that `181080` is the 60-second discretized value.

As a sanity check, a shorter 90-minute start-only window that excludes `100016.champ1` solves to `21420` seconds. Both `exclusive` and `cumulative` capacity modes produce the same makespan on these small samples, so the equality is not caused by the default one-job-per-node simplification.

## Notes For Later QUBO/QAOA Work

- Use CP-SAT makespan as the ground-truth reference.
- Report QUBO/QAOA makespan gap as `(candidate_makespan - cp_sat_makespan) / cp_sat_makespan`.
- Report feasibility separately from objective quality.
- Use small windows first, because CP-SAT exactness is most useful as the instance size grows gradually.
- For QUBO mapping-only experiments, CP-SAT can still provide the target assignment/schedule pair for comparison.
- Prefer `--mode start` windows for CP-SAT ground-truth scheduling. `--mode overlap` is useful for resource-occupancy analysis, but already-running jobs need explicit locking before overlap windows should be treated as a scheduling ground truth.
