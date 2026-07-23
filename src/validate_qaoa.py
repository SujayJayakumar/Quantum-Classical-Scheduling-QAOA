#!/usr/bin/env python3
"""Validate CUDA-Q QAOA solver against SA, CP-SAT, and Brute Force on toy problems."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import cudaq
from assignment_validator import validate_assignment
from brute_force_mapping_solver import make_example_2x2, make_example_3x2, solve_bruteforce
from path_utils import REPORTS_DIR
import qaoa_cudaq_solver
run_qaoa = qaoa_cudaq_solver.run_solver
from qubo_builder import build_qubo, qubo_energy
from qubo_sa_solver import run_solver as run_sa


def make_example_4x3() -> dict[str, Any]:
    """Generate a 4-job, 3-node toy instance."""
    return {
        "jobs": [
            {"job_id": "j0", "optimization": {"cpu_req": 1, "gpu_req": 0, "node_req": 1, "estimated_runtime_seconds": 3}},
            {"job_id": "j1", "optimization": {"cpu_req": 2, "gpu_req": 1, "node_req": 1, "estimated_runtime_seconds": 5}},
            {"job_id": "j2", "optimization": {"cpu_req": 1, "gpu_req": 0, "node_req": 1, "estimated_runtime_seconds": 2}},
            {"job_id": "j3", "optimization": {"cpu_req": 2, "gpu_req": 1, "node_req": 1, "estimated_runtime_seconds": 4}},
        ],
        "nodes": [
            {"node_id": "n0", "node_type": "gpu", "capacity": {"ncpus": 4, "ngpus": 1}},
            {"node_id": "n1", "node_type": "cpu", "capacity": {"ncpus": 2, "ngpus": 0}},
            {"node_id": "n2", "node_type": "gpu", "capacity": {"ncpus": 4, "ngpus": 1}},
        ],
    }


def validate_qubo_to_ising(qubo: dict[str, Any]) -> tuple[bool, int, int]:
    """Verify that E_QUBO(x) == E_Ising(z) + offset for all 2^n states."""
    Q = qubo["Q"]
    n_qubits = len(Q)
    from qaoa_cudaq_solver import build_spin_operator
    hamiltonian, offset = build_spin_operator(Q)
    
    import itertools
    
    passed = 0
    failed = 0
    # Enumerate all possible bitstrings
    for bits in itertools.product([0, 1], repeat=n_qubits):
        # Calculate classical QUBO energy
        E_qubo = qubo_energy(bits, Q)
        
        # Prepare state vector in CUDA-Q using a parameter-free kernel
        kernel = cudaq.make_kernel()
        q = kernel.qalloc(n_qubits)
        for idx, b in enumerate(bits):
            if b == 1:
                kernel.x(q[idx])
        
        # Measure expectation of the Hamiltonian
        res = cudaq.observe(kernel, hamiltonian)
        E_ising = res.expectation()
        
        # Check matching
        if abs(E_qubo - (E_ising + offset)) < 1e-6:
            passed += 1
        else:
            failed += 1
            
    ok = (failed == 0)
    return ok, passed, failed


def run_cpsat_mapping(jobs: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Import and run the CP-SAT scheduler/solver in mapping mode."""
    # We can import solve_mapping from cp_sat_mapping_baseline or cp_sat_scheduler
    from cp_sat_mapping_baseline import solve_mapping
    return solve_mapping(
        {"metadata": {}, "jobs": jobs, "nodes": nodes},
        time_limit=5.0,
        workers=1,
        allow_multi_node=False
    )


def evaluate_sample_feasibility(samples: Any, jobs: list[dict[str, Any]], nodes: list[dict[str, Any]], variables: dict[str, dict[str, Any]]) -> tuple[float, float]:
    """Calculate the feasible assignment rate in the sample counts."""
    if not samples:
        return 0.0, 0.0
    
    total_shots = sum(samples.values())
    feasible_shots = 0
    from qaoa_cudaq_solver import decode_assignment
    
    for bits, count in samples.items():
        assignment = decode_assignment(bits, variables)
        validation = validate_assignment(assignment, jobs, nodes)
        if validation["valid"]:
            feasible_shots += count
            
    return float(feasible_shots) / total_shots, float(total_shots)


