#!/usr/bin/env python3
"""Build a mapping-only QUBO from job and node structures.

This implements the initial paper-aligned subset:

1. Objective term: execution/runtime cost
2. Assignment uniqueness penalty: each job assigned to exactly one node
3. Capacity penalty: total assigned CPU/GPU demand must not exceed node capacity

Excluded for now:
- communication penalty
- dependency penalty
- feature compatibility penalty
- multi-node jobs

The builder does not solve the QUBO. It only emits:

- variables
- Q matrix
- metadata

Variable indexing is deterministic:

    x(i, j) where i = job index, j = node index

The JSON output shape is:

{
  "variables": {...},
  "Q": [...],
  "metadata": {...}
}
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from path_utils import REPO_ROOT, VALIDATION_DIR, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON or Python file containing jobs/nodes")
    parser.add_argument(
        "--example",
        choices=("2x2", "3x2"),
        help="Build one of the built-in unit-test-sized examples instead of reading input",
    )
    parser.add_argument("--output", default=str(VALIDATION_DIR / "qubo_model.json"), help="Output JSON path")
    parser.add_argument("--alpha-assign", type=float, default=10.0, help="Assignment uniqueness penalty weight")
    parser.add_argument("--alpha-capacity", type=float, default=10.0, help="Capacity penalty weight")
    parser.add_argument("--objective-scale", type=float, default=1.0, help="Objective scaling factor")
    parser.add_argument("--debug", action="store_true", help="Print QUBO diagnostics")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    if path.suffix == ".py":
        spec = importlib.util.spec_from_file_location("qubo_input_module", path)
        if spec is None or spec.loader is None:
            raise SystemExit(f"Could not import {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return {
            "metadata": getattr(module, "metadata", {}),
            "jobs": getattr(module, "jobs"),
            "nodes": getattr(module, "nodes"),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def job_view(job: dict[str, Any]) -> dict[str, Any]:
    opt = job.get("optimization") or {}
    requested = job.get("requested") or {}
    return {
        "job_id": str(opt.get("job_id") or job.get("job_id")),
        "cpu_req": _int(job.get("cpu_req", opt.get("cpu_req", requested.get("ncpus")))),
        "gpu_req": _int(job.get("gpu_req", opt.get("gpu_req", requested.get("ngpus")))),
        "estimated_runtime_seconds": _float(job.get("estimated_runtime_seconds", opt.get("estimated_runtime_seconds", job.get("runtime_seconds", 0.0)))),
        "priority": _float(job.get("priority", opt.get("priority", job.get("priority", 0.0)))),
    }


def node_view(node: dict[str, Any]) -> dict[str, Any]:
    capacity = node.get("capacity") or node.get("observed_capacity") or {}
    cpu_capacity = node.get("cpu_capacity", capacity.get("ncpus"))
    gpu_capacity = node.get("gpu_capacity", capacity.get("ngpus"))
    return {
        "node_id": str(node.get("node_id")),
        "node_type": str(node.get("node_type") or node.get("kind") or ("gpu" if _int(capacity.get("ngpus")) > 0 else "cpu")),
        "cpu_capacity": _int(cpu_capacity),
        "gpu_capacity": _int(gpu_capacity),
    }


def node_cost_proxy(job: dict[str, Any], node: dict[str, Any]) -> float:
    cpu_capacity = node.get("cpu_capacity", node.get("ncpus", 0))
    gpu_capacity = node.get("gpu_capacity", node.get("ngpus", 0))
    capacity_score = max(1.0, float(cpu_capacity + gpu_capacity))
    return float(job["estimated_runtime_seconds"]) / capacity_score


def gpu_compatibility_penalty(job: dict[str, Any], node: dict[str, Any]) -> float:
    return 1.0 if job["gpu_req"] > 0 and node["gpu_capacity"] == 0 else 0.0


def variable_name(i: int, j: int, job_id: str, node_id: str) -> str:
    return f"x({i},{j})_{job_id}_{node_id}"


def is_compatible(job: dict[str, Any], node: dict[str, Any]) -> bool:
    """Check if a job is compatible with a node under resource requirements."""
    # 1. GPU compatibility
    if job["gpu_req"] > 0:
        if node["node_type"] != "gpu" or node["gpu_capacity"] < job["gpu_req"]:
            return False
    # 2. CPU capacity limit
    if job["cpu_req"] > node["cpu_capacity"]:
        return False
    return True


def build_variable_map(jobs: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[tuple[int, int], int]]:
    variables: dict[str, dict[str, Any]] = {}
    index_map: dict[tuple[int, int], int] = {}
    idx = 0
    for i, job in enumerate(jobs):
        for j, node in enumerate(nodes):
            if not is_compatible(job, node):
                continue
            name = variable_name(i, j, job["job_id"], node["node_id"])
            variables[name] = {
                "index": idx,
                "i": i,
                "j": j,
                "job_id": job["job_id"],
                "node_id": node["node_id"],
            }
            index_map[(i, j)] = idx
            idx += 1
    return variables, index_map


def zero_matrix(size: int) -> list[list[float]]:
    return [[0.0 for _ in range(size)] for _ in range(size)]


def add_to_q(Q: list[list[float]], a: int, b: int, value: float) -> None:
    if a <= b:
        Q[a][b] += value
    else:
        Q[b][a] += value


def qubo_energy(bits: list[int] | tuple[int, ...], Q: list[list[float]]) -> float:
    energy = 0.0
    n = len(Q)
    if len(bits) != n:
        raise ValueError(f"Bit vector length {len(bits)} does not match Q size {n}")
    for i in range(n):
        if not bits[i]:
            continue
        for j in range(n):
            if not bits[j]:
                continue
            energy += Q[i][j] if i <= j else 0.0
    return energy


def build_qubo(
    jobs_input: list[dict[str, Any]],
    nodes_input: list[dict[str, Any]],
    alpha_assign: float,
    alpha_capacity: float,
    alpha_gpu_compat: float = 0.0,
    objective_scale: float = 1.0,
) -> dict[str, Any]:
    jobs = [job_view(job) for job in jobs_input]
    nodes = [node_view(node) for node in nodes_input]
    variables, index_map = build_variable_map(jobs, nodes)
    q_size = len(variables)
    Q = zero_matrix(q_size)

    objective_terms = 0
    assignment_terms = 0
    cpu_capacity_terms = 0
    gpu_capacity_terms = 0
    gpu_compatibility_terms = 0

    # A. Objective term: execution/runtime cost
    for name, info in variables.items():
        idx = info["index"]
        i = info["i"]
        j = info["j"]
        job = jobs[i]
        node = nodes[j]
        add_to_q(Q, idx, idx, objective_scale * node_cost_proxy(job, node))
        objective_terms += 1
        if alpha_gpu_compat and gpu_compatibility_penalty(job, node) > 0:
            add_to_q(Q, idx, idx, alpha_gpu_compat)
            gpu_compatibility_terms += 1

    # B. Assignment uniqueness penalty:
    #    alpha_assign * (1 - sum_j x_ij)^2
    # Expands to:
    #    alpha_assign * (1 - sum_j x_ij - 2 * sum_{j<k} x_ij x_ik)
    for i, _job in enumerate(jobs):
        # Find all active node indices j for job i
        active_nodes = [info["j"] for info in variables.values() if info["i"] == i]
        for j in active_nodes:
            idx = index_map[(i, j)]
            add_to_q(Q, idx, idx, -alpha_assign)
            assignment_terms += 1
        for idx_j_pos, j in enumerate(active_nodes):
            for k in active_nodes[idx_j_pos + 1:]:
                idx_j = index_map[(i, j)]
                idx_k = index_map[(i, k)]
                add_to_q(Q, idx_j, idx_k, 2.0 * alpha_assign)
                assignment_terms += 1

    # C. Capacity penalties:
    # Removed under Option B (feasibility-only penalty implemented in decoder).
    _ = alpha_capacity

    metadata = {
        "formulation": "mapping_only_qubo_v2_option_b",
        "reference_alignment": "paper_style_task_node_mapping",
        "included_terms": [
            "objective_runtime_cost",
            "assignment_uniqueness",
            "gpu_compatibility_penalty",
        ],
        "excluded_terms": [
            "cpu_capacity_penalty",
            "gpu_capacity_penalty",
            "communication_penalty",
            "dependency_penalty",
            "feature_compatibility_penalty",
            "multi_node_jobs",
        ],
        "alpha_assign": alpha_assign,
        "alpha_capacity": alpha_capacity,
        "alpha_gpu_compat": alpha_gpu_compat,
        "objective_scale": objective_scale,
        "job_count": len(jobs),
        "node_count": len(nodes),
        "variable_count": q_size,
        "matrix_dimensions": [q_size, q_size],
        "objective_term_count": objective_terms,
        "assignment_term_count": assignment_terms,
        "cpu_capacity_term_count": cpu_capacity_terms,
        "gpu_capacity_term_count": gpu_capacity_terms,
        "gpu_compatibility_term_count": gpu_compatibility_terms,
    }

    return {
        "variables": variables,
        "Q": Q,
        "metadata": metadata,
    }


def debug_report(result: dict[str, Any]) -> str:
    Q = result["Q"]
    non_zero = 0
    objective = 0.0
    assignment = 0.0
    cpu_capacity = 0.0
    gpu_capacity = 0.0
    gpu_compat = 0.0
    # Debug accounting is approximate at the matrix level because the model
    # already folds terms together; we report the term counts and Q statistics.
    for row in Q:
        for value in row:
            if value != 0:
                non_zero += 1
    md = result["metadata"]
    objective = float(md["objective_term_count"])
    assignment = float(md["assignment_term_count"])
    cpu_capacity = float(md["cpu_capacity_term_count"])
    gpu_capacity = float(md["gpu_capacity_term_count"])
    gpu_compat = float(md["gpu_compatibility_term_count"])
    lines = [
        f"variable count: {md['variable_count']}",
        f"matrix dimensions: {md['matrix_dimensions'][0]} x {md['matrix_dimensions'][1]}",
        f"non-zero entries: {non_zero}",
        f"objective contribution: {objective}",
        f"assignment contribution: {assignment}",
        f"cpu capacity contribution: {cpu_capacity}",
        f"gpu capacity contribution: {gpu_capacity}",
        f"gpu compatibility contribution: {gpu_compat}",
    ]
    return "\n".join(lines)


def example_2x2() -> dict[str, Any]:
    jobs = [
        {"job_id": "j0", "optimization": {"cpu_req": 1, "gpu_req": 0, "estimated_runtime_seconds": 10}},
        {"job_id": "j1", "optimization": {"cpu_req": 2, "gpu_req": 1, "estimated_runtime_seconds": 5}},
    ]
    nodes = [
        {"node_id": "n0", "capacity": {"ncpus": 4, "ngpus": 1}, "kind": "gpu"},
        {"node_id": "n1", "capacity": {"ncpus": 2, "ngpus": 0}, "kind": "cpu"},
    ]
    return build_qubo(jobs, nodes, alpha_assign=10.0, alpha_capacity=10.0, alpha_gpu_compat=10.0, objective_scale=1.0)


def example_3x2() -> dict[str, Any]:
    jobs = [
        {"job_id": "j0", "optimization": {"cpu_req": 1, "gpu_req": 0, "estimated_runtime_seconds": 7}},
        {"job_id": "j1", "optimization": {"cpu_req": 2, "gpu_req": 1, "estimated_runtime_seconds": 3}},
        {"job_id": "j2", "optimization": {"cpu_req": 1, "gpu_req": 0, "estimated_runtime_seconds": 9}},
    ]
    nodes = [
        {"node_id": "n0", "capacity": {"ncpus": 4, "ngpus": 1}, "kind": "gpu"},
        {"node_id": "n1", "capacity": {"ncpus": 2, "ngpus": 0}, "kind": "cpu"},
    ]
    return build_qubo(jobs, nodes, alpha_assign=10.0, alpha_capacity=10.0, alpha_gpu_compat=10.0, objective_scale=1.0)


def main() -> None:
    args = parse_args()
    if args.example:
        result = example_2x2() if args.example == "2x2" else example_3x2()
    elif args.input:
        payload = load_payload(resolve_path(args.input))
        result = build_qubo(
            payload["jobs"],
            payload["nodes"],
            args.alpha_assign,
            args.alpha_capacity,
            0.0,
            args.objective_scale,
        )
    else:
        raise SystemExit("Provide either --input or --example")

    if args.debug:
        print(debug_report(result))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, indent=2 if args.pretty else None, sort_keys=True),
        encoding="utf-8",
    )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
