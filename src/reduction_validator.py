#!/usr/bin/env python3
"""Validate reduced candidate-node windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from path_utils import resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Reduced window JSON file")
    parser.add_argument("--output", help="Optional JSON validation report")
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_window(window: dict[str, Any]) -> dict[str, Any]:
    jobs = window.get("jobs", [])
    nodes = window.get("candidate_nodes", [])
    node_ids = {str(node.get("node_id")) for node in nodes}
    node_types = {str(node.get("node_id")): str(node.get("node_type") or "") for node in nodes}
    details: list[dict[str, Any]] = []

    ok = True
    for job in jobs:
        opt = job.get("optimization") or {}
        requested = job.get("requested") or {}
        job_id = str(opt.get("job_id") or job.get("job_id"))
        cpu_req = int(opt.get("cpu_req", requested.get("ncpus", 0)) or 0)
        gpu_req = int(opt.get("gpu_req", requested.get("ngpus", 0)) or 0)
        feasible = [
            node
            for node in nodes
            if cpu_req <= int(node.get("cpu_capacity", 0) or 0)
            and gpu_req <= int(node.get("gpu_capacity", 0) or 0)
            and (gpu_req == 0 or str(node.get("node_type")) == "gpu")
        ]
        if not feasible:
            ok = False
            details.append({"type": "infeasible_job", "job_id": job_id, "cpu_req": cpu_req, "gpu_req": gpu_req})
        if gpu_req > 0 and not any(str(node.get("node_type")) == "gpu" for node in nodes):
            ok = False
            details.append({"type": "gpu_missing", "job_id": job_id, "message": "GPU job has no GPU candidate nodes."})

    if not nodes:
        ok = False
        details.append({"type": "empty_candidate_set", "message": "No candidate nodes present."})

    original_nodes = window.get("reduction_metadata", {}).get("original_node_count", 0)
    if original_nodes and len(nodes) > original_nodes:
        ok = False
        details.append({"type": "expanded_candidate_set", "message": "Reduced candidate set is larger than original state-aware node set."})

    if not node_ids:
        ok = False
        details.append({"type": "missing_node_ids", "message": "Candidate nodes are missing node_id values."})

    if len(node_ids) != len(nodes):
        ok = False
        details.append({"type": "duplicate_node_ids", "message": "Candidate node IDs are not unique."})

    if window.get("reduction_metadata", {}).get("estimated_qubits", 0) != len(jobs) * len(nodes):
        ok = False
        details.append({"type": "qubit_mismatch", "message": "Estimated qubits do not match jobs x candidate_nodes."})

    return {
        "valid": ok,
        "job_count": len(jobs),
        "candidate_node_count": len(nodes),
        "details": details,
    }


def main() -> None:
    args = parse_args()
    payload = load_payload(resolve_path(args.input))
    windows = payload.get("windows", [])
    report = {
        "valid": all(validate_window(window)["valid"] for window in windows),
        "windows": [validate_window(window) for window in windows],
    }
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
