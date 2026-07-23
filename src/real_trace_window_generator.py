#!/usr/bin/env python3
"""Generate small real-trace HPC scheduling windows from merged PBS JSONL data.

The output is intentionally close to the next optimization layer:

    jobs = [...]
    nodes = [...]

Jobs are filtered from real completed trace records with valid submit time,
start time, observed runtime, and allocation. Times are normalized relative to
the requested window start so they can become QUBO time-bin indices later.
"""

from __future__ import annotations

import argparse
import json
import pprint
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from path_utils import REPO_ROOT, VALIDATION_DIR, WINDOWS_DIR, resolve_path

PBS_TIME_FORMAT = "%a %b %d %H:%M:%S %Y"
ISO_FORMAT_HINT = "YYYY-MM-DDTHH:MM:SS"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(REPO_ROOT / "data" / "overlap_jobs.jsonl"), help="Input PBS JSONL trace")
    parser.add_argument("--output", default=str(WINDOWS_DIR / "trace_window.json"), help="Output file path")
    parser.add_argument(
        "--format",
        choices=("json", "python"),
        default="json",
        help="Write plain JSON or a Python module containing jobs/nodes variables",
    )
    parser.add_argument("--window-start", required=True, help=f"Window start in {ISO_FORMAT_HINT}")
    parser.add_argument("--window-end", help=f"Window end in {ISO_FORMAT_HINT}")
    parser.add_argument("--duration-minutes", type=int, help="Window duration if --window-end is omitted")
    parser.add_argument(
        "--mode",
        choices=("overlap", "start", "submit"),
        default="overlap",
        help="Select jobs overlapping the window, starting in the window, or submitted in the window",
    )
    parser.add_argument("--queue", action="append", help="Queue filter; may be passed more than once")
    parser.add_argument("--gpu-only", action="store_true", help="Keep only jobs requesting or allocated GPUs")
    parser.add_argument("--cpu-only", action="store_true", help="Keep only jobs without requested or allocated GPUs")
    parser.add_argument("--max-jobs", type=int, help="Limit jobs after sorting")
    parser.add_argument(
        "--sort-by",
        choices=("start", "submit", "runtime", "gpu", "cpu"),
        default="start",
        help="Ordering used before --max-jobs",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args()


def parse_iso(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid datetime `{value}`. Expected {ISO_FORMAT_HINT}") from exc


def parse_pbs_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), PBS_TIME_FORMAT)
    except ValueError:
        return None


def parse_hms(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    match = re.fullmatch(r"(?:(\d+):)?(\d{1,2}):(\d{1,2})", text)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds)


