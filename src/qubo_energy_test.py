#!/usr/bin/env python3
"""Brute-force QUBO energy validation for a tiny mapping-only problem.

This script enumerates every binary assignment for a 2-job / 2-node instance,
computes the energy contribution of each QUBO term, and checks that:

- valid assignments have lower energy
- invalid assignments are penalized
- increasing penalty coefficients widens the energy gap

The goal is mathematical validation of the QUBO formulation, not optimization.
"""

from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from path_utils import VALIDATION_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(VALIDATION_DIR / "qubo_energy_report.json"), help="Output report path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--debug", action="store_true", help="Print a short text summary")
    return parser.parse_args()


@dataclass(frozen=True)
class Job:
    job_id: str
    cpu_req: int
    gpu_req: int
    runtime: float


@dataclass(frozen=True)
class Node:
    node_id: str
    cpu_capacity: int
    gpu_capacity: int


JOBS = [
    Job("j0", cpu_req=1, gpu_req=0, runtime=3.0),
    Job("j1", cpu_req=2, gpu_req=1, runtime=5.0),
]

NODES = [
    Node("n0", cpu_capacity=4, gpu_capacity=1),
    Node("n1", cpu_capacity=2, gpu_capacity=0),
]


def variable_order(jobs: list[Job], nodes: list[Node]) -> list[tuple[int, int, str]]:
    return [(i, j, f"x({i},{j})") for i in range(len(jobs)) for j in range(len(nodes))]


def bits_to_assignment(bits: tuple[int, ...], jobs: list[Job], nodes: list[Node]) -> dict[str, str]:
    assignment: dict[str, str] = {}
    idx = 0
    for i, job in enumerate(jobs):
        for j, node in enumerate(nodes):
            if bits[idx]:
                assignment[job.job_id] = node.node_id
            idx += 1
    return assignment


def assignment_details(bits: tuple[int, ...], jobs: list[Job], nodes: list[Node]) -> dict[str, Any]:
    job_to_nodes: dict[str, list[str]] = {job.job_id: [] for job in jobs}
    node_cpu = {node.node_id: 0 for node in nodes}
    node_gpu = {node.node_id: 0 for node in nodes}
    idx = 0
    for i, job in enumerate(jobs):
        for j, node in enumerate(nodes):
            if bits[idx]:
                job_to_nodes[job.job_id].append(node.node_id)
                node_cpu[node.node_id] += job.cpu_req
                node_gpu[node.node_id] += job.gpu_req
            idx += 1
    return {
        "job_to_nodes": job_to_nodes,
        "node_cpu": node_cpu,
        "node_gpu": node_gpu,
    }


def valid_assignment(bits: tuple[int, ...], jobs: list[Job], nodes: list[Node]) -> bool:
    details = assignment_details(bits, jobs, nodes)
    for job in jobs:
        if len(details["job_to_nodes"][job.job_id]) != 1:
            return False
    for node in nodes:
        if details["node_cpu"][node.node_id] > node.cpu_capacity:
            return False
        if details["node_gpu"][node.node_id] > node.gpu_capacity:
            return False
    return True


def objective_energy(bits: tuple[int, ...], jobs: list[Job], nodes: list[Node], objective_scale: float) -> float:
    energy = 0.0
    idx = 0
    for job in jobs:
        for _node in nodes:
            energy += objective_scale * job.runtime * bits[idx]
            idx += 1
    return energy


def assignment_penalty(bits: tuple[int, ...], jobs: list[Job], nodes: list[Node], alpha_assign: float) -> float:
    penalty = 0.0
    idx = 0
    for job in jobs:
        s = 0
        for _node in nodes:
            s += bits[idx]
            idx += 1
        penalty += alpha_assign * (1 - s) ** 2
    return penalty


def capacity_penalty(bits: tuple[int, ...], jobs: list[Job], nodes: list[Node], alpha_capacity: float) -> float:
    penalty = 0.0
    for j, node in enumerate(nodes):
        cpu_load = 0
        gpu_load = 0
        for i, job in enumerate(jobs):
            bit_index = i * len(nodes) + j
            if bits[bit_index]:
                cpu_load += job.cpu_req
                gpu_load += job.gpu_req
        cpu_over = max(0, cpu_load - node.cpu_capacity)
        gpu_over = max(0, gpu_load - node.gpu_capacity)
        penalty += alpha_capacity * (cpu_over**2 + gpu_over**2)
    return penalty


