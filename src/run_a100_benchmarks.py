#!/usr/bin/env python3
"""Resumable A100 batch runner for the expanded benchmark suite.

Loops through small, medium, and large buckets, builds QUBO with dynamic
penalty scaling, solves with CP-SAT, SA, and QAOA, and writes results immediately.
"""

import json
import sys
import time
import traceback
from pathlib import Path

# Add src to path
sys.path.append(str(Path("src").resolve()))

from qubo_builder import build_qubo, qubo_energy, job_view, node_view
from qubo_sa_solver import run_solver as run_sa_solver
from cp_sat_mapping_baseline import solve_mapping
from assignment_validator import validate_assignment
from qaoa_cudaq_solver import run_solver as run_qaoa_solver, build_spin_operator
from schedule_decoder import decode_exclusive

def get_energy_components(assignment, jobs, nodes, variables, Q, offset, alpha_assign, alpha_gpu_compat):
    bits = [0] * len(variables)
    for name, info in variables.items():
        if assignment.get(info["job_id"]) == info["node_id"]:
            bits[info["index"]] = 1
            
    total_qubo_energy = qubo_energy(bits, Q) + offset
    
    obj_energy = 0.0
    assign_penalty = 0.0
    gpu_compat_penalty = 0.0
    
    from qubo_builder import node_cost_proxy, gpu_compatibility_penalty as gpu_compat_p
    jobs_dict = {str(j.get("job_id") or j.get("optimization", {}).get("job_id")): job_view(j) for j in jobs}
    nodes_dict = {str(n.get("node_id")): node_view(n) for n in nodes}
    
    for j_id, n_id in assignment.items():
        if j_id in jobs_dict and n_id in nodes_dict:
            obj_energy += 0.1 * node_cost_proxy(jobs_dict[j_id], nodes_dict[n_id])
            
    for j_id in jobs_dict:
        count = 1 if j_id in assignment else 0
        assign_penalty += alpha_assign * ((1 - count) ** 2)
        
    for j_id, n_id in assignment.items():
        if j_id in jobs_dict and n_id in nodes_dict:
            gpu_compat_penalty += alpha_gpu_compat * gpu_compat_p(jobs_dict[j_id], nodes_dict[n_id])
            
    return {
        "total_qubo": total_qubo_energy,
        "objective": obj_energy,
        "assignment_penalty": assign_penalty,
        "gpu_compat_penalty": gpu_compat_penalty
    }