def parse_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_memory_kib(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    match = re.fullmatch(r"([0-9.]+)\s*([kmgtp]?b?)?", text)
    if not match:
        return parse_int(value)
    number = float(match.group(1))
    unit = (match.group(2) or "kb").rstrip("b")
    factor = {
        "": 1,
        "k": 1,
        "m": 1024,
        "g": 1024**2,
        "t": 1024**3,
        "p": 1024**4,
    }.get(unit)
    return None if factor is None else int(number * factor)


def parse_select_total(text: Any, resource_name: str) -> int | None:
    if not isinstance(text, str) or not text.strip():
        return None
    total = 0
    found = False
    for chunk in text.split("+"):
        parts = chunk.strip("()").split(":")
        multiplier = parse_int(parts[0]) if parts else None
        if multiplier is None:
            multiplier = 1
        per_chunk = 0
        for part in parts[1:]:
            if "=" not in part:
                continue
            name, raw_value = part.split("=", 1)
            if name == resource_name:
                value = parse_int(raw_value)
                if value is not None:
                    per_chunk += value
                    found = True
        total += multiplier * per_chunk
    return total if found else None


def parse_exec_vnode(exec_vnode: Any) -> list[dict[str, int | str]]:
    if not isinstance(exec_vnode, str) or not exec_vnode.strip():
        return []
    allocations = []
    for match in re.finditer(r"\(([^)]+)\)", exec_vnode):
        parts = match.group(1).split(":")
        if not parts:
            continue
        node_id = clean_node_id(parts[0])
        resources: dict[str, int | str] = {"node_id": node_id}
        for part in parts[1:]:
            if "=" not in part:
                continue
            key, raw_value = part.split("=", 1)
            parsed = parse_int(raw_value)
            if parsed is not None:
                resources[key] = parsed
        allocations.append(resources)
    return allocations


def clean_node_id(node_id: Any) -> str:
    return "".join(str(node_id or "").split())


def aggregate_allocations(allocations: list[dict[str, int | str]]) -> list[dict[str, int | str]]:
    by_node: dict[str, dict[str, int | str]] = {}
    for allocation in allocations:
        node_id = clean_node_id(allocation.get("node_id"))
        if not node_id:
            continue
        current = by_node.setdefault(node_id, {"node_id": node_id})
        for key, value in allocation.items():
            if key == "node_id":
                continue
            parsed = parse_int(value)
            if parsed is not None:
                current[key] = int(current.get(key, 0) or 0) + parsed
    return list(by_node.values())


def parse_exec_host_nodes(exec_host: Any) -> list[str]:
    if not isinstance(exec_host, str) or not exec_host.strip():
        return []
    nodes = []
    for chunk in exec_host.split("+"):
        node = clean_node_id(chunk.split("/")[0])
        if node and node not in nodes:
            nodes.append(node)
    return nodes


def resource_total(row: dict[str, Any], canonical_field: str, resource_name: str) -> int:
    direct = parse_int(row.get(canonical_field))
    if direct is not None:
        return direct
    for field_name in ("Resource_List.select", "schedselect", "exec_vnode"):
        parsed = parse_select_total(row.get(field_name), resource_name)
        if parsed is not None:
            return parsed
    return 0


def clean_user(row: dict[str, Any]) -> str:
    return str(row.get("euser") or row.get("Job_Owner") or "").split("@")[0]


def build_job(row: dict[str, Any], window_start: datetime) -> dict[str, Any] | None:
    submit_time = parse_pbs_time(row.get("qtime"))
    start_time = parse_pbs_time(row.get("stime"))
    runtime_seconds = parse_hms(row.get("resources_used.walltime"))
    if not submit_time or not start_time or runtime_seconds is None or runtime_seconds <= 0:
        return None

    end_time = start_time + timedelta(seconds=runtime_seconds)
    vnode_allocations = aggregate_allocations(parse_exec_vnode(row.get("exec_vnode")))
    host_nodes = parse_exec_host_nodes(row.get("exec_host"))
    allocated_nodes = [str(item["node_id"]) for item in vnode_allocations]
    for node_id in host_nodes:
        if node_id not in allocated_nodes:
            allocated_nodes.append(node_id)
    if not allocated_nodes:
        return None

    requested_ncpus = resource_total(row, "Resource_List.ncpus", "ncpus")
    requested_ngpus = resource_total(row, "Resource_List.ngpus", "ngpus")
    requested_nodes = parse_int(row.get("Resource_List.nodect")) or len(allocated_nodes)
    requested_mpiprocs = resource_total(row, "Resource_List.mpiprocs", "mpiprocs")
    requested_walltime_seconds = parse_hms(row.get("Resource_List.walltime"))
    requested_mem_kib = parse_memory_kib(row.get("Resource_List.mem"))
    used_mem_kib = parse_memory_kib(row.get("resources_used.mem"))
    used_vmem_kib = parse_memory_kib(row.get("resources_used.vmem"))
    priority = parse_int(row.get("Priority")) or 0
    wait_seconds = max(0, int((start_time - submit_time).total_seconds()))

    return {
        "job_id": row.get("job_id"),
        "name": row.get("Job_Name"),
        "user": clean_user(row),
        "group": row.get("egroup"),
        "queue": row.get("queue"),
        "project": row.get("project"),
        "priority": priority,
        "submit_time": submit_time.isoformat(sep=" "),
        "start_time": start_time.isoformat(sep=" "),
        "end_time": end_time.isoformat(sep=" "),
        "submit_offset_seconds": int((submit_time - window_start).total_seconds()),
        "start_offset_seconds": int((start_time - window_start).total_seconds()),
        "end_offset_seconds": int((end_time - window_start).total_seconds()),
        "runtime_seconds": runtime_seconds,
        "wait_seconds": wait_seconds,
        "optimization": {
            "job_id": row.get("job_id"),
            "cpu_req": requested_ncpus,
            "gpu_req": requested_ngpus,
            "node_req": requested_nodes,
            "mpiprocs_req": requested_mpiprocs,
            "memory_req_kib": requested_mem_kib,
            "submit_offset_seconds": int((submit_time - window_start).total_seconds()),
            "estimated_runtime_seconds": runtime_seconds,
            "estimated_runtime_source": "observed_runtime_proxy",
            "queue": row.get("queue"),
            "priority": priority,
        },
        "history": {
            "actual_submit_time": submit_time.isoformat(sep=" "),
            "actual_start_time": start_time.isoformat(sep=" "),
            "actual_end_time": end_time.isoformat(sep=" "),
            "actual_wait_seconds": wait_seconds,
            "actual_runtime_seconds": runtime_seconds,
            "actual_nodes": allocated_nodes,
            "actual_allocations": vnode_allocations,
        },
        "requested": {
            "nodes": requested_nodes,
            "ncpus": requested_ncpus,
            "ngpus": requested_ngpus,
            "mpiprocs": requested_mpiprocs,
            "walltime_seconds": requested_walltime_seconds,
            "mem_kib": requested_mem_kib,
        },
        "used": {
            "mem_kib": used_mem_kib,
            "vmem_kib": used_vmem_kib,
            "ncpus": parse_int(row.get("resources_used.ncpus")),
            "cpupercent": parse_int(row.get("resources_used.cpupercent")),
        },
        "allocated_nodes": allocated_nodes,
        "allocations": vnode_allocations,
        "raw": {
            "exec_host": row.get("exec_host"),
            "exec_vnode": row.get("exec_vnode"),
            "select": row.get("Resource_List.select"),
            "schedselect": row.get("schedselect"),
            "exit_status": row.get("Exit_status"),
        },
    }


def job_in_window(job: dict[str, Any], window_start: datetime, window_end: datetime, mode: str) -> bool:
    submit_time = datetime.fromisoformat(job["submit_time"])
    start_time = datetime.fromisoformat(job["start_time"])
    end_time = datetime.fromisoformat(job["end_time"])
    if mode == "submit":
        return window_start <= submit_time < window_end
    if mode == "start":
        return window_start <= start_time < window_end
    return start_time < window_end and end_time > window_start


def infer_nodes(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    observed: dict[str, dict[str, Any]] = defaultdict(lambda: {"max_ncpus": 0, "max_ngpus": 0, "job_count": 0})
    for job in jobs:
        allocation_by_node = {str(item["node_id"]): item for item in job["allocations"]}
        for node_id in job["allocated_nodes"]:
            node = observed[node_id]
            node["node_id"] = node_id
            node["job_count"] += 1
            allocation = allocation_by_node.get(node_id, {})
            node["max_ncpus"] = max(node["max_ncpus"], int(allocation.get("ncpus", 0) or 0))
            node["max_ngpus"] = max(node["max_ngpus"], int(allocation.get("ngpus", 0) or 0))

    nodes = []
    for node_id, info in sorted(observed.items()):
        max_ngpus = info["max_ngpus"]
        nodes.append(
            {
                "node_id": node_id,
                "kind": "gpu" if max_ngpus > 0 or "gn" in node_id else "cpu",
                "observed_capacity": {
                    "ncpus": info["max_ncpus"],
                    "ngpus": max_ngpus,
                },
                "job_count_in_window": info["job_count"],
            }
        )
    return nodes


def sort_jobs(jobs: list[dict[str, Any]], sort_by: str) -> list[dict[str, Any]]:
    key_map = {
        "start": lambda job: (job["start_offset_seconds"], job["job_id"]),
        "submit": lambda job: (job["submit_offset_seconds"], job["job_id"]),
        "runtime": lambda job: (-job["runtime_seconds"], job["job_id"]),
        "gpu": lambda job: (-job["requested"]["ngpus"], job["start_offset_seconds"], job["job_id"]),
        "cpu": lambda job: (-job["requested"]["ncpus"], job["start_offset_seconds"], job["job_id"]),
    }
    return sorted(jobs, key=key_map[sort_by])


def write_output(payload: dict[str, Any], output_path: Path, output_format: str, pretty: bool) -> None:
    if output_format == "python":
        text = [
            "# Generated by real_trace_window_generator.py",
            f"metadata = {pprint.pformat(payload['metadata'], sort_dicts=True)}",
            f"jobs = {pprint.pformat(payload['jobs'], sort_dicts=True)}",
            f"nodes = {pprint.pformat(payload['nodes'], sort_dicts=True)}",
            "",
        ]
        output_path.write_text("\n".join(text), encoding="utf-8")
        return

    indent = 2 if pretty else None
    output_path.write_text(json.dumps(payload, indent=indent, sort_keys=True), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.gpu_only and args.cpu_only:
        raise SystemExit("--gpu-only and --cpu-only cannot be used together")

    window_start = parse_iso(args.window_start)
    if args.window_end:
        window_end = parse_iso(args.window_end)
    elif args.duration_minutes:
        window_end = window_start + timedelta(minutes=args.duration_minutes)
    else:
        raise SystemExit("Provide either --window-end or --duration-minutes")
    if window_end <= window_start:
        raise SystemExit("Window end must be after window start")

    input_path = resolve_path(args.input)
    jobs = []
    scanned = 0
    usable = 0
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            scanned += 1
            row = json.loads(line)
            job = build_job(row, window_start)
            if job is None:
                continue
            usable += 1
            if args.queue and job["queue"] not in args.queue:
                continue
            if not job_in_window(job, window_start, window_end, args.mode):
                continue
            has_gpu = job["requested"]["ngpus"] > 0 or any(int(item.get("ngpus", 0) or 0) > 0 for item in job["allocations"])
            if args.gpu_only and not has_gpu:
                continue
            if args.cpu_only and has_gpu:
                continue
            jobs.append(job)

    jobs = sort_jobs(jobs, args.sort_by)
    if args.max_jobs is not None:
        jobs = jobs[: args.max_jobs]
    nodes = infer_nodes(jobs)
    payload = {
        "metadata": {
            "source": str(input_path),
            "window_start": window_start.isoformat(sep=" "),
            "window_end": window_end.isoformat(sep=" "),
            "window_seconds": int((window_end - window_start).total_seconds()),
            "mode": args.mode,
            "queue_filter": args.queue,
            "gpu_only": args.gpu_only,
            "cpu_only": args.cpu_only,
            "max_jobs": args.max_jobs,
            "scanned_records": scanned,
            "usable_records": usable,
            "selected_jobs": len(jobs),
            "selected_nodes": len(nodes),
        },
        "jobs": jobs,
        "nodes": nodes,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_output(payload, output_path, args.format, args.pretty)
    print(f"Wrote {output_path}")
    print(f"Selected {len(jobs):,} jobs and {len(nodes):,} nodes from {usable:,} usable records")


if __name__ == "__main__":
    main()
