#!/usr/bin/env python3
"""Benchmark CUDA-Q QAOA on reduced real trace windows.

Pipeline:
1. Load a reduced quantum window.
2. Generate QUBO from the window.
3. Run QAOA solver (placeholder for qaoa_cudaq_solver.py).
4. Decode assignment from the resulting bitstring.
5. Validate the assignment's feasibility.
6. Run the deterministic schedule decoder to get a makespan.
7. Run the CP-SAT mapping baseline on the same small window for comparison.
8. Compare QAOA results (makespan, feasibility, runtime) against the classical baseline.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from assignment_validator import validate_assignment
from cp_sat_mapping_baseline import solve_mapping
from path_utils import REPORTS_DIR, WINDOWS_DIR, resolve_path
from qaoa_cudaq_solver import run_solver as run_qaoa_solver  # Placeholder
from qubo_builder import build_qubo
from schedule_decoder import decode_exclusive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Reduced quantum window JSON file")
    parser.add_argument(
        "--output-dir",
        default=str(REPORTS_DIR / "qaoa_benchmarks"),
        help="Directory for benchmark JSON outputs",
    )
    parser.add_argument("--p", type=int, default=1, help="QAOA depth (number of layers)")
    parser.add_argument("--optimizer-steps", type=int, default=100, help="Max iterations for the classical optimizer")
    parser.add_argument("--cp-sat-time-limit-seconds", type=float, default=60.0)
    parser.add_argument("--cp-sat-workers", type=int, default=1)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def benchmark_one(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    label = payload.get("label", Path(args.input).stem)
    jobs = payload["jobs"]
    nodes = payload["candidate_nodes"]

    # 1. Build the QUBO
    qubo_start = time.perf_counter()
    qubo = build_qubo(
        jobs,
        nodes,
        alpha_assign=10.0,
        alpha_capacity=10.0,
        alpha_gpu_compat=10.0,
        objective_scale=0.1,
    )
    qubo_runtime = time.perf_counter() - qubo_start

    # 2. Run QAOA Solver
    qaoa_start = time.perf_counter()
    qaoa_result = run_qaoa_solver(
        qubo,
        p=args.p,
        optimizer_steps=args.optimizer_steps,
    )
    qaoa_runtime = time.perf_counter() - qaoa_start

    # 3. Decode, Validate, and Schedule QAOA result
    qaoa_assignment = qaoa_result["assignment"]
    qaoa_validation = validate_assignment(qaoa_assignment, jobs, nodes)
    try:
        qaoa_decoded = decode_exclusive(jobs, nodes, qaoa_assignment)
    except Exception as exc:
        qaoa_decoded = {"makespan_seconds": None, "error": str(exc)}

    # 4. Run CP-SAT Mapping Baseline for comparison
    cp_sat_start = time.perf_counter()
    cp_sat = solve_mapping(
        {
            "metadata": {"source": "real_trace_qaoa_benchmark"},
            "jobs": jobs,
            "nodes": nodes,
        },
        time_limit=args.cp_sat_time_limit_seconds,
        workers=args.cp_sat_workers,
        allow_multi_node=True,  # Reduced windows are single-node
    )
    cp_sat_runtime = time.perf_counter() - cp_sat_start

    # 5. Collate and Compare
    cp_sat_makespan = cp_sat.get("decoded_schedule", {}).get("makespan_seconds")
    qaoa_makespan = qaoa_decoded.get("makespan_seconds")

    makespan_gap = None
    if qaoa_makespan is not None and cp_sat_makespan is not None and cp_sat_makespan > 0:
        makespan_gap = (qaoa_makespan - cp_sat_makespan) / cp_sat_makespan

    return {
        "label": label,
        "job_count": len(jobs),
        "node_count": len(nodes),
        "qubo_variables": qubo["metadata"]["variable_count"],
        "qubo_build_runtime": qubo_runtime,
        "qaoa": {
            "p": args.p,
            "feasible": qaoa_validation["valid"],
            "makespan_seconds": qaoa_makespan,
            "runtime_seconds": qaoa_runtime,
            "expected_value": qaoa_result["expected_value"],
            "optimal_parameters": qaoa_result["optimal_parameters"],
            "assignment": qaoa_assignment,
            "validation_details": qaoa_validation,
        },
        "cp_sat": {
            "feasible": cp_sat["feasible"],
            "makespan_seconds": cp_sat_makespan,
            "runtime_seconds": cp_sat_runtime,
            "assignment": cp_sat["assignments"],
        },
        "comparison": {
            "makespan_gap_vs_cp_sat_pct": makespan_gap * 100.0 if makespan_gap is not None else None,
            "assignment_matches_cp_sat": qaoa_assignment == cp_sat["assignments"],
        },
    }


def main() -> None:
    args = parse_args()
    input_path = resolve_path(args.input)
    payload = load_payload(input_path)

    # The reduced window format has jobs under "jobs" and nodes under "candidate_nodes"
    if "candidate_nodes" not in payload:
        raise SystemExit(f"Input file {input_path} does not appear to be a reduced quantum window (missing 'candidate_nodes').")

    result = benchmark_one(payload, args)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{result['label']}_qaoa_p{args.p}.json"

    out_path.write_text(
        json.dumps(result, indent=2 if args.pretty else None, sort_keys=True),
        encoding="utf-8",
    )

    print(f"Wrote benchmark results to {out_path}")
    qaoa_makespan = result["qaoa"]["makespan_seconds"]
    cp_sat_makespan = result["cp_sat"]["makespan_seconds"]
    print(f"  QAOA Makespan: {qaoa_makespan} seconds (Feasible: {result['qaoa']['feasible']})")
    print(f"CP-SAT Makespan: {cp_sat_makespan} seconds")
    if result["comparison"]["makespan_gap_vs_cp_sat_pct"] is not None:
        print(f"  Makespan Gap: {result['comparison']['makespan_gap_vs_cp_sat_pct']:.2f}%")


if __name__ == "__main__":
    # This is a placeholder for the real solver.
    # Create a dummy file so the import works.
    placeholder_path = Path(__file__).parent / "qaoa_cudaq_solver.py"
    if not placeholder_path.exists():
        placeholder_path.write_text(
            'def run_solver(*args, **kwargs):\n'
            '    print("WARNING: Using placeholder QAOA solver.")\n'
            '    return {"assignment": {}, "expected_value": -1.0, "optimal_parameters": []}\n'
        )
    main()