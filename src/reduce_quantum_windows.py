#!/usr/bin/env python3
"""Build reduced quantum benchmark windows and write a summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from candidate_node_reducer import reduce_window
from path_utils import REPORTS_DIR, WINDOWS_DIR, resolve_path
from reduction_validator import validate_window


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default=str(WINDOWS_DIR / "state_aware_windows"), help="State-aware windows directory")
    parser.add_argument("--output-dir", default=str(WINDOWS_DIR / "quantum_windows_reduced"), help="Reduced window output directory")
    parser.add_argument("--summary", default=str(REPORTS_DIR / "candidate_reduction_summary.md"), help="Summary markdown path")
    parser.add_argument("--budgets", default="small,medium,large", help="Budgets to build")
    parser.add_argument("--max-per-budget", type=int, default=3)
    return parser.parse_args()


def load_windows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(item.read_text(encoding="utf-8")) for item in sorted(path.glob("*.json")) if item.is_file() and item.name != "manifest.json"]


def write_bucket(path: Path, category: str, windows: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps({"category": category, "count": len(windows), "windows": windows}, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_dir = resolve_path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_windows = load_windows(input_dir)
    budgets = [item.strip() for item in args.budgets.split(",") if item.strip()]
    summaries: list[str] = ["# Candidate Reduction Summary", ""]

    all_validated: list[dict[str, Any]] = []
    for budget in budgets:
        reduced: list[dict[str, Any]] = []
        for window in source_windows:
            candidate = reduce_window(window, budget)
            if candidate is None:
                continue
            validation = validate_window(candidate)
            candidate["validation"] = validation
            if not validation["valid"]:
                continue
            reduced.append(candidate)
        reduced.sort(key=lambda w: (-w["estimated_qubits"], -w["original_pressure"]["cpu_pressure"], w.get("label") or ""))
        reduced = reduced[: args.max_per_budget]
        all_validated.extend(reduced)
        write_bucket(output_dir / f"{budget}.json", budget, reduced)
        summaries.append(f"## {budget.title()}")
        summaries.append(f"- windows: {len(reduced)}")
        if reduced:
            summaries.append("")
            summaries.append("| window | jobs | original nodes | reduced nodes | qubits | CPU before | CPU after | GPU before | GPU after |")
            summaries.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
            for window in reduced:
                summaries.append(
                    "| {label} | {jobs} | {orig} | {red} | {qubits} | {cpu0:.3f} | {cpu1:.3f} | {gpu0:.3f} | {gpu1:.3f} |".format(
                        label=window.get("label"),
                        jobs=len(window.get("jobs", [])),
                        orig=window.get("original_node_count", 0),
                        red=window.get("reduced_node_count", 0),
                        qubits=window.get("estimated_qubits", 0),
                        cpu0=window.get("original_pressure", {}).get("cpu_pressure", 0.0),
                        cpu1=window.get("reduced_pressure", {}).get("cpu_pressure", 0.0),
                        gpu0=window.get("original_pressure", {}).get("gpu_pressure", 0.0),
                        gpu1=window.get("reduced_pressure", {}).get("gpu_pressure", 0.0),
                    )
                )
            summaries.append("")

    (output_dir / "manifest.json").write_text(json.dumps({"windows": all_validated}, indent=2, sort_keys=True), encoding="utf-8")
    Path(args.summary).write_text("\n".join(summaries).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote reduced windows to {output_dir}")
    print(f"Wrote {args.summary}")


if __name__ == "__main__":
    main()
