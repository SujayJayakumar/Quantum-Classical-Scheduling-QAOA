# Quantum-HPC Scheduling Research

This repository contains the research pipeline for a hybrid quantum-classical HPC job scheduler built around real PBS traces.

## Layout

- `src/`: executable Python scripts for trace profiling, window generation, CP-SAT baselines, QUBO construction, validation, and brute-force checks
- `data/windows/`: generated trace-window inputs used for experiments
- `data/windows/benchmarks/`: CPU-only, GPU-only, and mixed benchmark windows built on the real cluster inventory
- `data/validation/`: generated JSON outputs from CP-SAT, QUBO, brute-force, and validation runs
- `reports/`: narrative and metadata reports for the research workflow
- `reports/benchmarks/`: benchmark summaries and CSVs for real-trace SA runs
- `data/merged_all_jobs.jsonl`: raw trace source file
- `data/nodes.csv`, `data/node_status.csv`, `data/node_metrics.csv`, `data/cpu_metrics.csv`: optional cluster-state tables for node reconstruction

- All content of 'data' folder are hosted on zenodo, please download the dataset from the link : https://doi.org/10.5281/zenodo.21504068     and place it under the 'data' folder.

## Main Flow

1. Profile the trace and produce dataset metadata.
2. Generate a small trace window for a specific time slice.
3. Solve the mapping problem with CP-SAT as the classical baseline.
4. Build the QUBO and validate the energy function.
5. Brute-force tiny cases and compare against CP-SAT.
6. Generate benchmark windows for CPU-only, GPU-only, and mixed workloads on the real cluster inventory.
7. Run SA and CP-SAT over those benchmark windows and summarize feasibility, makespan, and overlap.

## Core Scripts

- `src/analyze_hpc_job_data.py`
- `src/real_trace_window_generator.py`
- `src/cp_sat_mapping_baseline.py`
- `src/cp_sat_scheduler.py`
- `src/qubo_builder.py`
- `src/assignment_validator.py`
- `src/qubo_energy_test.py`
- `src/brute_force_mapping_solver.py`
- `src/real_trace_sa_benchmark.py`

## Reproducibility Notes

- Scripts resolve inputs relative to the repository root.
- Generated artifacts are kept out of `src/`.
- Historical fields are separated from optimization inputs in the trace windows.
- Mapping-only experiments use `optimization.*` fields and the schedule decoder, not the raw execution history.

## Recommended Starting Commands

```bash
python3 src/analyze_hpc_job_data.py
python3 src/real_trace_window_generator.py --window-start 2025-01-12T17:30:00 --duration-minutes 180 --queue gpu --mode start --max-jobs 12
python3 src/cp_sat_mapping_baseline.py --input data/windows/sample_trace_window_start_only.json
python3 src/qubo_builder.py --input data/windows/sample_trace_window_start_only.json
python3 src/qubo_energy_test.py
python3 src/brute_force_mapping_solver.py --example 2x2
python3 src/benchmark_window_generator.py --input data/windows/sample_trace_window_start_only.json
python3 src/real_trace_sa_benchmark.py --input-dir data/windows/benchmarks
```
