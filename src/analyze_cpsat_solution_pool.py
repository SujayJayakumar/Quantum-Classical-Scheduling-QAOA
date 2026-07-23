#!/usr/bin/env python3
"""CP-SAT Solution Pool Enumerator for Phase 7C.

Finds the Top-100 assignments (by objective value) using no-good cuts,
runs the deterministic decoder on each, and validates capacity constraints.
"""

import json
import sys
from pathlib import Path
from ortools.sat.python import cp_model

# Add src to python path if needed
sys.path.append(str(Path(__file__).parent.resolve()))

from cp_sat_mapping_baseline import compatible, node_view
from qubo_builder import job_view, node_cost_proxy
from schedule_decoder import decode_exclusive, job_optimization_view
from assignment_validator import validate_assignment

REPRESENTATIVE_WINDOWS = {
    "small": ["small_0", "small_3", "small_6", "small_9", "small_12"],
    "medium": ["medium_0", "medium_1", "medium_3", "medium_6", "medium_9"],
    "large": ["large_0", "large_1", "large_3", "large_6", "large_9"]
}

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

def main():
    reduced_dir = Path("data/windows/quantum_windows_reduced")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    pool_results = {}
    
    for bucket, labels in REPRESENTATIVE_WINDOWS.items():
        file_path = reduced_dir / f"{bucket}.json"
        if not file_path.exists():
            print(f"Skipping bucket {bucket} (file not found)")
            continue
            
        data = json.loads(file_path.read_text(encoding="utf-8"))
        all_w = {w["label"]: w for w in data.get("windows", [])}
        
        for label in labels:
            if label not in all_w:
                print(f"Window {label} not found in {bucket}.json")
                continue
                
            w = all_w[label]
            print(f"Enumerating CP-SAT solutions for {label}...")
            
            sols = enumerate_cpsat_solutions(w, limit=100)
            
            # Compute stats
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
            
            pool_results[label] = {
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
            
            print(f"  Total: {len(sols)}, Feasible: {feasible_count} ({feasible_fraction * 100.0:.1f}%), First Feasible Rank: {first_feasible_rank}")
            
    # Save results
    output_path = reports_dir / "cpsat_pool_results.json"
    output_path.write_text(json.dumps(pool_results, indent=2), encoding="utf-8")
    print(f"Wrote CP-SAT pool results to {output_path}")

if __name__ == "__main__":
    main()