def run_one_window_a100(window_payload, budget, optimizer_steps=100):
    label = window_payload.get("label", "unknown")
    jobs = window_payload["jobs"]
    nodes = window_payload["candidate_nodes"]
    
    # Calculate max objective cost to dynamically scale alpha_assign
    from qubo_builder import node_cost_proxy
    max_obj_cost = 0.0
    for job in jobs:
        for node in nodes:
            max_obj_cost = max(max_obj_cost, 0.1 * node_cost_proxy(job, node))
    alpha_assign = max(10.0, 1.5 * max_obj_cost)
    alpha_gpu_compat = alpha_assign

    # 1. Build QUBO
    qubo_start = time.perf_counter()
    qubo = build_qubo(
        jobs,
        nodes,
        alpha_assign=alpha_assign,
        alpha_capacity=10.0,
        alpha_gpu_compat=alpha_gpu_compat,
        objective_scale=0.1
    )
    qubo_build_time = time.perf_counter() - qubo_start
    
    Q = qubo["Q"]
    variables = qubo["variables"]
    n_qubits = len(Q)
    _, offset = build_spin_operator(Q)
    
    # 2. CP-SAT Baseline
    cpsat_start = time.perf_counter()
    cpsat_res = solve_mapping(
        {"jobs": jobs, "nodes": nodes},
        time_limit=30.0,
        workers=1,
        allow_multi_node=False
    )
    cpsat_time = time.perf_counter() - cpsat_start
    cpsat_assignment = cpsat_res.get("assignments", {})
    cpsat_valid = validate_assignment(cpsat_assignment, jobs, nodes)["valid"]
    cpsat_comp = get_energy_components(cpsat_assignment, jobs, nodes, variables, Q, offset, alpha_assign, alpha_gpu_compat)
    
    cpsat_assigned_jobs = [j for j in jobs if (j.get("job_id") or j.get("optimization", {}).get("job_id")) in cpsat_assignment]
    cpsat_schedule = decode_exclusive(cpsat_assigned_jobs, nodes, cpsat_assignment)
    cpsat_makespan = cpsat_schedule["makespan_seconds"]
    
    # 3. Simulated Annealing Baseline
    sa_start = time.perf_counter()
    sa_res = run_sa_solver(
        qubo,
        None,
        None,
        initial_temperature=100.0,
        cooling_rate=0.95,
        iterations=1000,
        trials=10,
        seed=42
    )
    sa_time = time.perf_counter() - sa_start
    best_sa = sa_res["summary"]["best_overall"]
    sa_assignment = best_sa["assignment"] if best_sa else {}
    sa_valid = validate_assignment(sa_assignment, jobs, nodes)["valid"]
    sa_comp = get_energy_components(sa_assignment, jobs, nodes, variables, Q, offset, alpha_assign, alpha_gpu_compat)
    
    sa_assigned_jobs = [j for j in jobs if (j.get("job_id") or j.get("optimization", {}).get("job_id")) in sa_assignment]
    sa_schedule = decode_exclusive(sa_assigned_jobs, nodes, sa_assignment)
    sa_makespan = sa_schedule["makespan_seconds"]
    
    # 4. QAOA Solver (No skipping on Large on A100)
    qaoa_start = time.perf_counter()
    qaoa_res = run_qaoa_solver(
        qubo,
        p=2,
        optimizer_steps=optimizer_steps,
        seed=42,
        shots=0,
        jobs=jobs,
        nodes=nodes
    )
    qaoa_time = time.perf_counter() - qaoa_start
    qaoa_assignment = qaoa_res["assignment"]
    qaoa_valid = validate_assignment(qaoa_assignment, jobs, nodes)["valid"]
    qaoa_comp = get_energy_components(qaoa_assignment, jobs, nodes, variables, Q, offset, alpha_assign, alpha_gpu_compat)
    
    qaoa_assigned_jobs = [j for j in jobs if (j.get("job_id") or j.get("optimization", {}).get("job_id")) in qaoa_assignment]
    qaoa_schedule = decode_exclusive(qaoa_assigned_jobs, nodes, qaoa_assignment)
    qaoa_makespan = qaoa_schedule["makespan_seconds"]
    
    # Overlap and approximation metrics
    total_jobs = len(jobs)
    overlap_count = sum(1 for j_id, n_id in qaoa_assignment.items() if cpsat_assignment.get(j_id) == n_id)
    overlap_pct = (overlap_count / max(1, total_jobs)) * 100.0
    
    qaoa_energy = qaoa_comp["total_qubo"]
    sa_energy = sa_comp["total_qubo"]
    cpsat_energy = cpsat_comp["total_qubo"]
    
    approx_sa = qaoa_energy / sa_energy if sa_energy != 0.0 else 1.0
    approx_cpsat = qaoa_energy / cpsat_energy if cpsat_energy != 0.0 else 1.0
    
    return {
        "label": label,
        "bucket": budget,
        "jobs": total_jobs,
        "nodes": len(nodes),
        "variables": len(variables),
        "qubits": n_qubits,
        "matrix_size": f"{n_qubits}x{n_qubits}",
        "qubo_build_time": qubo_build_time,
        "qaoa": {
            "feasible": qaoa_valid,
            "runtime": qaoa_time,
            "energy": qaoa_energy,
            "obj": qaoa_comp["objective"],
            "makespan": qaoa_makespan
        },
        "sa": {
            "feasible": sa_valid,
            "runtime": sa_time,
            "energy": sa_energy,
            "obj": sa_comp["objective"],
            "makespan": sa_makespan
        },
        "cpsat": {
            "feasible": cpsat_valid,
            "runtime": cpsat_time,
            "energy": cpsat_energy,
            "obj": cpsat_comp["objective"],
            "makespan": cpsat_makespan
        },
        "comparison": {
            "overlap_pct": overlap_pct,
            "approx_sa": approx_sa,
            "approx_cpsat": approx_cpsat,
            "energy_gap_vs_cpsat": qaoa_energy - cpsat_energy,
            "energy_gap_vs_sa": qaoa_energy - sa_energy,
            "makespan_gap_vs_cpsat": qaoa_makespan - cpsat_makespan,
            "makespan_gap_vs_sa": qaoa_makespan - sa_makespan
        }
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Master A100 batch runner")
    parser.add_argument("--bucket", choices=["small", "medium", "large", "all"], default="all", help="Target bucket to run")
    args = parser.parse_args()
    
    reduced_dir = Path("data/windows/quantum_windows_reduced")
    results_dir = Path("reports/benchmarks/qaoa")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    failures_log = results_dir / "failures.log"
    
    if args.bucket == "all":
        buckets = ["small", "medium", "large"]
    else:
        buckets = [args.bucket]
        
    print(f"Starting master A100 batch execution for bucket(s): {buckets}...")
    print(f"Skipping already completed runs in: {results_dir}")
    
    total_runs = 0
    skipped_runs = 0
    successful_runs = 0
    failed_runs = 0
    
    for bucket in buckets:
        data_path = reduced_dir / f"{bucket}.json"
        if not data_path.exists():
            print(f"[WARNING] Missing bucket file: {data_path}")
            continue
            
        data = json.loads(data_path.read_text(encoding="utf-8"))
        windows = data.get("windows", [])
        
        # Ensure subdirectory for bucket exists
        bucket_dir = results_dir / bucket
        bucket_dir.mkdir(parents=True, exist_ok=True)
        
        for w in windows:
            label = w["label"]
            output_file = bucket_dir / f"{label}_result.json"
            
            total_runs += 1
            
            # Check if already completed
            if output_file.exists():
                print(f"  [SKIP] {label} already completed.")
                skipped_runs += 1
                continue
                
            print(f"  [RUNNING] {label} ({bucket.upper()})...")
            
            try:
                # Execute full QAOA simulation with 100 optimizer steps
                res = run_one_window_a100(w, bucket, optimizer_steps=100)
                
                # Write results immediately
                output_file.write_text(json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")
                print(f"  [SUCCESS] Wrote {output_file}")
                successful_runs += 1
            except Exception as e:
                # Record failure and continue
                tb = traceback.format_exc()
                error_msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Failure in window {label} ({bucket.upper()}):\n{tb}\n"
                with open(failures_log, "a", encoding="utf-8") as fl:
                    fl.write(error_msg)
                print(f"  [FAILED] {label}. Recorded to failures.log")
                failed_runs += 1
                
    print("\nBatch Execution Summary:")
    print(f"  Total Windows in Suite: {total_runs}")
    print(f"  Skipped (Already Done): {skipped_runs}")
    print(f"  Completed Successfully: {successful_runs}")
    print(f"  Failed runs recorded:   {failed_runs}")

if __name__ == "__main__":
    main()
