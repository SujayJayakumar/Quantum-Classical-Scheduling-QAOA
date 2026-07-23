#!/usr/bin/env python3
"""Run CP-SAT Solution Pool and Simulated Annealing restarts over all 45 windows.

Generates complete reports/cpsat_pool_results.json and reports/sa_restarts_results.json.
"""

import json
import sys
import random
import time
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model

# Add src to python path
sys.path.append(str(Path("src").resolve()))

from cp_sat_mapping_baseline import compatible, node_view
from qubo_builder import build_qubo, node_cost_proxy, job_view
from schedule_decoder import decode_exclusive, job_optimization_view
from assignment_validator import validate_assignment
from qubo_sa_solver import anneal_once

def enumerate_cpsat_solutions(payload, limit=100):
    raw_jobs = payload["jobs"]
    raw_nodes = payload["candidate_nodes"]
    
    opt_jobs = [job_optimization_view(job) for job in raw_jobs]
    nodes = [node_view(node) for node in raw_nodes]

    kept_jobs = []
    for raw_job, opt_job in zip(raw_jobs, opt_jobs):
        if opt_job["node_req"] != 1:
            continue
        kept_jobs.append((raw_job, opt_job))

    model = cp_model.CpModel()
    x = {}
    for _, job in kept_jobs:
        choices = []
        for node in nodes:
            if not compatible(job, node):
                continue
            var = model.NewBoolVar(f"x_{job['job_id']}_{node['node_id']}")
            x[(job["job_id"], node["node_id"])] = var
            choices.append(var)
        model.Add(sum(choices) == 1)

    total_cost_terms = []
    for _, job in kept_jobs:
        for node in nodes:
            var = x.get((job["job_id"], node["node_id"]))
            if var is not None:
                total_cost_terms.append(var * node_cost_proxy(job, node))
    model.Minimize(sum(total_cost_terms))

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 42

    solutions = []
    
    for step in range(limit):
        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            break
            
        assignment = {}
        for _, job in kept_jobs:
            for node in nodes:
                var = x.get((job["job_id"], node["node_id"]))
                if var is not None and solver.BooleanValue(var):
                    assignment[job["job_id"]] = node["node_id"]
                    break
                    
        obj_val = solver.ObjectiveValue()
        
        kept_raw_jobs = [raw_job for raw_job, _ in kept_jobs]
        decoded = decode_exclusive(kept_raw_jobs, raw_nodes, assignment)
        validation = validate_assignment(assignment, kept_raw_jobs, raw_nodes)
        
        solutions.append({
            "step": step,
            "objective": obj_val,
            "assignment": assignment,
            "makespan": decoded.get("makespan_seconds", 0),
            "feasible": validation["valid"],
            "capacity_violations": validation.get("capacity_violations", 0),
            "uniqueness_violations": validation.get("uniqueness_violations", 0)
        })
        
        # Add no-good cut to prevent this exact assignment
        cut_terms = []
        for j_id, n_id in assignment.items():
            var = x.get((j_id, n_id))
            if var is not None:
                cut_terms.append(var)
        model.Add(sum(cut_terms) <= len(assignment) - 1)
        
    return solutions

