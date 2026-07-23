#!/usr/bin/env python3
"""Exhaustive mapping solver for very small job-to-node problems.

This enumerates every binary mapping assignment up to 12 variables total,
computes the mapping objective, filters feasible assignments using
assignment_validator.py, and compares the result against the CP-SAT mapping
baseline on toy instances.

The solver is intentionally tiny and brute-force only.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

from assignment_validator import validate_assignment
from cp_sat_mapping_baseline import solve_mapping
from qubo_builder import build_qubo, qubo_energy
from path_utils import REPO_ROOT, VALIDATION_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON or Python file containing assignments/jobs/nodes")
    parser.add_argument(
        "--example",
        choices=("2x2", "3x2"),
        help="Run one of the built-in toy problems instead of reading input",
    )
    parser.add_argument("--output", default=str(VALIDATION_DIR / "brute_force_mapping_report.json"), help="Output JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--debug", action="store_true", help="Print a short summary")
    return parser.parse_args()


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_payload(path: Path) -> dict[str, Any]:
    if path.suffix == ".py":
        namespace: dict[str, Any] = {}
        exec(path.read_text(encoding="utf-8"), namespace)
        return {
            "jobs": namespace.get("jobs"),
            "nodes": namespace.get("nodes"),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def job_view(job: dict[str, Any]) -> dict[str, Any]:
    opt = job.get("optimization") or {}
    requested = job.get("requested") or {}
    return {
        "job_id": str(opt.get("job_id") or job.get("job_id")),
        "cpu_req": _int(job.get("cpu_req", opt.get("cpu_req", requested.get("ncpus")))),
        "gpu_req": _int(job.get("gpu_req", opt.get("gpu_req", requested.get("ngpus")))),
        "node_req": max(1, _int(opt.get("node_req", requested.get("nodes", 1)), 1)),
        "estimated_runtime_seconds": _int(job.get("estimated_runtime_seconds", opt.get("estimated_runtime_seconds", job.get("runtime_seconds", 0)))),
    }


def node_view(node: dict[str, Any]) -> dict[str, Any]:
    capacity = node.get("capacity") or node.get("observed_capacity") or {}
    return {
        "node_id": str(node.get("node_id")),
        "cpu_capacity": _int(capacity.get("ncpus")),
        "gpu_capacity": _int(capacity.get("ngpus")),
    }


def make_example_2x2() -> dict[str, Any]:
    return {
        "jobs": [
            {"job_id": "j0", "optimization": {"cpu_req": 1, "gpu_req": 0, "node_req": 1, "estimated_runtime_seconds": 3}},
            {"job_id": "j1", "optimization": {"cpu_req": 2, "gpu_req": 1, "node_req": 1, "estimated_runtime_seconds": 5}},
        ],
        "nodes": [
            {"node_id": "n0", "node_type": "gpu", "capacity": {"ncpus": 4, "ngpus": 1}},
            {"node_id": "n1", "node_type": "cpu", "capacity": {"ncpus": 2, "ngpus": 0}},
        ],
    }


def make_example_3x2() -> dict[str, Any]:
    return {
        "jobs": [
            {"job_id": "j0", "optimization": {"cpu_req": 1, "gpu_req": 0, "node_req": 1, "estimated_runtime_seconds": 7}},
            {"job_id": "j1", "optimization": {"cpu_req": 2, "gpu_req": 1, "node_req": 1, "estimated_runtime_seconds": 3}},
            {"job_id": "j2", "optimization": {"cpu_req": 1, "gpu_req": 0, "node_req": 1, "estimated_runtime_seconds": 9}},
        ],
        "nodes": [
            {"node_id": "n0", "node_type": "gpu", "capacity": {"ncpus": 4, "ngpus": 1}},
            {"node_id": "n1", "node_type": "cpu", "capacity": {"ncpus": 2, "ngpus": 0}},
        ],
    }


EXAMPLES = {
    "2x2": make_example_2x2,
    "3x2": make_example_3x2,
}


def mapping_objective(assignments: dict[str, str], jobs: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> int:
    job_lookup = {job["job_id"]: job_view(job) for job in jobs}
    node_lookup = {node["node_id"]: node_view(node) for node in nodes}
    load = {node_id: 0 for node_id in node_lookup}
    for job_id, node_id in assignments.items():
        if job_id in job_lookup and node_id in load:
            load[node_id] += job_lookup[job_id]["estimated_runtime_seconds"]
    return max(load.values()) if load else 0


def enumerate_assignments(jobs: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    job_ids = [job_view(job)["job_id"] for job in jobs]
    node_ids = [node_view(node)["node_id"] for node in nodes]
    if len(job_ids) * len(node_ids) > 12:
        raise SystemExit(
            f"Problem too large for brute force: {len(job_ids) * len(node_ids)} binary variables (limit 12)"
        )

    rows = []
    for choice in itertools.product(node_ids, repeat=len(job_ids)):
        assignments = dict(zip(job_ids, choice))
        validation = validate_assignment(assignments, jobs, nodes)
        objective = mapping_objective(assignments, jobs, nodes)
        rows.append(
            {
                "assignment": assignments,
                "objective": objective,
                "valid": validation["valid"],
                "validation": validation,
            }
        )
    return rows


def solve_bruteforce(payload: dict[str, Any]) -> dict[str, Any]:
    jobs = payload["jobs"]
    nodes = payload["nodes"]
    qubo = build_qubo(jobs, nodes, alpha_assign=10.0, alpha_capacity=0.0, alpha_gpu_compat=0.0, objective_scale=1.0)
    variable_map = qubo["variables"]
    q_matrix = qubo["Q"]
    rows = enumerate_assignments(jobs, nodes)
    valid_rows = [row for row in rows if row["valid"]]
    all_rows_sorted = sorted(rows, key=lambda row: (row["objective"], not row["valid"], json.dumps(row["assignment"], sort_keys=True)))

    best_objective_row = min(rows, key=lambda row: (row["objective"], not row["valid"], json.dumps(row["assignment"], sort_keys=True)))
    best_feasible_row = min(valid_rows, key=lambda row: (row["objective"], json.dumps(row["assignment"], sort_keys=True))) if valid_rows else None

    def assignment_to_bits(assignment: dict[str, str]) -> list[int]:
        bits = [0] * len(variable_map)
        for name, info in variable_map.items():
            if assignment.get(info["job_id"]) == info["node_id"]:
                bits[info["index"]] = 1
        return bits

    for row in rows:
        bits = assignment_to_bits(row["assignment"])
        row["qubo_energy"] = qubo_energy(bits, q_matrix)
        row["bits"] = "".join(str(bit) for bit in bits)

    best_energy_row = min(rows, key=lambda row: (row["qubo_energy"], not row["valid"], json.dumps(row["assignment"], sort_keys=True)))
    best_energy_feasible_row = min(
        valid_rows,
        key=lambda row: (row["qubo_energy"], json.dumps(row["assignment"], sort_keys=True)),
    ) if valid_rows else None

    cp_sat_result = solve_mapping(
        {
            "metadata": {"source": "brute_force_mapping_solver"},
            "jobs": jobs,
            "nodes": nodes,
        },
        time_limit=10.0,
        workers=1,
        allow_multi_node=False,
    )

    cp_sat_assignments = cp_sat_result.get("assignments", {})
    cp_sat_objective = cp_sat_result.get("mapping_objective_total_cost")

    result = {
        "problem": {
            "job_count": len(jobs),
            "node_count": len(nodes),
            "variable_count": len(jobs) * len(nodes),
            "jobs": [job_view(job) for job in jobs],
            "nodes": [node_view(node) for node in nodes],
            "qubo_metadata": qubo["metadata"],
        },
        "enumeration_count": len(rows),
        "rows": all_rows_sorted,
        "best_objective_solution": best_objective_row,
        "best_energy_solution": best_energy_row,
        "best_feasible_solution": best_feasible_row,
        "best_energy_feasible_solution": best_energy_feasible_row,
        "cp_sat": {
            "status": cp_sat_result["status"],
            "optimal": cp_sat_result["optimal"],
            "assignments": cp_sat_assignments,
            "mapping_objective_total_cost": cp_sat_objective,
            "decoded_makespan_seconds": cp_sat_result.get("decoded_schedule", {}).get("makespan_seconds"),
            "job_count": cp_sat_result["job_count"],
            "node_count": cp_sat_result["node_count"],
        },
        "verification": {
            "best_energy_feasible_matches_cp_sat": (
                best_energy_feasible_row is not None
                and best_energy_feasible_row["assignment"] == cp_sat_assignments
            ),
            "three_way_match": (
                best_energy_feasible_row is not None
                and best_energy_feasible_row["assignment"] == cp_sat_assignments
            ),
            "cp_sat_is_feasible": cp_sat_result["feasible"],
            "enumerated_feasible_count": len(valid_rows),
        },
    }
    return result


def main() -> None:
    args = parse_args()
    if args.example:
        payload = EXAMPLES[args.example]()
    elif args.input:
        payload = load_payload(resolve_path(args.input))
    else:
        raise SystemExit("Provide either --input or --example")

    report = solve_bruteforce(payload)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True), encoding="utf-8")
    if args.debug:
        print(
            f"variables={report['problem']['variable_count']} "
            f"enumerated={report['enumeration_count']} "
            f"three_way_match={report['verification']['three_way_match']}"
        )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
