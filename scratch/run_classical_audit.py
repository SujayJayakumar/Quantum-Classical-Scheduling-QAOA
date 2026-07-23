import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path("src").resolve()))

from qubo_builder import build_qubo, qubo_energy, job_view, node_view
from qubo_sa_solver import run_solver as run_sa_solver
from cp_sat_mapping_baseline import solve_mapping
from assignment_validator import validate_assignment
from qaoa_cudaq_solver import build_spin_operator

def audit_window(window_payload: dict, bucket: str):
    label = window_payload.get("label", "unknown")
    jobs = window_payload["jobs"]
    nodes = window_payload["candidate_nodes"]
    
    # 1. Build QUBO
    qubo = build_qubo(
        jobs,
        nodes,
        alpha_assign=10.0,
        alpha_capacity=10.0,
        alpha_gpu_compat=10.0,
        objective_scale=0.1
    )
    
    Q = qubo["Q"]
    variables = qubo["variables"]
    _, offset = build_spin_operator(Q)
    
    # Helper to calculate energy components
    def get_energy_components(assignment: dict):
        bits = [0] * len(variables)
        for name, info in variables.items():
            if assignment.get(info["job_id"]) == info["node_id"]:
                bits[info["index"]] = 1
                
        # Total QUBO Energy from matrix
        total_qubo_energy = qubo_energy(bits, Q) + offset
        
        # Calculate individual terms manually:
        # 1. Objective contribution
        obj_energy = 0.0
        # 2. Assignment uniqueness penalty
        assign_penalty = 0.0
        # 3. GPU compatibility penalty
        gpu_compat_penalty = 0.0
        
        # Objective term
        from qubo_builder import node_cost_proxy, gpu_compatibility_penalty as gpu_compat_p
        jobs_dict = {str(j.get("job_id") or j.get("optimization", {}).get("job_id")): job_view(j) for j in jobs}
        nodes_dict = {str(n.get("node_id")): node_view(n) for n in nodes}
        
        # Objective contribution = sum_{j_id, n_id} 0.1 * node_cost_proxy(job, node)
        for j_id, n_id in assignment.items():
            if j_id in jobs_dict and n_id in nodes_dict:
                obj_energy += 0.1 * node_cost_proxy(jobs_dict[j_id], nodes_dict[n_id])
                
        # Assignment penalty = alpha_assign * sum_{job} (1 - sum_{node} x_ij)^2
        # Let's count how many nodes each job is assigned to
        for j_id in jobs_dict:
            # count assignments
            count = 0
            if j_id in assignment:
                count = 1
            assign_penalty += 10.0 * ((1 - count) ** 2)
            
        # GPU compatibility penalty = alpha_gpu_compat * sum_{job, node} gpu_compat_penalty
        for j_id, n_id in assignment.items():
            if j_id in jobs_dict and n_id in nodes_dict:
                gpu_compat_penalty += 10.0 * gpu_compat_p(jobs_dict[j_id], nodes_dict[n_id])
                
        return {
            "total_qubo": total_qubo_energy,
            "objective": obj_energy,
            "assignment_penalty": assign_penalty,
            "gpu_compat_penalty": gpu_compat_penalty
        }
        
    # 2. CP-SAT
    cpsat_res = solve_mapping(
        {"jobs": jobs, "nodes": nodes},
        time_limit=10.0,
        workers=1,
        allow_multi_node=False
    )
    cpsat_assignment = cpsat_res.get("assignments", {})
    cpsat_valid = cpsat_res.get("feasible", False)
    
    # 3. SA
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
    best_sa = sa_res["summary"]["best_overall"]
    sa_assignment = best_sa["assignment"] if best_sa else {}
    sa_valid = validate_assignment(sa_assignment, jobs, nodes)["valid"]
    
    print(f"\n========================================")
    print(f"AUDITING WINDOW: {label} ({bucket.upper()})")
    print(f"========================================")
    print(f"CP-SAT Assignment: {cpsat_assignment} (Feasible: {cpsat_valid})")
    cpsat_comp = get_energy_components(cpsat_assignment)
    print(f"  CP-SAT Energy Components: {cpsat_comp}")
    
    print(f"SA Assignment: {sa_assignment} (Feasible: {sa_valid})")
    sa_comp = get_energy_components(sa_assignment)
    print(f"  SA Energy Components: {sa_comp}")
    
    # Compute violations for SA
    sa_violations = validate_assignment(sa_assignment, jobs, nodes)
    print(f"  SA Violations: {sa_violations}")
    
    # Compute violations for CP-SAT
    cpsat_violations = validate_assignment(cpsat_assignment, jobs, nodes)
    print(f"  CP-SAT Violations: {cpsat_violations}")

def main():
    reduced_dir = Path("data/windows/quantum_windows_reduced")
    
    # Audit Small windows
    small_data = json.loads((reduced_dir / "small.json").read_text(encoding="utf-8"))
    for w in small_data["windows"]:
        audit_window(w, "small")
        
    # Audit Medium window
    medium_data = json.loads((reduced_dir / "medium.json").read_text(encoding="utf-8"))
    audit_window(medium_data["windows"][0], "medium")
    
    # Audit Large window
    large_data = json.loads((reduced_dir / "large.json").read_text(encoding="utf-8"))
    audit_window(large_data["windows"][0], "large")

if __name__ == "__main__":
    main()
