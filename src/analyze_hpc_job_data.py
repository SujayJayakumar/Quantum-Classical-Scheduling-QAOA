#!/usr/bin/env python3
"""Profile PBS job-history JSONL data for QUBO scheduling design.

The script streams the JSONL file, so it is safe for multi-GB traces.
It writes a compact Markdown report plus a machine-readable JSON summary.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from path_utils import REPO_ROOT, REPORTS_DIR, VALIDATION_DIR, resolve_path


TIME_FIELDS = ("ctime", "qtime", "etime", "stime", "mtime")
RESOURCE_FIELDS = (
    "Resource_List.ncpus",
    "Resource_List.ngpus",
    "Resource_List.nodect",
    "Resource_List.mpiprocs",
    "Resource_List.mem",
    "Resource_List.walltime",
    "resources_used.ncpus",
    "resources_used.mem",
    "resources_used.vmem",
    "resources_used.walltime",
    "resources_used.cput",
    "resources_used.cpupercent",
)

CORE_FIELDS = (
    "job_id",
    "Job_Name",
    "Job_Owner",
    "euser",
    "egroup",
    "queue",
    "job_state",
    "Priority",
    "qtime",
    "stime",
    "etime",
    "mtime",
    "resources_used.walltime",
    "Resource_List.walltime",
    "Resource_List.ncpus",
    "Resource_List.ngpus",
    "Resource_List.nodect",
    "Resource_List.mpiprocs",
    "resources_used.mem",
    "Resource_List.mem",
    "exec_host",
    "exec_vnode",
    "Resource_List.select",
    "schedselect",
    "Exit_status",
    "project",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(REPO_ROOT / "data" / "merged_all_jobs.jsonl"), help="JSONL job trace path")
    parser.add_argument("--markdown", default=str(REPORTS_DIR / "dataset_metadata.md"), help="Markdown report path")
    parser.add_argument("--json", default=str(VALIDATION_DIR / "dataset_metadata_summary.json"), help="JSON summary path")
    parser.add_argument("--sample-limit", type=int, default=5, help="Example values per field")
    parser.add_argument("--candidate-limit", type=int, default=25, help="Conflict candidate rows to report")
    return parser.parse_args()


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    for fmt in ("%a %b %d %H:%M:%S %Y",):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    return None


def parse_hms(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    match = re.fullmatch(r"(?:(\d+):)?(\d{1,2}):(\d{1,2})", text)
    if not match:
        return None
    first, minutes, seconds = match.groups()
    hours = int(first or 0)
    return hours * 3600 + int(minutes) * 60 + int(seconds)


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


def parse_memory_kb(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    match = re.fullmatch(r"([0-9.]+)\s*([kmgtp]?b?)?", text)
    if not match:
        return parse_int(text)
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


def parse_resource_from_select(text: Any, key: str) -> int | None:
    if not isinstance(text, str):
        return None
    total = 0
    found = False
    for chunk in text.strip().split("+"):
        parts = chunk.split(":")
        multiplier = parse_int(parts[0]) if parts else 1
        if multiplier is None:
            multiplier = 1
        per_chunk = 0
        for part in parts[1:]:
            if "=" not in part:
                continue
            name, raw_value = part.split("=", 1)
            if name == key:
                value = parse_int(raw_value)
                if value is not None:
                    per_chunk += value
                    found = True
        total += multiplier * per_chunk
    return total if found else None


def first_node(exec_host: Any, exec_vnode: Any) -> str | None:
    if isinstance(exec_host, str) and exec_host.strip():
        return exec_host.strip().split("+")[0].split("/")[0]
    if isinstance(exec_vnode, str) and exec_vnode.strip():
        match = re.search(r"\(?([^:)+]+)", exec_vnode)
        if match:
            return match.group(1)
    return None


@dataclass
class NumericStats:
    count: int = 0
    missing: int = 0
    min_value: float | None = None
    max_value: float | None = None
    total: float = 0.0
    values_for_quantiles: list[float] = field(default_factory=list)

    def add(self, value: float | None) -> None:
        if value is None or isinstance(value, bool) or math.isnan(float(value)):
            self.missing += 1
            return
        value = float(value)
        self.count += 1
        self.total += value
        self.min_value = value if self.min_value is None else min(self.min_value, value)
        self.max_value = value if self.max_value is None else max(self.max_value, value)
        self.values_for_quantiles.append(value)

    def as_dict(self) -> dict[str, float | int | None]:
        values = sorted(self.values_for_quantiles)
        return {
            "count": self.count,
            "missing": self.missing,
            "min": self.min_value,
            "p50": percentile(values, 0.50),
            "p90": percentile(values, 0.90),
            "p95": percentile(values, 0.95),
            "max": self.max_value,
            "mean": self.total / self.count if self.count else None,
        }


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    idx = int(round((len(values) - 1) * p))
    return values[idx]


def fmt_number(value: float | int | None, suffix: str = "") -> str:
    if value is None:
        return "-"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value:,}{suffix}"


def fmt_seconds(value: float | int | None) -> str:
    if value is None:
        return "-"
    value = int(value)
    days, rem = divmod(value, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    if days:
        return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def classify_field(field_name: str, present_count: int, total: int) -> tuple[str, str]:
    present = "Yes" if present_count else "No"
    coverage = present_count / total if total else 0.0
    weak = coverage < 0.50
    use = "No"
    if field_name in {"job_id", "Job_Name", "Job_Owner", "euser", "egroup", "project"}:
        use = "No"
    elif field_name in {"queue", "job_state", "Exit_status"}:
        use = "Maybe"
    elif field_name in {"qtime", "stime", "etime", "mtime"}:
        use = "Yes"
    elif field_name in {
        "resources_used.walltime",
        "Resource_List.walltime",
        "Resource_List.ncpus",
        "Resource_List.ngpus",
        "Resource_List.nodect",
        "Resource_List.mpiprocs",
        "resources_used.mem",
        "Resource_List.mem",
        "exec_host",
        "exec_vnode",
        "Resource_List.select",
        "schedselect",
    }:
        use = "Yes"
    elif field_name == "Priority":
        use = "Maybe"
    if weak and use == "Yes":
        use = "Maybe"
    return present, use


def qubo_note(field_name: str) -> str:
    notes = {
        "job_id": "Identifier only.",
        "Job_Name": "Useful for grouping; avoid as optimization variable.",
        "Job_Owner": "Fair-share/user grouping if needed.",
        "euser": "Fair-share/user grouping if needed.",
        "egroup": "Group fair-share if needed.",
        "queue": "Partition/eligibility or queue-class penalties.",
        "job_state": "Filter completed/running/queued records.",
        "Priority": "Priority objective weight, but values may be uninformative if mostly zero.",
        "qtime": "Submit/queue time; supports release-time and wait-time terms.",
        "stime": "Observed start time; supports replay windows and conflict detection.",
        "etime": "Eligibility time; close to submit time in PBS traces.",
        "mtime": "Last modified/end proxy for finished jobs.",
        "resources_used.walltime": "Observed runtime cost.",
        "Resource_List.walltime": "Requested walltime/deadline bound.",
        "Resource_List.ncpus": "CPU capacity constraint.",
        "Resource_List.ngpus": "GPU capacity/eligibility constraint.",
        "Resource_List.nodect": "Node capacity constraint.",
        "Resource_List.mpiprocs": "MPI/process capacity term.",
        "resources_used.mem": "Observed memory demand; useful if requested memory is sparse.",
        "Resource_List.mem": "Requested memory capacity constraint when present.",
        "exec_host": "Observed allocation; use for overlap/conflict mining.",
        "exec_vnode": "Observed vnode resources; use for allocation and GPU/node constraints.",
        "Resource_List.select": "Parseable resource request; fills missing CPU/GPU/node fields.",
        "schedselect": "Expanded resource request; useful fallback for resources.",
        "Exit_status": "Filter failed jobs or penalize risky classes.",
        "project": "Project/fair-share grouping if useful.",
    }
    return notes.get(field_name, "")


def main() -> None:
    args = parse_args()
    input_path = resolve_path(args.input)
    markdown_path = Path(args.markdown)
    json_path = Path(args.json)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    bad_json = 0
    field_counts: Counter[str] = Counter()
    null_counts: Counter[str] = Counter()
    type_counts: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[str]] = defaultdict(list)
    categorical: dict[str, Counter[str]] = defaultdict(Counter)

    numeric_stats = {
        "requested_ncpus": NumericStats(),
        "requested_ngpus": NumericStats(),
        "requested_nodes": NumericStats(),
        "requested_mpiprocs": NumericStats(),
        "used_ncpus": NumericStats(),
        "used_mem_gib": NumericStats(),
        "used_vmem_gib": NumericStats(),
        "requested_walltime_seconds": NumericStats(),
        "used_walltime_seconds": NumericStats(),
        "wait_seconds": NumericStats(),
        "turnaround_seconds": NumericStats(),
        "priority": NumericStats(),
        "cpupercent": NumericStats(),
    }

    min_time: dict[str, datetime] = {}
    max_time: dict[str, datetime] = {}
    queue_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    user_counts: Counter[str] = Counter()
    project_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    host_counts: Counter[str] = Counter()
    gpu_jobs = 0
    cpu_only_jobs = 0
    usable_finished_jobs = 0
    overlap_events: list[dict[str, Any]] = []
    running_by_host: dict[str, list[dict[str, Any]]] = defaultdict(list)

    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                bad_json += 1
                continue

            total += 1
            for key, value in row.items():
                field_counts[key] += 1
                if value is None or value == "":
                    null_counts[key] += 1
                type_counts[key][type(value).__name__] += 1
                if len(examples[key]) < args.sample_limit:
                    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                    text = " ".join(text.split())
                    if text not in examples[key]:
                        examples[key].append(text[:160])

            for key in ("queue", "job_state", "Exit_status", "queue_type"):
                if key in row:
                    categorical[key][str(row[key])] += 1
            queue_counts[str(row.get("queue", ""))] += 1
            state_counts[str(row.get("job_state", ""))] += 1
            user_counts[str(row.get("euser") or row.get("Job_Owner", "")).split("@")[0]] += 1
            project_counts[str(row.get("project", ""))] += 1
            for source in row.get("source_files", []) or []:
                source_counts[str(source)] += 1

            for time_field in TIME_FIELDS:
                parsed = parse_time(row.get(time_field))
                if parsed:
                    min_time[time_field] = min(parsed, min_time.get(time_field, parsed))
                    max_time[time_field] = max(parsed, max_time.get(time_field, parsed))

            requested_ncpus = parse_int(row.get("Resource_List.ncpus"))
            requested_ngpus = parse_int(row.get("Resource_List.ngpus"))
            requested_nodes = parse_int(row.get("Resource_List.nodect"))
            requested_mpiprocs = parse_int(row.get("Resource_List.mpiprocs"))
            for source_key in ("Resource_List.select", "schedselect", "exec_vnode"):
                requested_ncpus = requested_ncpus if requested_ncpus is not None else parse_resource_from_select(row.get(source_key), "ncpus")
                requested_ngpus = requested_ngpus if requested_ngpus is not None else parse_resource_from_select(row.get(source_key), "ngpus")
                requested_mpiprocs = requested_mpiprocs if requested_mpiprocs is not None else parse_resource_from_select(row.get(source_key), "mpiprocs")

            used_walltime = parse_hms(row.get("resources_used.walltime"))
            requested_walltime = parse_hms(row.get("Resource_List.walltime"))
            qtime = parse_time(row.get("qtime"))
            stime = parse_time(row.get("stime"))
            mtime = parse_time(row.get("mtime"))
            wait_seconds = (stime - qtime).total_seconds() if qtime and stime else None
            turnaround_seconds = (mtime - qtime).total_seconds() if qtime and mtime else None
            used_mem_gib = parse_memory_kb(row.get("resources_used.mem"))
            used_vmem_gib = parse_memory_kb(row.get("resources_used.vmem"))
            used_mem_gib = used_mem_gib / (1024**2) if used_mem_gib is not None else None
            used_vmem_gib = used_vmem_gib / (1024**2) if used_vmem_gib is not None else None

            numeric_stats["requested_ncpus"].add(requested_ncpus)
            numeric_stats["requested_ngpus"].add(requested_ngpus)
            numeric_stats["requested_nodes"].add(requested_nodes)
            numeric_stats["requested_mpiprocs"].add(requested_mpiprocs)
            numeric_stats["used_ncpus"].add(parse_int(row.get("resources_used.ncpus")))
            numeric_stats["used_mem_gib"].add(used_mem_gib)
            numeric_stats["used_vmem_gib"].add(used_vmem_gib)
            numeric_stats["requested_walltime_seconds"].add(requested_walltime)
            numeric_stats["used_walltime_seconds"].add(used_walltime)
            numeric_stats["wait_seconds"].add(wait_seconds)
            numeric_stats["turnaround_seconds"].add(turnaround_seconds)
            numeric_stats["priority"].add(parse_int(row.get("Priority")))
            numeric_stats["cpupercent"].add(parse_int(row.get("resources_used.cpupercent")))

            if requested_ngpus and requested_ngpus > 0:
                gpu_jobs += 1
            elif requested_ngpus == 0:
                cpu_only_jobs += 1

            node = first_node(row.get("exec_host"), row.get("exec_vnode"))
            if node:
                host_counts[node] += 1
            if stime and used_walltime and node:
                end_ts = stime.timestamp() + used_walltime
                start_ts = stime.timestamp()
                record = {
                    "job_id": row.get("job_id"),
                    "queue": row.get("queue"),
                    "node": node,
                    "start": stime.isoformat(sep=" "),
                    "end_ts": end_ts,
                    "start_ts": start_ts,
                    "ngpus": requested_ngpus or 0,
                    "ncpus": requested_ncpus or 0,
                    "runtime_seconds": used_walltime,
                }
                still_running = [r for r in running_by_host[node] if r["end_ts"] > start_ts]
                if still_running and len(overlap_events) < args.candidate_limit:
                    overlap_events.append(
                        {
                            "node": node,
                            "new_job": record["job_id"],
                            "new_start": record["start"],
                            "overlaps": [
                                {
                                    "job_id": r["job_id"],
                                    "start": r["start"],
                                    "overlap_seconds": int(min(r["end_ts"], end_ts) - start_ts),
                                    "ngpus": r["ngpus"],
                                    "ncpus": r["ncpus"],
                                }
                                for r in still_running[:5]
                            ],
                        }
                    )
                running_by_host[node] = still_running + [record]
                usable_finished_jobs += 1

    numeric_summary = {key: value.as_dict() for key, value in numeric_stats.items()}
    all_fields = sorted(field_counts)
    core_table = []
    for field_name in CORE_FIELDS:
        present_count = field_counts.get(field_name, 0)
        present, use = classify_field(field_name, present_count, total)
        core_table.append(
            {
                "field": field_name,
                "present": present,
                "coverage": present_count / total if total else 0.0,
                "use_in_qubo": use,
                "note": qubo_note(field_name),
            }
        )

    summary = {
        "input_path": str(input_path),
        "total_records": total,
        "bad_json_lines": bad_json,
        "field_count": len(all_fields),
        "fields": {key: {"present": field_counts[key], "types": dict(type_counts[key]), "examples": examples[key]} for key in all_fields},
        "numeric_summary": numeric_summary,
        "time_ranges": {key: {"min": min_time[key].isoformat(sep=" "), "max": max_time[key].isoformat(sep=" ")} for key in sorted(min_time)},
        "top_queues": queue_counts.most_common(20),
        "top_states": state_counts.most_common(20),
        "top_users": user_counts.most_common(20),
        "top_projects": project_counts.most_common(20),
        "top_sources": source_counts.most_common(20),
        "top_hosts": host_counts.most_common(20),
        "gpu_jobs": gpu_jobs,
        "cpu_only_jobs": cpu_only_jobs,
        "usable_finished_jobs_with_start_runtime_host": usable_finished_jobs,
        "qubo_field_table": core_table,
        "overlap_examples": overlap_events,
    }

    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(summary), encoding="utf-8")
    print(f"Wrote {markdown_path} and {json_path}")
    print(f"Records: {total:,}; fields: {len(all_fields):,}; bad JSON lines: {bad_json:,}")


def render_counter(items: list[tuple[str, int]]) -> str:
    if not items:
        return "- none\n"
    return "\n".join(f"- `{key or '<missing>'}`: {value:,}" for key, value in items)


def render_stats_table(numeric_summary: dict[str, dict[str, Any]]) -> str:
    lines = ["| Metric | Count | Missing | Min | P50 | P90 | P95 | Max | Mean |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    seconds_fields = {"requested_walltime_seconds", "used_walltime_seconds", "wait_seconds", "turnaround_seconds"}
    for key, stats in numeric_summary.items():
        formatter = fmt_seconds if key in seconds_fields else fmt_number
        lines.append(
            "| "
            + " | ".join(
                [
                    key,
                    fmt_number(stats["count"]),
                    fmt_number(stats["missing"]),
                    formatter(stats["min"]),
                    formatter(stats["p50"]),
                    formatter(stats["p90"]),
                    formatter(stats["p95"]),
                    formatter(stats["max"]),
                    formatter(stats["mean"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# M1 Dataset Metadata: HPC Job Trace\n")
    lines.append("## Dataset Snapshot\n")
    lines.append(f"- Source file: `{summary['input_path']}`")
    lines.append(f"- Records: {summary['total_records']:,}")
    lines.append(f"- JSON parse failures: {summary['bad_json_lines']:,}")
    lines.append(f"- Distinct fields: {summary['field_count']:,}")
    lines.append(f"- GPU-requesting jobs: {summary['gpu_jobs']:,}")
    lines.append(f"- CPU-only jobs with explicit zero GPUs: {summary['cpu_only_jobs']:,}")
    lines.append(f"- Jobs with start time, runtime, and host allocation: {summary['usable_finished_jobs_with_start_runtime_host']:,}\n")

    lines.append("## Time Coverage\n")
    for key, value in summary["time_ranges"].items():
        lines.append(f"- `{key}`: {value['min']} to {value['max']}")
    lines.append("")

    lines.append("## M1 Field-to-QUBO Table\n")
    lines.append("| Field | Present? | Coverage | Use in QUBO? | Why / How |")
    lines.append("|---|---|---:|---|---|")
    for row in summary["qubo_field_table"]:
        lines.append(
            f"| `{row['field']}` | {row['present']} | {row['coverage']:.1%} | {row['use_in_qubo']} | {row['note']} |"
        )
    lines.append("")

    lines.append("## Numeric / Duration Profile\n")
    lines.append(render_stats_table(summary["numeric_summary"]))
    lines.append("")

    lines.append("## Key Categorical Distributions\n")
    lines.append("### Queues\n")
    lines.append(render_counter(summary["top_queues"]))
    lines.append("\n### Job States\n")
    lines.append(render_counter(summary["top_states"]))
    lines.append("\n### Users\n")
    lines.append(render_counter(summary["top_users"]))
    lines.append("\n### Projects\n")
    lines.append(render_counter(summary["top_projects"]))
    lines.append("\n### Source Files\n")
    lines.append(render_counter(summary["top_sources"]))
    lines.append("\n### Allocated Nodes\n")
    lines.append(render_counter(summary["top_hosts"]))
    lines.append("")

    lines.append("## Initial QUBO-Relevant Interpretation\n")
    lines.append("- Strong constraint candidates: CPU count, GPU count, node count, requested walltime, observed runtime, and observed allocation host/vnode.")
    lines.append("- Objective candidates: minimize waiting time, minimize turnaround, penalize long runtimes, and optionally reward priority or queue class.")
    lines.append("- Filtering candidates: finished jobs with valid `qtime`, `stime`, `resources_used.walltime`, and `exec_host`/`exec_vnode` are the cleanest replay substrate.")
    lines.append("- Memory is useful if requested memory exists; otherwise observed memory can support analysis but is weaker as a scheduling constraint because it is known after execution.")
    lines.append("- Priority should be inspected before use; if it is mostly zero, it will not provide a meaningful QUBO weight without an inferred priority scheme.")
    lines.append("- Some rare field names look like shell/environment fragments from the merge process; treat them as data-quality artifacts, not scheduling features.")
    lines.append("- `mtime - qtime` can be negative for a small number of records, so observed runtime from `resources_used.walltime` is safer than deriving runtime from timestamps.")
    lines.append("")

    lines.append("## Example Same-Node Overlap Windows\n")
    if not summary["overlap_examples"]:
        lines.append("- No overlaps found in the first pass.")
    else:
        for item in summary["overlap_examples"][:10]:
            overlaps = ", ".join(
                f"{overlap['job_id']} ({fmt_seconds(overlap['overlap_seconds'])})"
                for overlap in item["overlaps"]
            )
            lines.append(f"- Node `{item['node']}`: `{item['new_job']}` at {item['new_start']} overlaps {overlaps}")
    lines.append("")

    lines.append("## All Fields\n")
    lines.append("| Field | Present Count | Types | Examples |")
    lines.append("|---|---:|---|---|")
    for field_name, info in summary["fields"].items():
        type_text = ", ".join(f"{key}:{value}" for key, value in info["types"].items())
        example_text = "<br>".join(f"`{example}`" for example in info["examples"])
        lines.append(f"| `{field_name}` | {info['present']:,} | {type_text} | {example_text} |")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
