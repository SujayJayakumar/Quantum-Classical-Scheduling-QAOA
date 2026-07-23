#!/usr/bin/env python3
"""Build state-aware benchmark windows from the overlap job dataset."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from node_state_loader import NodeStateLoader, _DEFAULT_LOADER
from path_utils import DATA_DIR, WINDOWS_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DATA_DIR / "overlap_jobs.jsonl"), help="Filtered overlap job JSONL")
    parser.add_argument("--output", default=str(WINDOWS_DIR / "state_aware_source.json"), help="Output window JSON")
    parser.add_argument("--window-dir", default=str(WINDOWS_DIR / "state_aware_windows"), help="Directory for individual windows")
    return parser.parse_args()


def load_jobs(path: Path) -> list[dict[str, Any]]:
    jobs = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            jobs.append(json.loads(line))
    return jobs


def job_is_gpu(job: dict[str, Any]) -> bool:
    return int((job.get("optimization") or {}).get("gpu_req", 0) or 0) > 0


def job_fits_cluster(job: dict[str, Any]) -> bool:
    opt = job.get("optimization") or {}
    cpu_req = int(opt.get("cpu_req", 0) or 0)
    gpu_req = int(opt.get("gpu_req", 0) or 0)
    node_req = int(opt.get("node_req", 1) or 1)
    return cpu_req <= 128 and gpu_req <= 4 and node_req == 1


def build_window(label: str, jobs: list[dict[str, Any]], loader: NodeStateLoader) -> dict[str, Any]:
    window_start = min(job["submit_time"] for job in jobs)
    cluster_state = loader.get_cluster_state(window_start)
    has_gpu = any(job_is_gpu(job) for job in jobs)
    if has_gpu:
        node_ids = cluster_state["available_gpu_nodes"] or cluster_state["busy_nodes"]
    else:
        node_ids = cluster_state["available_cpu_nodes"] or cluster_state["busy_nodes"]
    cluster_nodes = {node["node_id"]: node for node in loader.cluster_nodes()}
    nodes = [cluster_nodes[node_id] for node_id in node_ids if node_id in cluster_nodes]
    if not nodes:
        nodes = loader.cluster_nodes()[:1]
    compatible = True
    for job in jobs:
        opt = job.get("optimization") or {}
        cpu_req = int(opt.get("cpu_req", 0) or 0)
        gpu_req = int(opt.get("gpu_req", 0) or 0)
        if not any(cpu_req <= node["cpu_capacity"] and gpu_req <= node["gpu_capacity"] for node in nodes):
            compatible = False
            break
    if not compatible:
        return {}
    return {
        "metadata": {
            "label": label,
            "window_start": window_start,
            "cluster_state": cluster_state,
            "job_count": len(jobs),
        },
        "jobs": jobs,
        "nodes": nodes,
        "cluster_state": cluster_state,
    }


def main() -> None:
    args = parse_args()
    loader = NodeStateLoader(tolerance_minutes=60)
    jobs = [job for job in load_jobs(resolve_path(args.input)) if job_fits_cluster(job)]
    cpu_jobs = [job for job in jobs if not job_is_gpu(job)]
    gpu_jobs = [job for job in jobs if job_is_gpu(job)]
    mixed_jobs = list(jobs)

    windows: list[dict[str, Any]] = []
    for category, pool in (("cpu", cpu_jobs), ("gpu", gpu_jobs), ("mixed", mixed_jobs)):
        for size in (10, 20, 30):
            if len(pool) < size:
                continue
            window_jobs = pool[:size]
            window = build_window(f"{category}_{size}", window_jobs, loader)
            if window:
                windows.append(window)

    payload = {
        "source": str(resolve_path(args.input)),
        "windows": windows,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    window_dir = Path(args.window_dir)
    window_dir.mkdir(parents=True, exist_ok=True)
    for index, window in enumerate(windows):
        window_path = window_dir / f"{window['metadata']['label']}_{index}.json"
        window_path.write_text(json.dumps(window, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Wrote state-aware windows to {window_dir}")



if __name__ == "__main__":
    main()
