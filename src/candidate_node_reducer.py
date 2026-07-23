#!/usr/bin/env python3
"""Reduce state-aware candidate nodes to quantum-sized local decision regions."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from node_state_loader import NodeStateLoader, _DEFAULT_LOADER
from path_utils import DATA_DIR, WINDOWS_DIR, resolve_path

CPU_CAPACITY = 128
GPU_CAPACITY = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Window JSON file or directory")
    parser.add_argument("--budget", choices=("small", "medium", "large"), help="Target quantum budget")
    parser.add_argument("--output-dir", default=str(WINDOWS_DIR / "quantum_windows_reduced"), help="Directory for reduced windows")
    parser.add_argument("--summary", default=str(DATA_DIR.parent / "reports" / "candidate_reduction_summary.md"), help="Markdown summary output")
    parser.add_argument("--top-k", type=int, default=3, help="Windows to retain per budget bucket")
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def as_job(job: dict[str, Any]) -> dict[str, Any]:
    opt = job.get("optimization") or {}
    requested = job.get("requested") or {}
    return {
        "job_id": str(opt.get("job_id") or job.get("job_id")),
        "cpu_req": int(opt.get("cpu_req", requested.get("ncpus", 0)) or 0),
        "gpu_req": int(opt.get("gpu_req", requested.get("ngpus", 0)) or 0),
        "queue": str(opt.get("queue") or job.get("queue") or ""),
        "submit_time": job.get("submit_time"),
        "start_time": job.get("start_time"),
        "estimated_runtime_seconds": int(opt.get("estimated_runtime_seconds", 0) or 0),
    }


def as_node(node: dict[str, Any]) -> dict[str, Any]:
    capacity = node.get("capacity") or node.get("observed_capacity") or {}
    node_type = str(node.get("node_type") or node.get("kind") or ("gpu" if int(node.get("gpu_capacity", capacity.get("ngpus", 0)) or 0) > 0 else "cpu"))
    return {
        "node_id": str(node.get("node_id")),
        "node_type": node_type,
        "cpu_capacity": int(node.get("cpu_capacity", capacity.get("ncpus", CPU_CAPACITY if node_type == "cpu" else CPU_CAPACITY)) or CPU_CAPACITY),
        "gpu_capacity": int(node.get("gpu_capacity", capacity.get("ngpus", GPU_CAPACITY if node_type == "gpu" else 0)) or (GPU_CAPACITY if node_type == "gpu" else 0)),
    }


def pressure(jobs: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> dict[str, float]:
    cpu_req = sum(j["cpu_req"] for j in jobs)
    gpu_req = sum(j["gpu_req"] for j in jobs)
    cpu_cap = sum(n["cpu_capacity"] for n in nodes)
    gpu_cap = sum(n["gpu_capacity"] for n in nodes)
    density = len(jobs) / len(nodes) if nodes else 0.0
    return {
        "cpu_pressure": cpu_req / cpu_cap if cpu_cap else 0.0,
        "gpu_pressure": gpu_req / gpu_cap if gpu_cap else 0.0,
        "job_density": density,
        "cpu_request": float(cpu_req),
        "gpu_request": float(gpu_req),
        "cpu_capacity": float(cpu_cap),
        "gpu_capacity": float(gpu_cap),
    }


def feasible_node(job: dict[str, Any], node: dict[str, Any]) -> bool:
    if job["gpu_req"] > 0 and node["node_type"] != "gpu":
        return False
    return job["cpu_req"] <= node["cpu_capacity"] and job["gpu_req"] <= node["gpu_capacity"]


def node_similarity_score(node: dict[str, Any], job_pool: list[dict[str, Any]], cluster_state: dict[str, Any]) -> float:
    score = 0.0
    if node["node_type"] == "gpu":
        score += 2.0 if any(job["gpu_req"] > 0 for job in job_pool) else 0.5
    else:
        score += 1.0
    # Prefer nodes that are currently available.
    summary = cluster_state.get("summary", {})
    if node["node_id"] in set(cluster_state.get("available_gpu_nodes", [])) | set(cluster_state.get("available_cpu_nodes", [])):
        score += 2.5
    elif node["node_id"] in set(cluster_state.get("busy_nodes", [])):
        score += 1.0
    # Prefer node types that appear in historical allocations.
    if any(str(job.get("allocated_node") or job.get("allocation") or "") == node["node_id"] for job in job_pool):
        score += 1.5
    if any(node["node_id"] in (job.get("allocated_nodes") or []) for job in job_pool):
        score += 1.5
    # Prefer nodes with similar type to historic allocations even when the exact node isn't present.
    historical_types = defaultdict(int)
    for job in job_pool:
        allocated_nodes = job.get("allocated_nodes") or []
        if allocated_nodes:
            historical_types["gpu" if node["node_type"] == "gpu" else "cpu"] += 1
    score += 0.1 * historical_types[node["node_type"]]
    return score


def score_nodes(jobs: list[dict[str, Any]], nodes: list[dict[str, Any]], cluster_state: dict[str, Any]) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for node in nodes:
        feasible_jobs = [job for job in jobs if feasible_node(job, node)]
        if not feasible_jobs:
            continue
        comp = pressure(feasible_jobs, [node])
        competition = comp["cpu_pressure"] + comp["gpu_pressure"] + comp["job_density"]
        scored.append(
            {
                **node,
                "feasible_job_count": len(feasible_jobs),
                "compatibility_score": node_similarity_score(node, jobs, cluster_state),
                "local_competition_score": competition,
                "local_pressure": comp,
            }
        )
    scored.sort(key=lambda item: (-item["compatibility_score"], -item["local_competition_score"], item["node_id"]))
    return scored


def target_bounds(budget: str) -> tuple[int, int]:
    if budget == "small":
        return 12, 16
    if budget == "medium":
        return 17, 24
    return 25, 32


def target_shape(budget: str) -> tuple[int, int, int]:
    if budget == "small":
        return 4, 4, 4
    if budget == "medium":
        return 5, 6, 5
    return 7, 8, 5


def select_nodes(jobs: list[dict[str, Any]], nodes: list[dict[str, Any]], cluster_state: dict[str, Any], budget: str, node_count: int) -> list[dict[str, Any]]:
    scored = score_nodes(jobs, nodes, cluster_state)
    if not scored:
        return []
    selected: list[dict[str, Any]] = []
    gpu_jobs = [job for job in jobs if job["gpu_req"] > 0]
    gpu_needed = bool(gpu_jobs)

    for node in scored:
        if gpu_needed and node["node_type"] != "gpu" and not selected:
            continue
        selected.append(node)
        if len(selected) >= node_count:
            break

    if gpu_needed and not any(node["node_type"] == "gpu" for node in selected):
        gpu_nodes = [node for node in scored if node["node_type"] == "gpu"]
        if gpu_nodes:
            selected = [gpu_nodes[0]] + [node for node in selected if node["node_id"] != gpu_nodes[0]["node_id"]]

    return selected[:node_count]


def score_job_subset(jobs: list[dict[str, Any]]) -> tuple[float, int, int, float]:
    cpu_req = sum(job["cpu_req"] for job in jobs)
    gpu_req = sum(job["gpu_req"] for job in jobs)
    density = len(jobs)
    mixed = 1 if any(job["gpu_req"] > 0 for job in jobs) else 0
    # Prefer contention-heavy, heterogeneous slices.
    return (cpu_req + 4 * gpu_req + 2 * density + 3 * mixed, gpu_req, cpu_req, density)


def select_jobs(jobs: list[dict[str, Any]], budget: str) -> list[dict[str, Any]]:
    min_jobs, max_jobs, _ = target_shape(budget)
    ordered = sorted(jobs, key=lambda job: (job["submit_time"], job["job_id"]))
    candidates: list[list[dict[str, Any]]] = []
    for size in range(min_jobs, min(max_jobs, len(ordered)) + 1):
        for start in range(0, len(ordered) - size + 1):
            subset = ordered[start : start + size]
            if len(subset) < min_jobs:
                continue
            if budget == "large" and all(job["gpu_req"] == 0 for job in subset):
                continue
            if budget == "medium" and all(job["gpu_req"] == 0 for job in subset) and size < 5:
                continue
            candidates.append(subset)
    if not candidates:
        return ordered[:min_jobs]
    candidates.sort(key=lambda subset: (-score_job_subset(subset)[0], -len(subset), subset[0]["job_id"]))
    return candidates[0]


def reduce_window(window: dict[str, Any], budget: str) -> dict[str, Any] | None:
    jobs = [as_job(job) for job in window.get("jobs", [])]
    nodes = [as_node(node) for node in window.get("nodes", [])]
    cluster_state = window.get("cluster_state") or window.get("metadata", {}).get("cluster_state") or {}
    if len(jobs) < 3 or len(nodes) < 2:
        return None
    original_pressure = pressure(jobs, nodes)
    if original_pressure["cpu_pressure"] == 0 and original_pressure["gpu_pressure"] == 0:
        return None

    all_nodes = _DEFAULT_LOADER.cluster_nodes()
    available_ids = set(cluster_state.get("available_cpu_nodes", [])) | set(cluster_state.get("available_gpu_nodes", [])) | set(cluster_state.get("busy_nodes", []))
    available_nodes = [node for node in all_nodes if node["node_id"] in available_ids]
    if not available_nodes:
        available_nodes = all_nodes

    orig_node_count = len(nodes)
    _, _, min_nodes = target_shape(budget)
    node_counts = [min_nodes]
    if budget == "small":
        node_counts = [3, 4]
    elif budget == "medium":
        node_counts = [3, 4]
    elif budget == "large":
        node_counts = [4, 5]

    # Cap node_counts to the original candidate pool size of the window
    node_counts = [min(nc, orig_node_count) for nc in node_counts]
    node_counts = sorted(list(set(node_counts)))

    best: dict[str, Any] | None = None
    ordered = sorted(jobs, key=lambda job: (job["submit_time"], job["job_id"]))
    
    lo, hi = target_bounds(budget)
    for node_count in node_counts:
        # Dynamically determine the job subset sizes that can satisfy the qubit budget
        min_size = (lo + node_count - 1) // node_count
        max_size = hi // node_count
        
        # Ensure sizes are within valid ranges
        min_size = max(3, min_size)
        max_size = min(len(ordered), max_size)
        
        for size in range(min_size, max_size + 1):
            for start in range(0, len(ordered) - size + 1):
                selected_jobs = ordered[start : start + size]
                if budget == "large" and all(job["gpu_req"] == 0 for job in selected_jobs):
                    continue
                if budget == "medium" and all(job["gpu_req"] == 0 for job in selected_jobs) and size < 5:
                    continue
                candidates = select_nodes(selected_jobs, available_nodes, cluster_state, budget, node_count=node_count)
                if len(candidates) != node_count:
                    continue
                reduced_pressure = pressure(selected_jobs, candidates)
                estimated_qubits = len(selected_jobs) * len(candidates)
                if not (lo <= estimated_qubits <= hi):
                    continue
                if reduced_pressure["cpu_pressure"] == 0 and reduced_pressure["gpu_pressure"] == 0:
                    continue
                score = (
                    reduced_pressure["cpu_pressure"]
                    + reduced_pressure["gpu_pressure"]
                    + reduced_pressure["job_density"]
                )
                candidate = {
                    "jobs": selected_jobs,
                    "candidate_nodes": candidates,
                    "cluster_state": cluster_state,
                    "original_node_count": len(nodes),
                    "reduced_node_count": len(candidates),
                    "original_job_count": len(jobs),
                    "reduced_job_count": len(selected_jobs),
                    "original_pressure": original_pressure,
                    "reduced_pressure": reduced_pressure,
                    "estimated_qubits": estimated_qubits,
                    "reduction_metadata": {
                        "budget": budget,
                        "original_node_count": len(nodes),
                        "reduced_node_count": len(candidates),
                        "original_job_count": len(jobs),
                        "reduced_job_count": len(selected_jobs),
                        "original_pressure": original_pressure,
                        "reduced_pressure": reduced_pressure,
                        "estimated_qubits": estimated_qubits,
                        "snapshot_timestamp": cluster_state.get("timestamp"),
                        "candidate_selection_method": "feasibility_ranked_local_competition",
                        "selection_score": score,
                    },
                    "window_start": window.get("metadata", {}).get("window_start"),
                    "label": window.get("metadata", {}).get("label"),
                }
                if best is None or candidate["reduction_metadata"]["selection_score"] > best["reduction_metadata"]["selection_score"]:
                    best = candidate

    return best


def load_windows(path: Path) -> list[dict[str, Any]]:
    if path.is_file():
        return [json.loads(path.read_text(encoding="utf-8"))]
    windows: list[dict[str, Any]] = []
    for item in sorted(path.glob("*.json")):
        if item.name == "manifest.json":
            continue
        windows.append(json.loads(item.read_text(encoding="utf-8")))
    return windows


def main() -> None:
    args = parse_args()
    input_path = resolve_path(args.input) if args.input else WINDOWS_DIR / "state_aware_windows"
    outputs = {
        "small": [],
        "medium": [],
        "large": [],
    }
    summary_rows: list[dict[str, Any]] = []
    windows = load_windows(input_path)
    for window in windows:
        reduced = reduce_window(window, args.budget or "small") if args.budget else None
        if reduced is None:
            continue
        reduced["category"] = args.budget or "small"
        outputs[args.budget or "small"].append(reduced)
        summary_rows.append(reduced)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"windows": []}
    for name, records in outputs.items():
        out_path = output_dir / f"{name}.json"
        out_path.write_text(json.dumps({"category": name, "count": len(records), "windows": records}, indent=2, sort_keys=True), encoding="utf-8")
        manifest["windows"].extend(records)

    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote reduced windows to {output_dir}")


if __name__ == "__main__":
    main()
