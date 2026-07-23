#!/usr/bin/env python3
"""Summarize reconstructed cluster state across extracted windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from path_utils import REPORTS_DIR, WINDOWS_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(WINDOWS_DIR / "quantum_windows_ranked.json"), help="Ranked windows JSON")
    parser.add_argument("--output", default=str(REPORTS_DIR / "state_reconstruction_summary.md"), help="Markdown report path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(resolve_path(args.input).read_text(encoding="utf-8"))
    windows = payload.get("windows", [])
    if not windows:
        text = "# State Reconstruction Summary\n\nNo windows were available.\n"
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
        return

    def state_summary(window: dict[str, Any]) -> dict[str, Any]:
        summary = window.get("cluster_state_summary")
        if isinstance(summary, dict):
            return summary
        return {
            "available_cpu_count": window.get("available_cpu_count", 0),
            "available_gpu_count": window.get("available_gpu_count", 0),
            "busy_count": window.get("busy_count", 0),
            "offline_count": window.get("offline_count", 0),
        }

    summaries = [state_summary(w) for w in windows]
    snapshots = sum(1 for s in summaries if s.get("available_cpu_count", 0) or s.get("available_gpu_count", 0))
    avg_available = mean(float(s.get("available_cpu_count", 0) + s.get("available_gpu_count", 0)) for s in summaries)
    avg_busy = mean(float(s.get("busy_count", 0)) for s in summaries)
    avg_offline = mean(float(s.get("offline_count", 0)) for s in summaries)

    lines = [
        "# State Reconstruction Summary",
        "",
        f"- Number of snapshots used: {snapshots}",
        f"- Average available nodes: {avg_available:.2f}",
        f"- Average busy nodes: {avg_busy:.2f}",
        f"- Average offline nodes: {avg_offline:.2f}",
        "",
        "Notes:",
        "- Cluster state is reconstructed from `node_status.csv` and `nodes.csv`.",
        "- Windows are ranked after state-aware candidate-node selection.",
        "- If snapshots used is 0, the monitoring tables did not overlap the frozen benchmark timestamps within the configured tolerance.",
    ]
    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
