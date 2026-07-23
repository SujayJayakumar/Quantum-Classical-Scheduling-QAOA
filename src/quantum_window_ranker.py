#!/usr/bin/env python3
"""Rank quantum windows using local state-aware scoring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from node_state_loader import get_cluster_state
from path_utils import WINDOWS_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=str(WINDOWS_DIR / "quantum_windows"), help="Directory with quantum window JSON files")
    parser.add_argument("--output", default=str(WINDOWS_DIR / "quantum_windows_ranked.json"), help="Output ranking file")
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rank_label(score: float) -> str:
    if score >= 2.0:
        return "HIGH"
    if score >= 1.0:
        return "MEDIUM"
    return "LOW"


def score_window(window: dict[str, Any]) -> dict[str, Any]:
    cpu_pressure = float(window.get("cpu_pressure_ratio", 0.0))
    gpu_pressure = float(window.get("gpu_pressure_ratio", 0.0))
    job_density = float(window.get("job_density", 0.0))
    qubits = int(window.get("qubits", 0))
    state_realism = 1.0
    if window.get("candidate_nodes", 0):
        state_realism = min(1.0, float(window.get("candidate_nodes", 0)) / max(1, qubits))
    wait_time_score = min(1.0, float(window.get("average_wait_seconds", 0.0)) / 3600.0)
    resource_pressure_score = (cpu_pressure + gpu_pressure) / 2.0
    competition_score = (resource_pressure_score + job_density) * state_realism
    overall = wait_time_score + resource_pressure_score + competition_score + (qubits / 32.0)
    return {
        **window,
        "wait_time_score": wait_time_score,
        "resource_pressure_score": resource_pressure_score,
        "candidate_node_competition_score": competition_score,
        "state_realism_score": state_realism,
        "overall_quantum_score": overall,
        "rank": rank_label(overall),
    }


def main() -> None:
    args = parse_args()
    input_dir = resolve_path(args.input_dir)
    ranked = []
    for path in sorted(input_dir.glob("quantum_windows_*.json")):
        payload = load_payload(path)
        for window in payload.get("windows", []):
            ranked.append(score_window(window))
    ranked.sort(key=lambda item: (-item["overall_quantum_score"], item["label"]))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"windows": ranked}, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

