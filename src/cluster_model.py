from __future__ import annotations

from typing import Any


def generate_cluster_inventory(
    cpu_nodes: int = 410,
    gpu_nodes: int = 12,
    cpu_capacity: int = 128,
    gpu_capacity: int = 4,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for idx in range(cpu_nodes):
        nodes.append(
            {
                "node_id": f"cpu-{idx:03d}",
                "node_type": "cpu",
                "cpu_capacity": cpu_capacity,
                "gpu_capacity": 0,
            }
        )
    for idx in range(gpu_nodes):
        nodes.append(
            {
                "node_id": f"gpu-{idx:03d}",
                "node_type": "gpu",
                "cpu_capacity": cpu_capacity,
                "gpu_capacity": gpu_capacity,
            }
        )
    return nodes

