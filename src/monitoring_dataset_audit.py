#!/usr/bin/env python3
"""Audit monitoring table coverage for cluster-state reconstruction."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from path_utils import DATA_DIR, REPORTS_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", default=str(DATA_DIR / "nodes.csv"), help="nodes.csv path")
    parser.add_argument("--node-status", default=str(DATA_DIR / "node_status.csv"), help="node_status.csv path")
    parser.add_argument("--node-metrics", default=str(DATA_DIR / "node_metrics.csv"), help="node_metrics.csv path")
    parser.add_argument("--cpu-metrics", default=str(DATA_DIR / "cpu_metrics.csv"), help="cpu_metrics.csv path")
    parser.add_argument("--output", default=str(REPORTS_DIR / "monitoring_dataset_audit.md"), help="Markdown output path")
    return parser.parse_args()


def _parse_dt(value: str) -> datetime:
    text = str(value).strip().replace(" ", "T")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                pass
        raise


def audit_csv(path: Path, timestamp_field: str = "timestamp", distinct_field: str | None = None) -> dict[str, Any]:
    min_ts = None
    max_ts = None
    count = 0
    distinct_values = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            count += 1
            ts = row.get(timestamp_field)
            if ts:
                parsed = _parse_dt(ts)
                min_ts = parsed if min_ts is None or parsed < min_ts else min_ts
                max_ts = parsed if max_ts is None or parsed > max_ts else max_ts
            if distinct_field and row.get(distinct_field):
                distinct_values.add(row[distinct_field])
    return {
        "path": str(path),
        "count": count,
        "min_timestamp": min_ts.isoformat(sep=" ") if min_ts else None,
        "max_timestamp": max_ts.isoformat(sep=" ") if max_ts else None,
        "distinct_count": len(distinct_values) if distinct_field else None,
    }


def main() -> None:
    args = parse_args()
    nodes = audit_csv(Path(args.nodes), distinct_field="node_id")
    status = audit_csv(Path(args.node_status), distinct_field="node_id")
    metrics = audit_csv(Path(args.node_metrics))
    cpu = audit_csv(Path(args.cpu_metrics))

    lines = [
        "# Monitoring Dataset Audit",
        "",
        "| Table | MIN(timestamp) | MAX(timestamp) | COUNT(*) | Distinct nodes |",
        "|---|---|---|---:|---:|",
        f"| nodes.csv | {nodes['min_timestamp'] or 'n/a'} | {nodes['max_timestamp'] or 'n/a'} | {nodes['count']} | {nodes['distinct_count'] or 'n/a'} |",
        f"| node_status.csv | {status['min_timestamp'] or 'n/a'} | {status['max_timestamp'] or 'n/a'} | {status['count']} | {status['distinct_count'] or 'n/a'} |",
        f"| node_metrics.csv | {metrics['min_timestamp'] or 'n/a'} | {metrics['max_timestamp'] or 'n/a'} | {metrics['count']} | n/a |",
        f"| cpu_metrics.csv | {cpu['min_timestamp'] or 'n/a'} | {cpu['max_timestamp'] or 'n/a'} | {cpu['count']} | n/a |",
        "",
        "## Notes",
        f"- node_status distinct node count: {status['distinct_count']}",
        "- Coverage period should be chosen from the overlap of these timestamp ranges and the job windows used for benchmark extraction.",
    ]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
