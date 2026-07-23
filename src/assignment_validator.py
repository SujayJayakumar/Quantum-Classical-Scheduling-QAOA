#!/usr/bin/env python3
"""Validate a job->node assignment against job and node resource data.

Expected input shape:

    {
      "assignments": {"job_id": "node_id", ...},
      "jobs": [...],
      "nodes": [...]
    }

or the equivalent three objects passed directly through the CLI helper.

The validator checks:

1. Every job assigned exactly once.
2. No missing jobs.
3. No duplicate assignments.
4. CPU capacity constraints.
5. GPU capacity constraints.
6. Detailed violation report.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from path_utils import REPO_ROOT, VALIDATION_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON or Python file with assignments, jobs, and nodes")
    parser.add_argument("--output", default=str(VALIDATION_DIR / "assignment_validation.json"), help="Output JSON path")
    parser.add_argument(
        "--example",
        choices=("valid", "missing", "overloaded", "gpu_mismatch"),
        help="Run one of the built-in test cases instead of reading input",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    if path.suffix == ".py":
        spec = importlib.util.spec_from_file_location("assignment_input_module", path)
        if spec is None or spec.loader is None:
            raise SystemExit(f"Could not import {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return {
            "assignments": getattr(module, "assignments"),
            "jobs": getattr(module, "jobs"),
            "nodes": getattr(module, "nodes"),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def job_view(job: dict[str, Any]) -> dict[str, Any]:
    opt = job.get("optimization") or {}
    requested = job.get("requested") or {}
    return {
        "job_id": str(opt.get("job_id") or job.get("job_id")),
        "cpu_req": _int(job.get("cpu_req", opt.get("cpu_req", requested.get("ncpus")))),
        "gpu_req": _int(job.get("gpu_req", opt.get("gpu_req", requested.get("ngpus")))),
        "node_req": max(1, _int(opt.get("node_req", requested.get("nodes", 1)), 1)),
    }


def node_view(node: dict[str, Any]) -> dict[str, Any]:
    capacity = node.get("capacity") or node.get("observed_capacity") or {}
    cpu_capacity = node.get("cpu_capacity", capacity.get("ncpus"))
    gpu_capacity = node.get("gpu_capacity", capacity.get("ngpus"))
    return {
        "node_id": str(node.get("node_id")),
        "node_type": str(node.get("node_type") or node.get("kind") or ("gpu" if _int(capacity.get("ngpus")) > 0 else "cpu")),
        "cpu_capacity": _int(cpu_capacity),
        "gpu_capacity": _int(gpu_capacity),
    }


def validate_assignment(assignments: dict[str, Any], jobs_input: list[dict[str, Any]], nodes_input: list[dict[str, Any]]) -> dict[str, Any]:
    jobs = [job_view(job) for job in jobs_input]
    nodes = [node_view(node) for node in nodes_input]
    node_by_id = {node["node_id"]: node for node in nodes}

    details: list[dict[str, Any]] = []
    job_ids = [job["job_id"] for job in jobs]
    assigned_job_ids = list(assignments.keys())
    assigned_counts = Counter(assigned_job_ids)

    missing_jobs = [job_id for job_id in job_ids if job_id not in assignments]
    unknown_jobs = [job_id for job_id in assigned_job_ids if job_id not in job_ids]
    duplicate_jobs = [job_id for job_id, count in assigned_counts.items() if count > 1]

    for job_id in missing_jobs:
        details.append(
            {
                "type": "missing_assignment",
                "job_id": job_id,
                "message": "Job has no node assignment.",
            }
        )
    for job_id in unknown_jobs:
        details.append(
            {
                "type": "unknown_job",
                "job_id": job_id,
                "message": "Assignment references a job that is not present in the job list.",
            }
        )
    for job_id in duplicate_jobs:
        details.append(
            {
                "type": "duplicate_assignment",
                "job_id": job_id,
                "count": assigned_counts[job_id],
                "message": "Job appears more than once in the assignment map.",
            }
        )

    node_cpu_used = defaultdict(int)
    node_gpu_used = defaultdict(int)
    node_jobs = defaultdict(list)
    gpu_compat_violations = 0

    for job in jobs:
        job_id = job["job_id"]
        if job_id not in assignments:
            continue
        node_id = str(assignments[job_id])
        if node_id not in node_by_id:
            details.append(
                {
                    "type": "unknown_node",
                    "job_id": job_id,
                    "node_id": node_id,
                    "message": "Assignment references a node that is not present in the node list.",
                }
            )
            continue

        node_jobs[node_id].append(job_id)
        node_cpu_used[node_id] += job["cpu_req"]
        node_gpu_used[node_id] += job["gpu_req"]
        if job["gpu_req"] > 0 and node_by_id[node_id]["node_type"] != "gpu":
            gpu_compat_violations += 1
            details.append(
                {
                    "type": "gpu_compatibility_violation",
                    "job_id": job_id,
                    "node_id": node_id,
                    "job_gpu_req": job["gpu_req"],
                    "node_type": node_by_id[node_id]["node_type"],
                    "message": "GPU job must be assigned to a GPU node.",
                }
            )

    cpu_violations = 0
    gpu_violations = 0
    for node_id, node in node_by_id.items():
        cpu_used = node_cpu_used[node_id]
        gpu_used = node_gpu_used[node_id]
        if cpu_used > node["cpu_capacity"]:
            cpu_violations += 1
            details.append(
                {
                    "type": "cpu_capacity_violation",
                    "node_id": node_id,
                    "used": cpu_used,
                    "capacity": node["cpu_capacity"],
                    "jobs": node_jobs[node_id],
                    "message": "Assigned CPU demand exceeds node CPU capacity.",
                }
            )
        if gpu_used > node["gpu_capacity"]:
            gpu_violations += 1
            details.append(
                {
                    "type": "gpu_capacity_violation",
                    "node_id": node_id,
                    "used": gpu_used,
                    "capacity": node["gpu_capacity"],
                    "jobs": node_jobs[node_id],
                    "message": "Assigned GPU demand exceeds node GPU capacity.",
                }
            )

    valid = (
        not missing_jobs
        and not unknown_jobs
        and not duplicate_jobs
        and cpu_violations == 0
        and gpu_violations == 0
        and gpu_compat_violations == 0
    )
    assignment_violations = len(missing_jobs) + len(unknown_jobs) + len(duplicate_jobs)

    return {
        "valid": valid,
        "assignment_violations": assignment_violations,
        "cpu_violations": cpu_violations,
        "gpu_violations": gpu_violations,
        "gpu_compatibility_violations": gpu_compat_violations,
        "details": details,
    }


def example_valid() -> dict[str, Any]:
    return {
        "assignments": {"j0": "n0", "j1": "n1"},
        "jobs": [
            {"job_id": "j0", "optimization": {"cpu_req": 1, "gpu_req": 0, "node_req": 1}},
            {"job_id": "j1", "optimization": {"cpu_req": 2, "gpu_req": 1, "node_req": 1}},
        ],
        "nodes": [
            {"node_id": "n0", "node_type": "cpu", "capacity": {"ncpus": 4, "ngpus": 0}},
            {"node_id": "n1", "node_type": "gpu", "capacity": {"ncpus": 2, "ngpus": 1}},
        ],
    }


def example_missing() -> dict[str, Any]:
    payload = example_valid()
    del payload["assignments"]["j1"]
    return payload


def example_overloaded() -> dict[str, Any]:
    return {
        "assignments": {"j0": "n0", "j1": "n0"},
        "jobs": [
            {"job_id": "j0", "optimization": {"cpu_req": 3, "gpu_req": 0, "node_req": 1}},
            {"job_id": "j1", "optimization": {"cpu_req": 2, "gpu_req": 0, "node_req": 1}},
        ],
        "nodes": [
            {"node_id": "n0", "node_type": "gpu", "capacity": {"ncpus": 4, "ngpus": 1}},
        ],
    }


def example_gpu_mismatch() -> dict[str, Any]:
    return {
        "assignments": {"j0": "n0"},
        "jobs": [
            {"job_id": "j0", "optimization": {"cpu_req": 1, "gpu_req": 1, "node_req": 1}},
        ],
        "nodes": [
            {"node_id": "n0", "node_type": "cpu", "capacity": {"ncpus": 4, "ngpus": 0}},
        ],
    }


EXAMPLES = {
    "valid": example_valid,
    "missing": example_missing,
    "overloaded": example_overloaded,
    "gpu_mismatch": example_gpu_mismatch,
}


def main() -> None:
    args = parse_args()
    if args.example:
        payload = EXAMPLES[args.example]()
    elif args.input:
        payload = load_payload(resolve_path(args.input))
    else:
        raise SystemExit("Provide either --input or --example")

    result = validate_assignment(payload["assignments"], payload["jobs"], payload["nodes"])
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(
        f"valid={result['valid']} assignment_violations={result['assignment_violations']} "
        f"cpu_violations={result['cpu_violations']} gpu_violations={result['gpu_violations']}"
    )


if __name__ == "__main__":
    main()
