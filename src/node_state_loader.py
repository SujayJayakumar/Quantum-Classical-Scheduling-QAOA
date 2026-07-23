#!/usr/bin/env python3
"""Load monitoring tables and reconstruct cluster state near a timestamp."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from path_utils import DATA_DIR


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
        if text.endswith("Z"):
            for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    dt = datetime.strptime(text, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
        raise


def _boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


@dataclass(frozen=True)
class NodeRecord:
    node_id: str
    is_gpu: bool


class NodeStateLoader:
    def __init__(
        self,
        nodes_path: str | Path = DATA_DIR / "nodes.csv",
        status_path: str | Path = DATA_DIR / "node_status.csv",
        tolerance_minutes: int = 5,
    ) -> None:
        self.nodes_path = Path(nodes_path)
        self.status_path = Path(status_path)
        self.tolerance = timedelta(minutes=tolerance_minutes)
        self.nodes = self._load_nodes()
        self.snapshots = self._load_status()

    def _load_nodes(self) -> dict[str, NodeRecord]:
        nodes: dict[str, NodeRecord] = {}
        with self.nodes_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                node_id = str(row.get("node_id") or "").strip()
                if not node_id:
                    continue
                nodes[node_id] = NodeRecord(node_id=node_id, is_gpu=_boolish(row.get("is_gpu")))
        return nodes

    def _load_status(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with self.status_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                node_id = str(row.get("node_id") or "").strip()
                timestamp = str(row.get("timestamp") or "").strip()
                if not node_id or not timestamp:
                    continue
                rows.append(
                    {
                        "node_id": node_id,
                        "timestamp": _parse_dt(timestamp),
                        "health": str(row.get("health") or "").strip().lower(),
                        "state": str(row.get("state") or "").strip().lower(),
                        "job_status": str(row.get("job_status") or "").strip().lower(),
                        "job_ids": str(row.get("job_ids") or "").strip(),
                    }
                )
        rows.sort(key=lambda item: (item["timestamp"], item["node_id"]))
        return rows

    def cluster_nodes(self) -> list[dict[str, Any]]:
        return [
            {
                "node_id": node_id,
                "node_type": "gpu" if record.is_gpu else "cpu",
                "cpu_capacity": 128,
                "gpu_capacity": 4 if record.is_gpu else 0,
            }
            for node_id, record in sorted(self.nodes.items())
        ]

    @lru_cache(maxsize=2048)
    def get_cluster_state(self, timestamp: str | datetime) -> dict[str, Any]:
        ts = _parse_dt(timestamp) if isinstance(timestamp, str) else timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=IST)

        chosen: dict[str, dict[str, Any]] = {}
        best_delta: dict[str, timedelta] = {}
        for row in self.snapshots:
            node_id = row["node_id"]
            delta = abs(row["timestamp"] - ts)
            if delta > self.tolerance:
                continue
            if node_id not in chosen or delta < best_delta[node_id]:
                chosen[node_id] = row
                best_delta[node_id] = delta

        available_cpu_nodes = []
        available_gpu_nodes = []
        busy_nodes = []
        offline_nodes = []
        unavailable_nodes = []

        for node_id, record in self.nodes.items():
            status = chosen.get(node_id)
            if status is None:
                unavailable_nodes.append(node_id)
                continue
            health = status["health"]
            state = status["state"]
            job_status = status["job_status"]
            if health in {"offline", "down"} or state == "unavailable":
                offline_nodes.append(node_id)
                continue
            if state in {"job_busy", "job_exclusive", "partially_free"} or job_status == "running":
                busy_nodes.append(node_id)
            if state in {"free", "partially_free"} and health == "online":
                if record.is_gpu:
                    available_gpu_nodes.append(node_id)
                else:
                    available_cpu_nodes.append(node_id)
            elif state == "job_busy" and health == "online":
                if record.is_gpu:
                    busy_nodes.append(node_id)
                else:
                    busy_nodes.append(node_id)
            else:
                unavailable_nodes.append(node_id)

        return {
            "timestamp": ts.isoformat(sep=" "),
            "available_cpu_nodes": sorted(set(available_cpu_nodes)),
            "available_gpu_nodes": sorted(set(available_gpu_nodes)),
            "busy_nodes": sorted(set(busy_nodes)),
            "offline_nodes": sorted(set(offline_nodes)),
            "unavailable_nodes": sorted(set(unavailable_nodes)),
            "summary": {
                "available_cpu_count": len(set(available_cpu_nodes)),
                "available_gpu_count": len(set(available_gpu_nodes)),
                "busy_count": len(set(busy_nodes)),
                "offline_count": len(set(offline_nodes)),
            },
        }


_DEFAULT_LOADER = NodeStateLoader()


def get_cluster_state(timestamp: str | datetime) -> dict[str, Any]:
    return _DEFAULT_LOADER.get_cluster_state(timestamp)


def get_cluster_state_with_tolerance(timestamp: str | datetime, tolerance_minutes: int) -> dict[str, Any]:
    loader = NodeStateLoader(tolerance_minutes=tolerance_minutes)
    return loader.get_cluster_state(timestamp)
IST = timezone(timedelta(hours=5, minutes=30))
