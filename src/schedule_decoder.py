#!/usr/bin/env python3
"""Deterministic schedule decoder for job-to-node mappings.

This is intentionally simple and QUBO-friendly: an optimizer proposes only
the mapping, then this decoder derives start/end times and makespan.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def job_optimization_view(job: dict[str, Any]) -> dict[str, Any]:
    opt = job.get("optimization", {})
    requested = job.get("requested", {})
    return {
        "job_id": str(opt.get("job_id") or job.get("job_id")),
        "submit_offset_seconds": int(job.get("submit_offset_seconds", opt.get("submit_offset_seconds", 0)) or 0),
        "estimated_runtime_seconds": int(job.get("estimated_runtime_seconds", opt.get("estimated_runtime_seconds", job.get("runtime_seconds", 0))) or 0),
        "cpu_req": int(job.get("cpu_req", opt.get("cpu_req", requested.get("ncpus", 0))) or 0),
        "gpu_req": int(job.get("gpu_req", opt.get("gpu_req", requested.get("ngpus", 0))) or 0),
        "node_req": int(opt.get("node_req", requested.get("nodes", 1)) or 1),
        "queue": opt.get("queue", job.get("queue")),
        "priority": int(job.get("priority", opt.get("priority", 0)) or 0),
    }


def node_view(node: dict[str, Any]) -> dict[str, Any]:
    capacity = node.get("capacity", node.get("observed_capacity", {}))
    cpu_capacity = node.get("cpu_capacity", capacity.get("ncpus", 0))
    gpu_capacity = node.get("gpu_capacity", capacity.get("ngpus", 0))
    return {
        "node_id": str(node.get("node_id")),
        "kind": node.get("node_type", node.get("kind", "cpu")),
        "ncpus": int(cpu_capacity or 0),
        "ngpus": int(gpu_capacity or 0),
    }


def decode_exclusive(
    jobs: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    assignments: dict[str, str],
) -> dict[str, Any]:
    """Decode a one-job-per-node mapping using release-time order."""

    opt_jobs = [job_optimization_view(job) for job in jobs]
    node_ids = {node_view(node)["node_id"] for node in nodes}
    availability = {node_id: 0 for node_id in node_ids}
    schedule = []

    for job in sorted(opt_jobs, key=lambda item: (item["submit_offset_seconds"], item["job_id"])):
        node_id = assignments.get(job["job_id"])
        if node_id not in node_ids:
            raise ValueError(f"Job {job['job_id']} is assigned to unknown node {node_id!r}")
        start = max(job["submit_offset_seconds"], availability[node_id])
        end = start + job["estimated_runtime_seconds"]
        availability[node_id] = end
        schedule.append(
            {
                "job_id": job["job_id"],
                "assigned_node": node_id,
                "start_seconds": start,
                "end_seconds": end,
                "duration_seconds": job["estimated_runtime_seconds"],
                "release_seconds": job["submit_offset_seconds"],
                "wait_seconds": start - job["submit_offset_seconds"],
            }
        )

    makespan = max((item["end_seconds"] for item in schedule), default=0)
    return {
        "decoder": "exclusive_release_order",
        "makespan_seconds": makespan,
        "schedule": schedule,
        "node_usage": {
            node_id: [item for item in schedule if item["assigned_node"] == node_id]
            for node_id in sorted(node_ids)
        },
    }
