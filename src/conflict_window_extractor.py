#!/usr/bin/env python3
"""Extract contention-heavy trace windows suitable for quantum experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from node_state_loader import NodeStateLoader, _DEFAULT_LOADER
from path_utils import REPO_ROOT, WINDOWS_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        default=str(WINDOWS_DIR / "benchmarks_frozen_phase55"),
        help="Directory containing frozen trace windows",
    )
    parser.add_argument(
        "--output-dir",
        default=str(WINDOWS_DIR / "quantum_windows"),
        help="Directory for extracted quantum windows",
    )
    parser.add_argument("--top-k", type=int, default=20, help="Number of top-ranked windows to export per bucket")
    parser.add_argument("--state-aware", action="store_true", help="Use monitoring-derived node state for candidate nodes")
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


def job_view(job: dict[str, Any]) -> dict[str, Any]:
    opt = job.get("optimization") or {}
    requested = job.get("requested") or {}
    cpu_req = int(opt.get("cpu_req", requested.get("ncpus", 0)) or 0)
    gpu_req = int(opt.get("gpu_req", requested.get("ngpus", 0)) or 0)
    return {
        "job_id": str(opt.get("job_id") or job.get("job_id")),
        "cpu_req": cpu_req,
        "gpu_req": gpu_req,
        "estimated_runtime_seconds": int(opt.get("estimated_runtime_seconds", job.get("runtime_seconds", 0)) or 0),
    }


def node_view(node: dict[str, Any]) -> dict[str, Any]:
    capacity = node.get("capacity") or node.get("observed_capacity") or {}
    return {
        "node_id": str(node.get("node_id")),
        "node_type": str(node.get("node_type") or node.get("kind") or ("gpu" if int(node.get("gpu_capacity", capacity.get("ngpus", 0)) or 0) > 0 else "cpu")),
        "cpu_capacity": int(node.get("cpu_capacity", capacity.get("ncpus", 0)) or 0),
        "gpu_capacity": int(node.get("gpu_capacity", capacity.get("ngpus", 0)) or 0),
    }


def classify_qubits(qubits: int) -> str:
    if qubits <= 16:
        return "SMALL"
    if qubits <= 24:
        return "MEDIUM"
    if qubits <= 32:
        return "LARGE"
    return "SKIP"


def ranking_label(score: float) -> str:
    if score >= 2.0:
        return "HIGH"
    if score >= 1.0:
        return "MEDIUM"
    return "LOW"


def build_subwindow(
    payload: dict[str, Any],
    jobs: list[dict[str, Any]],
    label: str,
    candidate_nodes: list[dict[str, Any]] | None = None,
    cluster_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    nodes = candidate_nodes
    if nodes is None:
        node_ids: list[str] = []
        for job in jobs:
            for node_id in job.get("allocated_nodes", []) or []:
                if node_id not in node_ids:
                    node_ids.append(node_id)
        nodes = [node_view(node) for node in payload.get("nodes", []) if str(node.get("node_id")) in node_ids]
        if not nodes:
            nodes = [node_view(node) for node in payload.get("nodes", [])]
    sub_payload = {
        "metadata": dict(payload.get("metadata", {})),
        "jobs": jobs,
        "nodes": nodes,
    }
    if cluster_state is not None:
        sub_payload["cluster_state"] = cluster_state
    return analyze_window(sub_payload, label)


def jobs_by_node(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for job in payload.get("jobs", []):
        nodes = job.get("allocated_nodes") or []
        if not nodes:
            continue
        node_id = str(nodes[0])
        grouped.setdefault(node_id, []).append(job)
    return grouped


def analyze_window(payload: dict[str, Any], label: str) -> dict[str, Any]:
    jobs = [job_view(job) for job in payload.get("jobs", [])]
    nodes = [node_view(node) for node in payload.get("nodes", [])]

    cpu_req_total = sum(job["cpu_req"] for job in jobs)
    gpu_req_total = sum(job["gpu_req"] for job in jobs)
    cpu_cap_total = sum(node["cpu_capacity"] for node in nodes)
    gpu_cap_total = sum(node["gpu_capacity"] for node in nodes)
    job_density = len(jobs) / len(nodes) if nodes else 0.0

    events: list[tuple[int, int, int]] = []
    for job in payload.get("jobs", []):
        opt = job.get("optimization") or {}
        start = int(opt.get("submit_offset_seconds", job.get("submit_offset_seconds", 0)) or 0)
        runtime = int(opt.get("estimated_runtime_seconds", job.get("runtime_seconds", 0)) or 0)
        end = start + max(0, runtime)
        cpu_req = int(opt.get("cpu_req", 0) or 0)
        gpu_req = int(opt.get("gpu_req", 0) or 0)
        events.append((start, cpu_req, gpu_req))
        events.append((end, -cpu_req, -gpu_req))

    events.sort(key=lambda item: (item[0], item[1] + item[2]))
    running_cpu = 0
    running_gpu = 0
    peak_cpu = 0
    peak_gpu = 0
    for _, cpu_delta, gpu_delta in events:
        running_cpu += cpu_delta
        running_gpu += gpu_delta
        peak_cpu = max(peak_cpu, running_cpu)
        peak_gpu = max(peak_gpu, running_gpu)

    cpu_pressure = peak_cpu / cpu_cap_total if cpu_cap_total else 0.0
    gpu_pressure = peak_gpu / gpu_cap_total if gpu_cap_total else 0.0
    competition_score = (cpu_pressure + gpu_pressure) * (1.0 + job_density)
    rank = ranking_label(competition_score)
    mixed_pressure = cpu_pressure > 1.0 and gpu_pressure > 1.0
    qubits = len(jobs) * len(nodes)
    classification = classify_qubits(qubits)

    return {
        "label": label,
        "source": payload.get("metadata", {}).get("source"),
        "job_count": len(jobs),
        "candidate_nodes": len(nodes),
        "cpu_request_total": cpu_req_total,
        "gpu_request_total": gpu_req_total,
        "cpu_capacity_total": cpu_cap_total,
        "gpu_capacity_total": gpu_cap_total,
        "peak_cpu_demand": peak_cpu,
        "peak_gpu_demand": peak_gpu,
        "cpu_pressure_ratio": cpu_pressure,
        "gpu_pressure_ratio": gpu_pressure,
        "job_density": job_density,
        "resource_competition_score": competition_score,
        "rank": rank,
        "mixed_contention": mixed_pressure,
        "expected_variable_count": qubits,
        "qubits": qubits,
        "classification": classification,
        "has_cpu_contention": cpu_pressure > 1.0,
        "has_gpu_contention": gpu_pressure > 1.0,
        "contention_type": (
            "mixed" if mixed_pressure else "gpu" if gpu_pressure > 1.0 else "cpu" if cpu_pressure > 1.0 else "local"
        ),
        "cluster_state_summary": payload.get("cluster_state", {}).get("summary", {}),
        "payload": payload,
    }


def state_nodes_for_window(payload: dict[str, Any], jobs: list[dict[str, Any]], loader: NodeStateLoader | None = None) -> list[dict[str, Any]]:
    metadata = payload.get("metadata", {})
    ts = metadata.get("window_start")
    if not ts and payload.get("jobs"):
        ts = min(str(job.get("submit_time") or job.get("start_time") or "") for job in payload["jobs"] if job.get("submit_time") or job.get("start_time"))
    if not ts:
        return _DEFAULT_LOADER.cluster_nodes()[: max(1, min(8, len(jobs)))]
    loader_to_use = loader if loader is not None else NodeStateLoader(tolerance_minutes=60)
    cluster_state = loader_to_use.get_cluster_state(ts)
    cluster_nodes = {node["node_id"]: node for node in _DEFAULT_LOADER.cluster_nodes()}
    has_gpu = any(int((job.get("optimization") or {}).get("gpu_req", 0) or 0) > 0 for job in jobs)
    target_pool = cluster_state["available_gpu_nodes"] if has_gpu else cluster_state["available_cpu_nodes"]
    if not target_pool:
        target_pool = cluster_state["busy_nodes"] or cluster_state["available_cpu_nodes"] or cluster_state["available_gpu_nodes"]
    limit = max(1, min(8, len(jobs)))
    selected = [cluster_nodes[node_id] for node_id in target_pool if node_id in cluster_nodes][:limit]
    if not selected:
        selected = _DEFAULT_LOADER.cluster_nodes()[:limit]
    return selected


def main() -> None:
    args = parse_args()
    input_dir = resolve_path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    loader = NodeStateLoader(tolerance_minutes=60) if args.state_aware else None

    buckets = {"SMALL": [], "MEDIUM": [], "LARGE": []}
    manifest: list[dict[str, Any]] = []

    input_paths = [input_dir] if input_dir.is_file() else sorted(input_dir.glob("*.json"))
    for path in input_paths:
        if path.name == "manifest.json":
            continue
        payload = load_payload(path)
        if "jobs" not in payload or "nodes" not in payload:
            continue
        cluster_state = loader.get_cluster_state(payload.get("metadata", {}).get("window_start")) if loader and payload.get("metadata", {}).get("window_start") else None
        candidate_nodes = None
        grouped = jobs_by_node(payload)
        if not grouped:
            grouped = {"all": payload.get("jobs", [])}
        for node_id, jobs_in_node in grouped.items():
            selected = sorted(jobs_in_node, key=lambda job: (job.get("submit_offset_seconds", 0), job.get("job_id")))
            for size in range(1, min(9, len(selected) + 1)):
                jobs = selected[:size]
                current_candidates = state_nodes_for_window(payload, jobs, loader=loader) if args.state_aware else candidate_nodes
                record = build_subwindow(payload, jobs, f"{path.stem}_{node_id}_{size}", candidate_nodes=current_candidates, cluster_state=cluster_state)
                if record["classification"] == "SKIP":
                    continue
                buckets[record["classification"]].append(record)
                manifest.append(
                    {
                        "label": record["label"],
                        "classification": record["classification"],
                        "contention_type": record["contention_type"],
                        "jobs": record["job_count"],
                        "candidate_nodes": record["candidate_nodes"],
                        "qubits": record["qubits"],
                        "cpu_pressure_ratio": record["cpu_pressure_ratio"],
                        "gpu_pressure_ratio": record["gpu_pressure_ratio"],
                        "job_density": record["job_density"],
                        "resource_competition_score": record["resource_competition_score"],
                        "rank": record["rank"],
                        "available_cpu_count": record["cluster_state_summary"].get("available_cpu_count"),
                        "available_gpu_count": record["cluster_state_summary"].get("available_gpu_count"),
                        "busy_count": record["cluster_state_summary"].get("busy_count"),
                        "offline_count": record["cluster_state_summary"].get("offline_count"),
                        "node_id": node_id,
                    }
                )

    for name, records in buckets.items():
        records.sort(key=lambda record: (-record["resource_competition_score"], -record["job_density"], record["label"]))
        records = records[: args.top_k]
        out_path = output_dir / f"quantum_windows_{name.lower()}.json"
        out_path.write_text(
            json.dumps(
                {
                    "category": name,
                    "count": len(records),
                    "windows": [
                        {
                            k: v
                            for k, v in record.items()
                            if k != "payload"
                        }
                        for record in records
                    ],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    (output_dir / "manifest.json").write_text(json.dumps({"windows": manifest}, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote quantum window exports to {output_dir}")


if __name__ == "__main__":
    main()
