#!/usr/bin/env python3
"""CP-SAT job-to-node mapping baseline plus deterministic schedule decoder.

This is the fair comparator for mapping-only QUBO/QAOA formulations:

    jobs -> node assignments -> schedule decoder -> makespan

It does not use actual historical node placement or actual start time as model
inputs. Those fields may remain in the trace window for evaluation only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path
from typing import Any

from ortools.sat.python import cp_model

from schedule_decoder import decode_exclusive, job_optimization_view, node_view
from qubo_builder import node_cost_proxy
from path_utils import REPO_ROOT, VALIDATION_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(REPO_ROOT / "data" / "windows" / "sample_trace_window_start_only.json"),
        help="Trace-window JSON or Python file",
    )
    parser.add_argument("--output", default=str(VALIDATION_DIR / "cp_sat_mapping_schedule.json"), help="Output JSON path")
    parser.add_argument("--time-limit-seconds", type=float, default=30.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--allow-multi-node", action="store_true", help="Allow multi-node jobs by assigning the first decoded node only")
    parser.add_argument("--pretty", action="store_true")
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


def compatible(job: dict[str, Any], node: dict[str, Any]) -> bool:
    node_kind = str(node.get("node_type") or node.get("kind") or "cpu")
    if job["gpu_req"] > 0 and node_kind != "gpu":
        return False
    if job["gpu_req"] > 0 and node["ngpus"] < job["gpu_req"]:
        return False
    if job["cpu_req"] > 0 and node["ncpus"] < job["cpu_req"]:
        return False
    return True


def solve_mapping(payload: dict[str, Any], time_limit: float, workers: int, allow_multi_node: bool) -> dict[str, Any]:
    raw_jobs = payload["jobs"]
    raw_nodes = payload["nodes"]
    opt_jobs = [job_optimization_view(job) for job in raw_jobs]
    nodes = [node_view(node) for node in raw_nodes]

    kept_jobs = []
    skipped_jobs = []
    for raw_job, opt_job in zip(raw_jobs, opt_jobs):
        if opt_job["node_req"] != 1 and not allow_multi_node:
            skipped_jobs.append(
                {
                    "job_id": opt_job["job_id"],
                    "reason": "multi_node_job_skipped_for_mapping_only_baseline",
                    "node_req": opt_job["node_req"],
                }
            )
            continue
        kept_jobs.append((raw_job, opt_job))

    if not kept_jobs:
        raise SystemExit("No single-node jobs available for mapping baseline")

    model = cp_model.CpModel()
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    for _, job in kept_jobs:
        choices = []
        for node in nodes:
            if not compatible(job, node):
                continue
            var = model.NewBoolVar(f"x_{job['job_id']}_{node['node_id']}")
            x[(job["job_id"], node["node_id"])] = var
            choices.append(var)
        if not choices:
            raise SystemExit(f"No compatible nodes for job {job['job_id']}")
        model.Add(sum(choices) == 1)

    # Mapping-only surrogate objective: minimize total node-sensitive execution cost.
    # The schedule decoder remains the only component that creates start/end times.
    total_cost_terms = []
    for _, job in kept_jobs:
        for node in nodes:
            var = x.get((job["job_id"], node["node_id"]))
            if var is not None:
                total_cost_terms.append(var * node_cost_proxy(job, node))
    model.Minimize(sum(total_cost_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 42

    started = time.perf_counter()
    status = solver.Solve(model)
    elapsed = time.perf_counter() - started
    feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    status_name = solver.StatusName(status)

    assignments: dict[str, str] = {}
    if feasible:
        for _, job in kept_jobs:
            for node in nodes:
                var = x.get((job["job_id"], node["node_id"]))
                if var is not None and solver.BooleanValue(var):
                    assignments[job["job_id"]] = node["node_id"]
                    break

    kept_raw_jobs = [raw_job for raw_job, _ in kept_jobs]
    decoded = decode_exclusive(kept_raw_jobs, raw_nodes, assignments) if feasible else {}
    return {
        "metadata": {
            "source_metadata": payload.get("metadata", {}),
            "solver": "OR-Tools CP-SAT mapping-only",
            "abstraction": "job_to_node_mapping_then_schedule_decoder",
            "model_inputs": [
                "optimization.cpu_req",
                "optimization.gpu_req",
                "optimization.node_req",
                "optimization.submit_offset_seconds",
                "optimization.estimated_runtime_seconds",
            ],
            "history_fields_used_by_model": [],
            "decoder": "exclusive_release_order",
            "time_limit_seconds": time_limit,
            "workers": workers,
        },
        "status": status_name,
        "feasible": feasible,
        "optimal": status == cp_model.OPTIMAL,
        "mapping_objective_total_cost": solver.ObjectiveValue() if feasible else None,
        "wall_time_seconds": elapsed,
        "job_count": len(kept_jobs),
        "node_count": len(nodes),
        "skipped_jobs": skipped_jobs,
        "assignments": assignments,
        "decoded_schedule": decoded,
    }


def main() -> None:
    args = parse_args()
    payload = load_window(resolve_path(args.input))
    result = solve_mapping(payload, args.time_limit_seconds, args.workers, args.allow_multi_node)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True), encoding="utf-8")
    print(f"Wrote {args.output}")
    print(
        f"Status: {result['status']}; optimal={result['optimal']}; "
        f"mapped_jobs={result['job_count']}; decoded_makespan="
        f"{result.get('decoded_schedule', {}).get('makespan_seconds')}"
    )


if __name__ == "__main__":
    main()
