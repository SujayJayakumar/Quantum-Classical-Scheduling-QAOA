#!/usr/bin/env python3
"""Generate benchmark trace windows for CPU-only, GPU-only, and mixed jobs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cluster_model import generate_cluster_inventory
from path_utils import DATA_DIR, REPO_ROOT, WINDOWS_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(WINDOWS_DIR / "sample_trace_window_start_only.json"),
        help="Source trace-window JSON or Python file",
    )
    parser.add_argument(
        "--output-dir",
        default=str(WINDOWS_DIR / "benchmarks"),
        help="Directory to write benchmark windows",
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


def is_gpu_job(job: dict[str, Any]) -> bool:
    opt = job.get("optimization", {})
    requested = job.get("requested", {})
    return int(opt.get("gpu_req", requested.get("ngpus", 0)) or 0) > 0


def job_fits_cluster(job: dict[str, Any]) -> bool:
    opt = job.get("optimization", {})
    requested = job.get("requested", {})
    cpu_req = int(opt.get("cpu_req", requested.get("ncpus", 0)) or 0)
    gpu_req = int(opt.get("gpu_req", requested.get("ngpus", 0)) or 0)
    return cpu_req <= 128 and gpu_req <= 4


def trim_jobs(jobs: list[dict[str, Any]], category: str, size: int) -> list[dict[str, Any]]:
    jobs = [job for job in jobs if job_fits_cluster(job)]
    if category == "cpu-only":
        filtered = [job for job in jobs if not is_gpu_job(job)]
    elif category == "gpu-only":
        filtered = [job for job in jobs if is_gpu_job(job)]
    else:
        filtered = list(jobs)
    return filtered[:size]


def main() -> None:
    args = parse_args()
    payload = load_payload(resolve_path(args.input))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    categories = ("cpu-only", "gpu-only", "mixed")
    sizes = (10, 20, 30)
    cluster_nodes = generate_cluster_inventory()

    manifest: dict[str, Any] = {
        "source": str(resolve_path(args.input)),
        "outputs": [],
        "cluster": {
            "cpu_nodes": 410,
            "gpu_nodes": 12,
            "cpu_capacity": 128,
            "gpu_capacity": 4,
        },
    }

    for category in categories:
        for size in sizes:
            jobs = trim_jobs(payload["jobs"], category, size)
            if len(jobs) < size:
                continue
            out_path = output_dir / f"{category}_{size}.json"
            window_payload = {
                "metadata": {
                    "source": str(resolve_path(args.input)),
                    "category": category,
                    "job_count": len(jobs),
                    "cluster": manifest["cluster"],
                },
                "jobs": jobs,
                "nodes": cluster_nodes,
            }
            out_path.write_text(json.dumps(window_payload, indent=2, sort_keys=True), encoding="utf-8")
            manifest["outputs"].append(str(out_path))

    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote benchmark windows to {output_dir}")


if __name__ == "__main__":
    main()