def total_energy(bits: tuple[int, ...], jobs: list[Job], nodes: list[Node], alpha_assign: float, alpha_capacity: float, objective_scale: float) -> dict[str, float]:
    obj = objective_energy(bits, jobs, nodes, objective_scale)
    assign = assignment_penalty(bits, jobs, nodes, alpha_assign)
    cap = capacity_penalty(bits, jobs, nodes, alpha_capacity)
    return {
        "objective": obj,
        "assignment": assign,
        "capacity": cap,
        "total": obj + assign + cap,
    }


def enumerate_states(
    jobs: list[Job],
    nodes: list[Node],
    alpha_assign: float,
    alpha_capacity: float,
    objective_scale: float,
) -> list[dict[str, Any]]:
    rows = []
    for bits in itertools.product([0, 1], repeat=len(jobs) * len(nodes)):
        energies = total_energy(bits, jobs, nodes, alpha_assign, alpha_capacity, objective_scale)
        details = assignment_details(bits, jobs, nodes)
        rows.append(
            {
                "bits": "".join(str(bit) for bit in bits),
                "assignment": bits_to_assignment(bits, jobs, nodes),
                "job_to_nodes": details["job_to_nodes"],
                "node_cpu": details["node_cpu"],
                "node_gpu": details["node_gpu"],
                "valid": valid_assignment(bits, jobs, nodes),
                **energies,
            }
        )
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid_rows = [row for row in rows if row["valid"]]
    invalid_rows = [row for row in rows if not row["valid"]]
    best_valid = min(valid_rows, key=lambda row: row["total"]) if valid_rows else None
    best_invalid = min(invalid_rows, key=lambda row: row["total"]) if invalid_rows else None
    return {
        "valid_count": len(valid_rows),
        "invalid_count": len(invalid_rows),
        "best_valid_total": best_valid["total"] if best_valid else None,
        "best_invalid_total": best_invalid["total"] if best_invalid else None,
        "energy_gap": (best_invalid["total"] - best_valid["total"]) if best_valid and best_invalid else None,
        "valid_lower_than_invalid": bool(best_valid and best_invalid and best_valid["total"] < best_invalid["total"]),
    }


def build_report() -> dict[str, Any]:
    penalty_sweeps = [
        {"alpha_assign": 10.0, "alpha_capacity": 10.0, "objective_scale": 0.1},
        {"alpha_assign": 20.0, "alpha_capacity": 20.0, "objective_scale": 0.1},
        {"alpha_assign": 40.0, "alpha_capacity": 40.0, "objective_scale": 0.1},
    ]
    sweeps = []
    for params in penalty_sweeps:
        rows = enumerate_states(JOBS, NODES, **params)
        sweeps.append(
            {
                "parameters": params,
                "summary": summarize(rows),
                "rows": rows,
            }
        )
    return {
        "problem": {
            "jobs": [job.__dict__ for job in JOBS],
            "nodes": [node.__dict__ for node in NODES],
            "variable_order": variable_order(JOBS, NODES),
        },
        "sweeps": sweeps,
        "verification": {
            "all_sweeps_valid_lower_than_invalid": all(sweep["summary"]["valid_lower_than_invalid"] for sweep in sweeps),
            "gap_increases_with_penalty": (
                sweeps[0]["summary"]["energy_gap"] < sweeps[1]["summary"]["energy_gap"] < sweeps[2]["summary"]["energy_gap"]
            ),
        },
    }


def format_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "bits",
        "valid",
        "objective",
        "assignment",
        "capacity",
        "total",
        "assignment",
        "cpu",
        "gpu",
    ]
    lines = [" | ".join(headers), " | ".join(["---"] * len(headers))]
    for row in rows:
        lines.append(
            " | ".join(
                [
                    row["bits"],
                    str(row["valid"]),
                    f"{row['objective']:.1f}",
                    f"{row['assignment']:.1f}",
                    f"{row['capacity']:.1f}",
                    f"{row['total']:.1f}",
                    str(row["assignment"]),
                    str(row["node_cpu"]),
                    str(row["node_gpu"]),
                ]
            )
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    report = build_report()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True), encoding="utf-8")

    if args.debug:
        print("2-job / 2-node QUBO validation")
        for sweep in report["sweeps"]:
            p = sweep["parameters"]
            s = sweep["summary"]
            print(
                f"alpha_assign={p['alpha_assign']} alpha_capacity={p['alpha_capacity']} "
                f"valid_lower_than_invalid={s['valid_lower_than_invalid']} gap={s['energy_gap']}"
            )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
