#!/usr/bin/env python3
"""Filter the full job trace down to the monitoring overlap interval."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from path_utils import DATA_DIR, REPORTS_DIR, resolve_path

PBS_TIME_FORMAT = "%a %b %d %H:%M:%S %Y"
OVERLAP_START = datetime.fromisoformat("2025-08-15T00:00:01+05:30")
OVERLAP_END = datetime.fromisoformat("2026-01-31T23:55:02+05:30")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DATA_DIR / "merged_all_jobs.jsonl"), help="Full trace JSONL")
    parser.add_argument("--output", default=str(DATA_DIR / "overlap_jobs.jsonl"), help="Filtered overlap JSONL")
    parser.add_argument("--summary", default=str(REPORTS_DIR / "overlap_dataset_summary.md"), help="Summary markdown")
    return parser.parse_args()


def parse_pbs_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), PBS_TIME_FORMAT).replace(tzinfo=OVERLAP_START.tzinfo)
    except ValueError:
        return None


def parse_walltime(value: Any) -> int | None:
    if value is None:
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    
    # 1. Pure integer seconds support
    if val_str.isdigit():
        return int(val_str)
        
    parts = val_str.split(":")
    
    # 2. HH:MM:SS format support
    if len(parts) == 3:
        try:
            h = int(parts[0])
            m = int(parts[1])
            s = int(parts[2])
            return h * 3600 + m * 60 + s
        except ValueError:
            print(f"[ERROR] Failed to parse HH:MM:SS components from '{val_str}'")
            return None
            
    # 3. D:HH:MM:SS format support
    if len(parts) == 4:
        try:
            d = int(parts[0])
            h = int(parts[1])
            m = int(parts[2])
            s = int(parts[3])
            return d * 86400 + h * 3600 + m * 60 + s
        except ValueError:
            print(f"[ERROR] Failed to parse D:HH:MM:SS components from '{val_str}'")
            return None
            
    print(f"[ERROR] Invalid walltime format: '{val_str}'")
    return None


def parse_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return None


def build_record(row: dict[str, Any]) -> dict[str, Any] | None:
    submit_time = parse_pbs_time(row.get("qtime"))
    start_time = parse_pbs_time(row.get("stime"))
    if not submit_time or not start_time:
        return None
    if not (OVERLAP_START <= submit_time <= OVERLAP_END and OVERLAP_START <= start_time <= OVERLAP_END):
        return None
    
    walltime_val = row.get("resources_used.walltime")
    runtime = parse_walltime(walltime_val)
    if runtime is None:
        print(f"[WARNING] Job {row.get('job_id')} has missing or invalid walltime '{walltime_val}'. Skipping job.")
        return None
        
    opt = {
        "job_id": row.get("job_id"),
        "cpu_req": parse_int(row.get("Resource_List.ncpus")) or 0,
        "gpu_req": parse_int(row.get("Resource_List.ngpus")) or 0,
        "estimated_runtime_seconds": runtime,
        "submit_offset_seconds": int((submit_time - OVERLAP_START).total_seconds()),
        "queue": row.get("queue"),
    }
    return {
        "job_id": row.get("job_id"),
        "queue": row.get("queue"),
        "submit_time": submit_time.isoformat(sep=" "),
        "start_time": start_time.isoformat(sep=" "),
        "end_time": row.get("etime"),
        "optimization": opt,
        "requested": {
            "ncpus": parse_int(row.get("Resource_List.ncpus")) or 0,
            "ngpus": parse_int(row.get("Resource_List.ngpus")) or 0,
        },
        "raw": {
            "job_id": row.get("job_id"),
            "queue": row.get("queue"),
        },
    }


def main() -> None:
    args = parse_args()
    input_path = resolve_path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = cpu = gpu = 0
    min_submit = None
    max_start = None
    with input_path.open("r", encoding="utf-8") as src, output_path.open("w", encoding="utf-8") as dst:
        for line in src:
            row = json.loads(line)
            record = build_record(row)
            if record is None:
                continue
            count += 1
            if int(record["optimization"]["gpu_req"]) > 0:
                gpu += 1
            else:
                cpu += 1
            submit_time = record["submit_time"]
            start_time = record["start_time"]
            min_submit = submit_time if min_submit is None or submit_time < min_submit else min_submit
            max_start = start_time if max_start is None or start_time > max_start else max_start
            dst.write(json.dumps(record) + "\n")

    summary = [
        "# Overlap Dataset Summary",
        "",
        f"- job count: {count}",
        f"- CPU jobs: {cpu}",
        f"- GPU jobs: {gpu}",
        f"- submit/start date range: {min_submit} to {max_start}",
    ]
    Path(args.summary).write_text("\n".join(summary), encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Wrote {args.summary}")


if __name__ == "__main__":
    main()
