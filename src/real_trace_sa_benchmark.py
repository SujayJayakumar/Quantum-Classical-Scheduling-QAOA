#!/usr/bin/env python3
"""Benchmark classical simulated annealing on real trace windows.

Pipeline:
1. Generate QUBO from a trace window
2. Run SA solver
3. Decode assignment
4. Validate assignment
5. Run schedule decoder
6. Run CP-SAT mapping baseline
7. Compare results

Outputs:
- JSON summary
- CSV row-per-benchmark report
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

from assignment_validator import validate_assignment
from cp_sat_mapping_baseline import solve_mapping
from path_utils import REPO_ROOT, REPORTS_DIR, VALIDATION_DIR, resolve_path
from qubo_builder import build_qubo, qubo_energy
from qubo_sa_solver import run_solver
from schedule_decoder import decode_exclusive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Trace window JSON or Python file containing jobs and nodes")
    parser.add_argument("--input-dir", help="Directory containing benchmark windows")
    parser.add_argument(
        "--output-dir",
        default=str(REPORTS_DIR / "benchmarks"),
        help="Directory for benchmark JSON and CSV outputs",
    )
    parser.add_argument("--initial-temperature", type=float, default=100.0)
    parser.add_argument("--cooling-rate", type=float, default=0.95)
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cp-sat-time-limit-seconds", type=float, default=30.0)
    parser.add_argument("--cp-sat-workers", type=int, default=1)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--target-sizes",
        default="10,20,30,50",
        help="Comma-separated benchmark sizes to report; uses the first N jobs in the window",
    )
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    if path.suffix == ".py":
        namespace: dict[str, Any] = {}
        exec(path.read_text(encoding="utf-8"), namespace)
        return {
            "metadata": namespace.get("metadata", {}),
            "jobs": namespace.get("jobs"),
            "nodes": namespace.get("nodes"),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def job_id_map(variables: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {name: info for name, info in variables.items()}


def assignment_from_bits(bits: str, variables: dict[str, dict[str, Any]]) -> dict[str, str]:
    assignment: dict[str, str] = {}
    for name, info in variables.items():
        idx = int(info["index"])
        if idx < len(bits) and bits[idx] == "1":
            assignment[str(info["job_id"])] = str(info["node_id"])
    return assignment


def reduce_payload(payload: dict[str, Any], job_count: int) -> dict[str, Any]:
    reduced_jobs = payload["jobs"][:job_count]
    return {
        "metadata": dict(payload.get("metadata", {})),
        "jobs": reduced_jobs,
        "nodes": payload["nodes"],
    }


def benchmark_one(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    qubo_start = time.perf_counter()
    qubo = build_qubo(
        payload["jobs"],
        payload["nodes"],
        alpha_assign=10.0,
        alpha_capacity=0.0,
        alpha_gpu_compat=10.0,
        objective_scale=1.0,
    )
    qubo_runtime = time.perf_counter() - qubo_start

    sa_start = time.perf_counter()
    sa_result = run_solver(
        qubo,
        None,
        None,
        initial_temperature=args.initial_temperature,
        cooling_rate=args.cooling_rate,
        iterations=args.iterations,
        trials=args.trials,
        seed=args.seed,
    )
    sa_runtime = time.perf_counter() - sa_start

    best_trial = sa_result["summary"]["best_feasible"] or sa_result["summary"]["best_overall"]
    if best_trial is None:
        raise RuntimeError("SA produced no trial result")

    assignment = best_trial["assignment"]
    validation = validate_assignment(assignment, payload["jobs"], payload["nodes"])
    try:
        decoded = decode_exclusive(payload["jobs"], payload["nodes"], assignment)
    except Exception as exc:
        decoded = {
            "decoder": "exclusive_release_order",
            "makespan_seconds": None,
            "schedule": [],
            "node_usage": {},
            "error": str(exc),
        }

    cp_sat_start = time.perf_counter()
    cp_sat = solve_mapping(
        {
            "metadata": {"source": "real_trace_sa_benchmark"},
            "jobs": payload["jobs"],
            "nodes": payload["nodes"],
        },
        time_limit=args.cp_sat_time_limit_seconds,
        workers=args.cp_sat_workers,
        allow_multi_node=False,
    )
    cp_sat_runtime = time.perf_counter() - cp_sat_start

    brute_like = {}
    if len(payload["jobs"]) * len(payload["nodes"]) <= 12:
        from brute_force_mapping_solver import solve_bruteforce

        brute_start = time.perf_counter()
        brute_report = solve_bruteforce({"jobs": payload["jobs"], "nodes": payload["nodes"]})
        brute_runtime = time.perf_counter() - brute_start
        brute_like = {
            "best_energy_feasible_assignment": brute_report["best_energy_feasible_solution"]["assignment"] if brute_report["best_energy_feasible_solution"] else None,
            "best_energy_feasible_energy": brute_report["best_energy_feasible_solution"]["qubo_energy"] if brute_report["best_energy_feasible_solution"] else None,
            "runtime_seconds": brute_runtime,
            "reference_assignment": brute_report["cp_sat"]["assignments"],
            "reference_energy_gap": (
                None
                if brute_report["best_energy_feasible_solution"] is None
                else brute_report["best_energy_feasible_solution"]["qubo_energy"] - brute_report["cp_sat"]["mapping_objective_total_cost"]
            ),
        }

    energy_gap = None
    if brute_like.get("best_energy_feasible_energy") is not None:
        energy_gap = best_trial["energy"] - brute_like["best_energy_feasible_energy"]

    return {
        "job_count": len(payload["jobs"]),
        "node_count": len(payload["nodes"]),
        "qubo": {
            "variable_count": qubo["metadata"]["variable_count"],
            "runtime_seconds": qubo_runtime,
            "metadata": qubo["metadata"],
        },
        "sa": {
            "feasibility_rate": sa_result["summary"]["feasibility_rate"],
            "objective_value": sa_result["summary"]["best_feasible"]["energy"] if sa_result["summary"]["best_feasible"] else None,
            "qubo_energy": sa_result["summary"]["best_feasible"]["energy"] if sa_result["summary"]["best_feasible"] else None,
            "decoded_assignment": assignment,
            "decoded_makespan": decoded["makespan_seconds"],
            "utilization": decoded["makespan_seconds"] and (sum(item["duration_seconds"] for item in decoded.get("schedule", [])) / decoded["makespan_seconds"]) or None,
            "runtime_seconds": sa_runtime,
            "validation": validation,
        },
        "cp_sat": {
            "assignment": cp_sat["assignments"],
            "decoded_makespan": cp_sat["decoded_schedule"]["makespan_seconds"],
            "utilization": cp_sat["decoded_schedule"]["makespan_seconds"] and (sum(item["duration_seconds"] for item in cp_sat["decoded_schedule"]["schedule"]) / cp_sat["decoded_schedule"]["makespan_seconds"]) or None,
            "objective_value": cp_sat["mapping_objective_total_cost"],
            "runtime_seconds": cp_sat_runtime,
        },
        "comparison": {
            "assignment_overlap_with_cp_sat_pct": 100.0
            if assignment == cp_sat["assignments"]
            else (100.0 * len(set(assignment.items()) & set(cp_sat["assignments"].items())) / max(1, len(cp_sat["assignments"]))),
            "energy_gap_vs_bruteforce": energy_gap,
            "runtime_seconds": {
                "qubo_build": qubo_runtime,
                "sa": sa_runtime,
                "cp_sat": cp_sat_runtime,
                "brute_force": brute_like.get("runtime_seconds"),
            },
            "matches": {
                "sa_matches_cp_sat": assignment == cp_sat["assignments"],
                "sa_assignment_match_pct_vs_cp_sat": 100.0 if assignment == cp_sat["assignments"] else 0.0,
                "sa_matches_bruteforce": brute_like.get("reference_assignment") == assignment if brute_like else None,
                "sa_assignment_match_pct_vs_bruteforce": 100.0 if brute_like and brute_like.get("reference_assignment") == assignment else None,
            },
            "brute_force": brute_like,
        },
    }


def payload_label(path: Path) -> str:
    return path.stem


def payloads_from_args(args: argparse.Namespace) -> list[tuple[str, dict[str, Any]]]:
    if args.input and args.input_dir:
        raise SystemExit("Provide either --input or --input-dir, not both")
    if not args.input and not args.input_dir:
        raise SystemExit("Provide either --input or --input-dir")
    if args.input_dir:
        input_dir = resolve_path(args.input_dir)
        files = sorted([p for p in input_dir.glob("*.json") if p.is_file() and p.name != "manifest.json"])
        payloads: list[tuple[str, dict[str, Any]]] = []
        for path in files:
            payload = load_payload(path)
            if "jobs" not in payload or "nodes" not in payload:
                continue
            payloads.append((payload_label(path), payload))
        return payloads
    path = resolve_path(args.input)
    return [(payload_label(path), load_payload(path))]


def build_csv_rows(result: dict[str, Any], label: str) -> dict[str, Any]:
    return {
        "label": label,
        "job_count": result["job_count"],
        "node_count": result["node_count"],
        "qubo_variables": result["qubo"]["variable_count"],
        "qubo_build_runtime_seconds": result["qubo"]["runtime_seconds"],
        "sa_feasibility_rate": result["sa"]["feasibility_rate"],
        "sa_objective_value": result["sa"]["objective_value"],
        "sa_qubo_energy": result["sa"]["qubo_energy"],
        "sa_decoded_makespan": result["sa"]["decoded_makespan"],
        "sa_utilization": result["sa"]["utilization"],
        "sa_runtime_seconds": result["sa"]["runtime_seconds"],
        "cp_sat_objective_value": result["cp_sat"]["objective_value"],
        "cp_sat_decoded_makespan": result["cp_sat"]["decoded_makespan"],
        "cp_sat_utilization": result["cp_sat"]["utilization"],
        "cp_sat_runtime_seconds": result["cp_sat"]["runtime_seconds"],
        "assignment_overlap_with_cp_sat_pct": result["comparison"]["assignment_overlap_with_cp_sat_pct"],
        "energy_gap_vs_bruteforce": result["comparison"]["energy_gap_vs_bruteforce"],
        "sa_matches_cp_sat": result["comparison"]["matches"]["sa_matches_cp_sat"],
        "sa_assignment_match_pct_vs_cp_sat": result["comparison"]["matches"]["sa_assignment_match_pct_vs_cp_sat"],
    }


def main() -> None:
    args = parse_args()
    payloads = payloads_from_args(args)
    target_sizes = [int(item.strip()) for item in args.target_sizes.split(",") if item.strip()]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    per_benchmark_results = []
    csv_rows = []

    for label, payload in payloads:
        available_jobs = len(payload["jobs"])
        size_results = []
        skipped_sizes = []
        for size in target_sizes:
            if size > available_jobs:
                skipped_sizes.append(size)
                continue
            reduced = reduce_payload(payload, size)
            result = benchmark_one(reduced, args)
            size_label = f"{label}_{size}_jobs"
            size_results.append({"label": size_label, "result": result})
            csv_rows.append(build_csv_rows(result, size_label))
        per_benchmark_results.append(
            {
                "source_label": label,
                "source_jobs": available_jobs,
                "target_sizes": target_sizes,
                "skipped_sizes": skipped_sizes,
                "benchmarks": size_results,
            }
        )

    json_path = output_dir / "real_trace_sa_benchmark.json"
    csv_path = output_dir / "real_trace_sa_benchmark.csv"
    summary_json_path = output_dir / "summary.json"
    summary_csv_path = output_dir / "summary.csv"
    summary_md_path = output_dir / "summary.md"

    summary_rows = []
    for benchmark in per_benchmark_results:
        for item in benchmark["benchmarks"]:
            result = item["result"]
            summary_rows.append(
                {
            "category": benchmark["source_label"],
            "jobs": result["job_count"],
            "feasible": result["sa"]["validation"]["valid"],
            "makespan": result["sa"]["decoded_makespan"],
            "runtime_seconds": result["sa"]["runtime_seconds"],
            "assignment_overlap": result["comparison"]["assignment_overlap_with_cp_sat_pct"],
            "cp_sat_runtime_seconds": result["cp_sat"]["runtime_seconds"],
        }
            )

    summary_json_path.write_text(
        json.dumps({"benchmarks": per_benchmark_results}, indent=2 if args.pretty else None, sort_keys=True),
        encoding="utf-8",
    )
    with summary_csv_path.open("w", newline="", encoding="utf-8") as handle:
        if summary_rows:
            writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)
    summary_md_path.write_text(
        "# Benchmark Summary\n\n"
        + "\n".join(
            f"- {row['category']}: jobs={row['jobs']}, feasible={row['feasible']}, makespan={row['makespan']}, runtime={row['runtime_seconds']:.3f}, overlap={row['assignment_overlap']:.1f}%"
            for row in summary_rows
        ),
        encoding="utf-8",
    )

    json_path.write_text(json.dumps({"benchmarks": per_benchmark_results}, indent=2 if args.pretty else None, sort_keys=True), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        if csv_rows:
            writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)

    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {summary_json_path}")
    print(f"Wrote {summary_csv_path}")
    print(f"Wrote {summary_md_path}")


if __name__ == "__main__":
    main()