def analyze_sa_for_window(w, bucket):
    raw_jobs = w["jobs"]
    raw_nodes = w["candidate_nodes"]
    
    # Filter single-node jobs (matching CP-SAT and QUBO builder)
    opt_jobs = [job_optimization_view(job) for job in raw_jobs]
    kept_jobs = [j for j, oj in zip(raw_jobs, opt_jobs) if oj["node_req"] == 1]
    
    # Compute penalty weights matching production
    max_obj_cost = max(0.1 * node_cost_proxy(j, n) for j in kept_jobs for n in raw_nodes)
    alpha_assign = max(10.0, 1.5 * max_obj_cost)
    alpha_gpu_compat = alpha_assign
    
    # Build QUBO payload (passes raw nodes directly)
    qubo_payload = build_qubo(kept_jobs, raw_nodes, alpha_assign=alpha_assign, alpha_capacity=10.0, alpha_gpu_compat=alpha_gpu_compat, objective_scale=0.1)
    
    rng = random.Random(42)
    trials = []
    
    for trial_index in range(100):
        trial_rng = random.Random(rng.randint(0, 2**31 - 1))
        t = anneal_once(
            qubo_payload["Q"],
            qubo_payload["variables"],
            initial_temperature=100.0,
            cooling_rate=0.95,
            iterations=1000,
            rng=trial_rng
        )
        validation = validate_assignment(t["assignment"], kept_jobs, raw_nodes)
        t["valid"] = validation["valid"]
        t["trial_index"] = trial_index
        trials.append(t)
    
    unique_assignments = []
    feasible_trials = []
    
    for t in trials:
        assign = t["assignment"]
        if assign not in unique_assignments:
            unique_assignments.append(assign)
        if t["valid"]:
            decoded = decode_exclusive(kept_jobs, raw_nodes, assign)
            t["makespan_seconds"] = decoded.get("makespan_seconds", 0)
            feasible_trials.append(t)
            
    feasible_count = len(feasible_trials)
    feasible_fraction = feasible_count / len(trials)
    
    first_feasible_rank = -1
    sorted_trials = sorted(trials, key=lambda x: x["energy"])
    for idx, t in enumerate(sorted_trials):
        if t["valid"]:
            first_feasible_rank = idx
            break
            
    best_feasible_energy = min([t["energy"] for t in feasible_trials]) if feasible_trials else None
    best_feasible_makespan = min([t["makespan_seconds"] for t in feasible_trials]) if feasible_trials else None
    
    energies = [t["energy"] for t in trials]
    energy_mean = np.mean(energies)
    energy_std = np.std(energies)
    energy_min = np.min(energies)
    energy_max = np.max(energies)
    
    return {
        "bucket": bucket,
        "total_trials": len(trials),
        "feasible_count": feasible_count,
        "feasible_fraction": feasible_fraction,
        "first_feasible_rank": first_feasible_rank,
        "unique_solutions_found": len(unique_assignments),
        "best_feasible_energy": best_feasible_energy,
        "best_feasible_makespan": best_feasible_makespan,
        "energy_min": energy_min,
        "energy_max": energy_max,
        "energy_mean": energy_mean,
        "energy_std": energy_std,
        "trials": [
            {
                "trial_index": t["trial_index"],
                "energy": t["energy"],
                "feasible": t["valid"],
                "makespan": t.get("makespan_seconds", 0),
                "assignment": t["assignment"]
            } for t in trials
        ]
    }

def main():
    reduced_dir = Path("data/windows/quantum_windows_reduced")
    reports_dir = Path("reports")
    
    cpsat_pool_results = {}
    sa_restarts_results = {}
    
    for bucket in ["small", "medium", "large"]:
        file_path = reduced_dir / f"{bucket}.json"
        if not file_path.exists():
            print(f"Skipping bucket {bucket} (file not found)")
            continue
            
        data = json.loads(file_path.read_text(encoding="utf-8"))
        windows = data.get("windows", [])
        
        for w in windows:
            label = w["label"]
            print(f"Processing {label}...")
            
            # 1. CP-SAT Pool
            sols = enumerate_cpsat_solutions(w, limit=100)
            feasible_sols = [s for s in sols if s["feasible"]]
            feasible_count = len(feasible_sols)
            feasible_fraction = feasible_count / len(sols) if sols else 0.0
            
            first_feasible_rank = -1
            for idx, s in enumerate(sols):
                if s["feasible"]:
                    first_feasible_rank = idx
                    break
                    
            best_feasible_obj = min([s["objective"] for s in feasible_sols]) if feasible_sols else None
            best_feasible_makespan = min([s["makespan"] for s in feasible_sols]) if feasible_sols else None
            global_opt = sols[0]["objective"] if sols else None
            obj_gap = (best_feasible_obj - global_opt) if (best_feasible_obj is not None and global_opt is not None) else None
            
            cpsat_pool_results[label] = {
                "bucket": bucket,
                "total_solutions": len(sols),
                "feasible_count": feasible_count,
                "feasible_fraction": feasible_fraction,
                "first_feasible_rank": first_feasible_rank,
                "best_feasible_objective": best_feasible_obj,
                "best_feasible_makespan": best_feasible_makespan,
                "global_optimum": global_opt,
                "objective_gap_vs_optimum": obj_gap,
                "solutions": sols
            }
            
            # 2. SA Restarts
            sa_res = analyze_sa_for_window(w, bucket)
            sa_restarts_results[label] = sa_res

    # Save results
    (reports_dir / "cpsat_pool_results.json").write_text(json.dumps(cpsat_pool_results, indent=2), encoding="utf-8")
    (reports_dir / "sa_restarts_results.json").write_text(json.dumps(sa_restarts_results, indent=2), encoding="utf-8")
    print("Completed CP-SAT Pool and SA Restart runs across all 45 windows!")

if __name__ == "__main__":
    main()