def main() -> None:
    examples = {
        "2x2": make_example_2x2(),
        "3x2": make_example_3x2(),
        "4x3": make_example_4x3(),
    }

    report_lines = [
        "# QAOA Toy Validation Report",
        "",
        "This report documents the validation of the CUDA-Q QAOA solver on toy problems, comparing it against classical exact (Brute Force, CP-SAT) and heuristic (Simulated Annealing) baselines.",
        "",
        "---",
        "",
        "## STAGE 1: QUBO-TO-ISING VALIDATION",
        "",
        "We verify that the classical QUBO energy matches the quantum expectation value of the Ising Hamiltonian (plus the offset) for all possible computational basis states: $E_{\\text{QUBO}}(x) = \\langle z | H_{\\text{Ising}} | z \\rangle + \\text{offset}$.",
        "",
        "| Instance | Qubits | Total States | Passed Matches | Failed Matches | Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |"
    ]

    # Run QUBO -> Ising validation first
    qubo_to_ising_results = {}
    for name, payload in examples.items():
        jobs = payload["jobs"]
        nodes = payload["nodes"]
        qubo = build_qubo(
            jobs,
            nodes,
            alpha_assign=10.0,
            alpha_capacity=10.0,
            alpha_gpu_compat=10.0,
            objective_scale=0.1
        )
        ok, passed, failed = validate_qubo_to_ising(qubo)
        qubo_to_ising_results[name] = {"ok": ok, "passed": passed, "failed": failed, "qubo": qubo}
        status_str = "**PASSED**" if ok else "**FAILED**"
        report_lines.append(f"| `{name}` | {len(qubo['Q'])} | {2**len(qubo['Q'])} | {passed} | {failed} | {status_str} |")

    report_lines.extend([
        "",
        "---",
        "",
        "## STAGE 2: QAOA SOLVER TOY VALIDATION",
        "",
        "We evaluate the QAOA solver (using $p=2$ and noiseless COBYLA optimization, followed by 1000 sampling shots) against SA, CP-SAT, and exact Brute Force search.",
        ""
    ])

    for name, payload in examples.items():
        jobs = payload["jobs"]
        nodes = payload["nodes"]
        qubo = qubo_to_ising_results[name]["qubo"]
        variables = qubo["variables"]
        Q = qubo["Q"]
        
        # Retrieve build offset
        from qaoa_cudaq_solver import build_spin_operator
        _, offset = build_spin_operator(Q)

        print(f"Running validation on {name}...")

        # 1. CP-SAT Baseline
        cpsat_res = run_cpsat_mapping(jobs, nodes)
        cpsat_assignment = cpsat_res.get("assignments", {})

        # 2. Simulated Annealing (SA)
        sa_res = run_sa(
            qubo,
            jobs,
            nodes,
            initial_temperature=20.0,
            cooling_rate=0.9,
            iterations=500,
            trials=5,
            seed=42
        )
        sa_assignment = sa_res["summary"]["best_feasible"]["assignment"] if sa_res["summary"]["best_feasible"] else None

        # 3. Brute Force (find exact minimum energy feasible assignment)
        brute_res = solve_bruteforce({"jobs": jobs, "nodes": nodes})
        # Note: solve_bruteforce uses a different QUBO, so we recalculate energies using OUR qubo
        all_bf_rows = brute_res["rows"]
        feasible_bf_rows = [r for r in all_bf_rows if r["valid"]]
        
        # Recalculate energy under our validation QUBO
        def get_qubo_bits(assignment: dict[str, str]) -> list[int]:
            bits = [0] * len(variables)
            for name, info in variables.items():
                if assignment.get(info["job_id"]) == info["node_id"]:
                    bits[info["index"]] = 1
            return bits
            
        for r in feasible_bf_rows:
            bits = get_qubo_bits(r["assignment"])
            r["validation_qubo_energy"] = qubo_energy(bits, Q) + offset
            
        best_feasible_bf = min(feasible_bf_rows, key=lambda r: r["validation_qubo_energy"])
        brute_assignment = best_feasible_bf["assignment"]
        brute_opt_energy = best_feasible_bf["validation_qubo_energy"]

        # 4. QAOA Solver Execution
        # We run the solver with shots=0 for noiseless optimization
        started = time.perf_counter()
        qaoa_res = run_qaoa(qubo, p=2, optimizer_steps=100, seed=42, shots=0, jobs=jobs, nodes=nodes)
        elapsed = time.perf_counter() - started
        
        # Get sample result for feasibility rate
        from qaoa_cudaq_solver import build_qaoa_kernel
        linear, quadratic, _ = qaoa_cudaq_solver.upper_triangle_terms(Q)
        kernel, _ = build_qaoa_kernel(len(Q), 2, linear, quadratic)
        samples = cudaq.sample(kernel, qaoa_res["optimal_parameters"], shots_count=1000)
        
        feasible_rate, total_shots = evaluate_sample_feasibility(samples, jobs, nodes, variables)
        
        qaoa_assignment = qaoa_res["assignment"]
        qaoa_best_bits = get_qubo_bits(qaoa_assignment)
        qaoa_energy = qubo_energy(qaoa_best_bits, Q) + offset
        
        qaoa_valid = validate_assignment(qaoa_assignment, jobs, nodes)["valid"]
        energy_gap = qaoa_energy - brute_opt_energy
        energy_gap_percent = (energy_gap / abs(brute_opt_energy)) * 100.0 if brute_opt_energy != 0 else 0.0

        match_cpsat = (qaoa_assignment == cpsat_assignment)
        match_brute = (qaoa_assignment == brute_assignment)

        report_lines.extend([
            f"### Toy Instance: `{name}`",
            f"- **Qubits**: {len(Q)} qubits",
            f"- **Runtime**: {elapsed:.3f} seconds",
            f"- **Feasible Assignment Rate (Sampled)**: {feasible_rate * 100.0:.2f}%",
            f"- **Energy Gap**: {energy_gap:.4f} (QAOA: {qaoa_energy:.4f} vs Brute Force: {brute_opt_energy:.4f}, Gap %: {energy_gap_percent:.2f}%)",
            f"- **Optimal Assignment Match**: CP-SAT: `{match_cpsat}`, Brute Force: `{match_brute}`",
            "",
            "| Solver | Feasible | Assignment | Energy / Cost |",
            "| :--- | :---: | :--- | :---: |",
            f"| **QAOA** (p=2) | {qaoa_valid} | `{qaoa_assignment}` | {qaoa_energy:.4f} |",
            f"| **SA** | {sa_assignment is not None} | `{sa_assignment}` | - |",
            f"| **CP-SAT** | True | `{cpsat_assignment}` | - |",
            f"| **Brute Force** | True | `{brute_assignment}` | {brute_opt_energy:.4f} |",
            ""
        ])

    out_path = REPORTS_DIR / "qaoa_toy_validation.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Validation finished. Report written to {out_path}")


if __name__ == "__main__":
    main()