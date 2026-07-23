#!/usr/bin/env python3
"""Simulated Annealing Multi-Restart Audit for Phase 7C.

Runs 100 independent Simulated Annealing restarts per benchmark window,
evaluates the final state of each trial, and records feasibility metrics.
"""

import json
import sys
import random
from pathlib import Path

# Add src to python path if needed
sys.path.append(str(Path(__file__).parent.resolve()))

from qubo_sa_solver import anneal_once
from qubo_builder import build_qubo, node_cost_proxy
from schedule_decoder import job_optimization_view, decode_exclusive
from assignment_validator import validate_assignment

REPRESENTATIVE_WINDOWS = {
    "small": ["small_0", "small_3", "small_6", "small_9", "small_12"],
    "medium": ["medium_0", "medium_1", "medium_3", "medium_6", "medium_9"],
    "large": ["large_0", "large_1", "large_3", "large_6", "large_9"]
}

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
    
    # Run solver with 100 trials using custom loop to bypass brute force checks
    print(f"  Running 100 SA trials for {w['label']}...")
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
    
    # Compute unique solutions and makespans
    unique_assignments = []
    feasible_trials = []
    
    for t in trials:
        assign = t["assignment"]
        if assign not in unique_assignments:
            unique_assignments.append(assign)
        if t["valid"]:
            # Decode makespan
            decoded = decode_exclusive(kept_jobs, raw_nodes, assign)
            t["makespan_seconds"] = decoded.get("makespan_seconds", 0)
            feasible_trials.append(t)
            
    feasible_count = len(feasible_trials)
    feasible_fraction = feasible_count / len(trials)
    
    first_feasible_rank = -1
    # Sort trials by energy to rank them
    sorted_trials = sorted(trials, key=lambda x: x["energy"])
    for idx, t in enumerate(sorted_trials):
        if t["valid"]:
            first_feasible_rank = idx
            break
            
    best_feasible_energy = min([t["energy"] for t in feasible_trials]) if feasible_trials else None
    best_feasible_makespan = min([t["makespan_seconds"] for t in feasible_trials]) if feasible_trials else None
    
    # Extract energy distribution stats
    energies = [t["energy"] for t in trials]
    import numpy as np
    energy_mean = np.mean(energies)
    energy_std = np.std(energies)
    energy_min = np.min(energies)
    energy_max = np.max(energies)
    
    print(f"    Feasible: {feasible_count} ({feasible_fraction * 100.0:.1f}%), Unique: {len(unique_assignments)}, First Feasible Rank: {first_feasible_rank}")
    
    return {
        "bucket": bucket,
        "total_trials": len(trials),
        "feasible_count": feasible_count,
        "feasible_fraction": feasible_fraction,
        "first_feasible_rank": first_feasible_rank,
        "unique_solutions_found": len(unique_assignments),
        "best_feasible_energy": best_feasible_energy,
        "best_feasible_makespan": best_feasible_makespan,
        "energy_min": float(energy_min),
        "energy_max": float(energy_max),
        "energy_mean": float(energy_mean),
        "energy_std": float(energy_std),
        "trials": [
            {
                "trial_index": t["trial_index"],
                "energy": t["energy"],
                "feasible": t["valid"],
                "makespan": t.get("makespan_seconds", 0),
                "assignment": t["assignment"]
            }
            for t in trials
        ]
    }

def main():
    reduced_dir = Path("data/windows/quantum_windows_reduced")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    sa_results = {}
    
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
            print(f"Auditing SA restarts for {label}...")
            
            res = analyze_sa_for_window(w, bucket)
            sa_results[label] = res
            
    # Save results
    output_path = reports_dir / "sa_restarts_results.json"
    output_path.write_text(json.dumps(sa_results, indent=2), encoding="utf-8")
    print(f"Wrote SA restarts results to {output_path}")

if __name__ == "__main__":
    main()
