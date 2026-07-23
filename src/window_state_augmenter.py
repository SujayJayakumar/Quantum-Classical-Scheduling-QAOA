#!/usr/bin/env python3
"""Attach reconstructed cluster state to a window JSON file."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from node_state_loader import get_cluster_state
from path_utils import WINDOWS_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Window JSON or Python module")
    parser.add_argument("--output", help="Output path; defaults to in-place overwrite")
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


def infer_timestamp(payload: dict[str, Any]) -> str:
    metadata = payload.get("metadata", {})
    if metadata.get("window_start"):
        return str(metadata["window_start"])
    jobs = payload.get("jobs", [])
    if not jobs:
        raise SystemExit("Cannot infer timestamp from empty window")
    return min(str(job.get("submit_time") or job.get("start_time") or "") for job in jobs if job.get("submit_time") or job.get("start_time"))


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace(" ", "T"))


def main() -> None:
    args = parse_args()
    input_path = resolve_path(args.input)
    payload = load_payload(input_path)
    timestamp = infer_timestamp(payload)
    payload["cluster_state"] = get_cluster_state(timestamp)
    out_path = Path(args.output) if args.output else input_path
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
