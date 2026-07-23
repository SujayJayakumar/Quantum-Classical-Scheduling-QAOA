#!/usr/bin/env python3
"""CP-SAT ground-truth scheduler for real trace windows.

This is the classical exact baseline for later QUBO/QAOA experiments.
It consumes the window format produced by real_trace_window_generator.py:

    {
      "metadata": {...},
      "jobs": [...],
      "nodes": [...]
    }

or a Python module containing jobs = [...] and nodes = [...].
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import time
from pathlib import Path
from typing import Any

from ortools.sat.python import cp_model

from path_utils import REPO_ROOT, VALIDATION_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(REPO_ROOT / "data" / "windows" / "sample_trace_window_start_only.json"),
        help="Trace-window JSON or Python file",
    )
    parser.add_argument("--output", default=str(VALIDATION_DIR / "cp_sat_schedule.json"), help="Schedule output JSON path")
    parser.add_argument("--time-limit-seconds", type=float, default=60.0, help="CP-SAT wall-time limit")
    parser.add_argument("--workers", type=int, default=8, help="Number of CP-SAT search workers")
    parser.add_argument(
        "--time-grain-seconds",
        type=int,
        default=60,
        help="Discretization grain for CP-SAT integer time variables",
    )
    parser.add_argument(
        "--capacity-mode",
        choices=("exclusive", "cumulative"),
        default="exclusive",
        help="exclusive = one job per node; cumulative = CPU/GPU capacity sharing",
    )
    parser.add_argument(
        "--objective",
        choices=("makespan", "total_completion", "makespan_then_wait"),
        default="makespan",
        help="Primary optimization objective",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args()


def load_window(path: Path) -> dict[str, Any]:
    if path.suffix == ".py":
        spec = importlib.util.spec_from_file_location("trace_window_module", path)
        if spec is None or spec.loader is None:
            raise SystemExit(f"Could not import {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return {
            "metadata": getattr(module, "metadata", {}),
            "jobs": getattr(module, "jobs"),
            "nodes": getattr(module, "nodes"),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def ceil_div(value: int, divisor: int) -> int:
    return int(math.ceil(value / max(1, divisor)))


def to_units(seconds: int, grain: int) -> int:
    return ceil_div(max(0, seconds), grain)


def positive_int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return default


def normalize_jobs(raw_jobs: list[dict[str, Any]], grain: int) -> list[dict[str, Any]]:
    jobs = []
    for index, job in enumerate(raw_jobs):
        requested = job.get("requested", {})
        raw_requested_nodes = max(1, positive_int(requested.get("nodes"), 1))
        allocated_unique_nodes = sorted(set(str(node) for node in job.get("allocated_nodes", []) if str(node).strip()))
        requested_nodes = raw_requested_nodes
        if allocated_unique_nodes and len(allocated_unique_nodes) < requested_nodes:
            requested_nodes = len(allocated_unique_nodes)
        runtime_seconds = positive_int(job.get("runtime_seconds"))
        if runtime_seconds <= 0:
            continue
        submit_offset_seconds = positive_int(job.get("submit_offset_seconds"))
        total_ncpus = positive_int(requested.get("ncpus"))
        total_ngpus = positive_int(requested.get("ngpus"))
        jobs.append(
            {
                "index": index,
                "job_id": str(job.get("job_id") or f"job_{index}"),
                "name": job.get("name"),
                "queue": job.get("queue"),
                "user": job.get("user"),
                "duration": to_units(runtime_seconds, grain),
                "duration_seconds": runtime_seconds,
                "release": to_units(submit_offset_seconds, grain),
                "release_seconds": submit_offset_seconds,
                "requested_nodes": requested_nodes,
                "raw_requested_nodes": raw_requested_nodes,
                "observed_unique_nodes": allocated_unique_nodes,
                "total_ncpus": total_ncpus,
                "total_ngpus": total_ngpus,
                "per_node_ncpus": max(1 if total_ncpus else 0, ceil_div(total_ncpus, requested_nodes)),
                "per_node_ngpus": ceil_div(total_ngpus, requested_nodes),
                "raw": job,
            }
        )
    return jobs


def normalize_nodes(raw_nodes: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_cpu_demand = max((job["per_node_ncpus"] for job in jobs), default=1)
    max_gpu_demand = max((job["per_node_ngpus"] for job in jobs), default=0)
    nodes = []
    for index, node in enumerate(raw_nodes):
        observed = node.get("observed_capacity", {})
        ncpus = positive_int(observed.get("ncpus"))
        ngpus = positive_int(observed.get("ngpus"))
        kind = node.get("kind") or ("gpu" if ngpus > 0 else "cpu")
        if kind == "gpu" and ngpus == 0:
            ngpus = max(1, max_gpu_demand)
        if ncpus == 0:
            ncpus = max(1, max_cpu_demand)
        nodes.append(
            {
                "index": index,
                "node_id": str(node.get("node_id") or f"node_{index}"),
                "kind": kind,
                "ncpus": ncpus,
                "ngpus": ngpus,
                "raw": node,
            }
        )
    return nodes


def compatible(job: dict[str, Any], node: dict[str, Any]) -> bool:
    if job["per_node_ngpus"] > 0 and node["ngpus"] < job["per_node_ngpus"]:
        return False
    if job["per_node_ncpus"] > 0 and node["ncpus"] < job["per_node_ncpus"]:
        return False
    return True


def solve_cp_sat(
    raw_jobs: list[dict[str, Any]],
    raw_nodes: list[dict[str, Any]],
    metadata: dict[str, Any],
    grain: int,
    time_limit: float,
    workers: int,
    capacity_mode: str,
    objective: str,
) -> dict[str, Any]:
    jobs = normalize_jobs(raw_jobs, grain)
    nodes = normalize_nodes(raw_nodes, jobs)
    if not jobs:
        raise SystemExit("No schedulable jobs found in input")
    if not nodes:
        raise SystemExit("No nodes found in input")

    horizon = sum(job["duration"] for job in jobs) + max(job["release"] for job in jobs)
    release_duration_bounds = [
        {
            "job_id": job["job_id"],
            "release_seconds": job["release_seconds"],
            "duration_seconds": job["duration_seconds"],
            "earliest_completion_seconds": (job["release"] + job["duration"]) * grain,
        }
        for job in jobs
    ]
    critical_release_duration_bound = max(release_duration_bounds, key=lambda item: item["earliest_completion_seconds"])
    model = cp_model.CpModel()
    starts: dict[int, cp_model.IntVar] = {}
    ends: dict[int, cp_model.IntVar] = {}
    assignment: dict[tuple[int, int], cp_model.IntVar] = {}
    intervals: dict[tuple[int, int], cp_model.IntervalVar] = {}

    for job in jobs:
        starts[job["index"]] = model.NewIntVar(job["release"], horizon, f"start_{job['index']}")
        ends[job["index"]] = model.NewIntVar(job["release"] + job["duration"], horizon, f"end_{job['index']}")
        model.Add(ends[job["index"]] == starts[job["index"]] + job["duration"])

    for job in jobs:
        compatible_nodes = []
        for node in nodes:
            if not compatible(job, node):
                continue
            var = model.NewBoolVar(f"x_j{job['index']}_n{node['index']}")
            interval = model.NewOptionalIntervalVar(
                starts[job["index"]],
                job["duration"],
                ends[job["index"]],
                var,
                f"interval_j{job['index']}_n{node['index']}",
            )
            assignment[(job["index"], node["index"])] = var
            intervals[(job["index"], node["index"])] = interval
            compatible_nodes.append(var)
        if len(compatible_nodes) < job["requested_nodes"]:
            raise SystemExit(
                f"Job {job['job_id']} needs {job['requested_nodes']} compatible node(s), "
                f"but only {len(compatible_nodes)} are available"
            )
        model.Add(sum(compatible_nodes) == job["requested_nodes"])

    for node in nodes:
        node_intervals = []
        cpu_demands = []
        gpu_demands = []
        for job in jobs:
            key = (job["index"], node["index"])
            if key not in intervals:
                continue
            node_intervals.append(intervals[key])
            cpu_demands.append(job["per_node_ncpus"])
            gpu_demands.append(job["per_node_ngpus"])
        if not node_intervals:
            continue
        if capacity_mode == "exclusive":
            model.AddNoOverlap(node_intervals)
        else:
            model.AddCumulative(node_intervals, cpu_demands, node["ncpus"])
            if node["ngpus"] > 0:
                model.AddCumulative(node_intervals, gpu_demands, node["ngpus"])

    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, [ends[job["index"]] for job in jobs])
    if objective == "total_completion":
        model.Minimize(sum(ends[job["index"]] for job in jobs))
    elif objective == "makespan_then_wait":
        model.Minimize(makespan * (len(jobs) * horizon + 1) + sum(starts[job["index"]] - job["release"] for job in jobs))
    else:
        model.Minimize(makespan)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 42
    start_wall = time.perf_counter()
    status = solver.Solve(model)
    elapsed = time.perf_counter() - start_wall
    status_name = solver.StatusName(status)
    feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    schedule = []
    assignment_output: dict[str, list[str]] = {}
    node_usage = {node["node_id"]: [] for node in nodes}
    if feasible:
        node_by_index = {node["index"]: node for node in nodes}
        for job in jobs:
            assigned_nodes = []
            for node in nodes:
                var = assignment.get((job["index"], node["index"]))
                if var is not None and solver.BooleanValue(var):
                    assigned_nodes.append(node["node_id"])
            assignment_output[job["job_id"]] = assigned_nodes
            start_units = solver.Value(starts[job["index"]])
            end_units = solver.Value(ends[job["index"]])
            item = {
                "job_id": job["job_id"],
                "name": job["name"],
                "queue": job["queue"],
                "user": job["user"],
                "assigned_nodes": assigned_nodes,
                "start": start_units,
                "end": end_units,
                "start_seconds": start_units * grain,
                "end_seconds": end_units * grain,
                "duration_seconds": job["duration_seconds"],
                "release_seconds": job["release_seconds"],
                "wait_seconds": max(0, (start_units - job["release"]) * grain),
                "requested": {
                    "nodes": job["requested_nodes"],
                    "raw_nodes": job["raw_requested_nodes"],
                    "observed_unique_nodes": job["observed_unique_nodes"],
                    "ncpus": job["total_ncpus"],
                    "ngpus": job["total_ngpus"],
                    "per_node_ncpus": job["per_node_ncpus"],
                    "per_node_ngpus": job["per_node_ngpus"],
                },
            }
            schedule.append(item)
            for node_id in assigned_nodes:
                node_usage[node_id].append(
                    {
                        "job_id": job["job_id"],
                        "start_seconds": item["start_seconds"],
                        "end_seconds": item["end_seconds"],
                    }
                )
        schedule.sort(key=lambda item: (item["start_seconds"], item["job_id"]))
        for usage in node_usage.values():
            usage.sort(key=lambda item: (item["start_seconds"], item["job_id"]))

    makespan_units = solver.Value(makespan) if feasible else None
    total_runtime_seconds = sum(job["duration_seconds"] * job["requested_nodes"] for job in jobs)
    node_window_seconds = (makespan_units or 0) * grain * max(1, len(nodes))
    utilization = total_runtime_seconds / node_window_seconds if feasible and node_window_seconds else None

    return {
        "metadata": {
            "source_metadata": metadata,
            "solver": "OR-Tools CP-SAT",
            "abstraction": "joint_assignment_and_start_time_optimization",
            "time_grain_seconds": grain,
            "capacity_mode": capacity_mode,
            "objective": objective,
            "time_limit_seconds": time_limit,
            "workers": workers,
        },
        "status": status_name,
        "feasible": feasible,
        "optimal": status == cp_model.OPTIMAL,
        "objective_value": solver.ObjectiveValue() if feasible else None,
        "best_objective_bound": solver.BestObjectiveBound() if feasible else None,
        "wall_time_seconds": elapsed,
        "solver_wall_time_seconds": solver.WallTime(),
        "conflicts": solver.NumConflicts(),
        "branches": solver.NumBranches(),
        "job_count": len(jobs),
        "node_count": len(nodes),
        "makespan_seconds": makespan_units * grain if feasible else None,
        "critical_release_duration_bound": critical_release_duration_bound,
        "total_job_node_runtime_seconds": total_runtime_seconds,
        "approx_node_utilization": utilization,
        "nodes": [
            {
                "node_id": node["node_id"],
                "kind": node["kind"],
                "capacity": {"ncpus": node["ncpus"], "ngpus": node["ngpus"]},
            }
            for node in nodes
        ],
        "assignments": assignment_output if feasible else {},
        "schedule": schedule,
        "node_usage": node_usage if feasible else {},
    }


def main() -> None:
    args = parse_args()
    payload = load_window(resolve_path(args.input))
    result = solve_cp_sat(
        payload["jobs"],
        payload["nodes"],
        payload.get("metadata", {}),
        args.time_grain_seconds,
        args.time_limit_seconds,
        args.workers,
        args.capacity_mode,
        args.objective,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True), encoding="utf-8")
    print(f"Wrote {output_path}")
    print(
        f"Status: {result['status']}; optimal={result['optimal']}; "
        f"jobs={result['job_count']}; nodes={result['node_count']}; "
        f"makespan={result['makespan_seconds']} seconds"
    )


if __name__ == "__main__":
    main()
