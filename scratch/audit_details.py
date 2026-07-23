import json
import sys
from pathlib import Path

sys.path.append(str(Path("src").resolve()))
from qubo_builder import build_qubo, node_cost_proxy
from cp_sat_mapping_baseline import solve_mapping
from qubo_sa_solver import run_solver as run_sa_solver
from qaoa_cudaq_solver import run_solver as run_qaoa_solver, decode_assignment, build_spin_operator
from assignment_validator import validate_assignment
from schedule_decoder import decode_exclusive

def audit_window(bucket, label):
    path = Path("data/windows/quantum_windows_reduced") / f"{bucket}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    w = [win for win in data["windows"] if win["label"] == label][0]
    jobs = w["jobs"]
    nodes = w["candidate_nodes"]
    
    # Scale parameters
    max_obj_cost = 0.0
    for job in jobs:
        for node in nodes:
            max_obj_cost = max(max_obj_cost, 0.1 * node_cost_proxy(job, node))
    alpha_assign = max(10.0, 1.5 * max_obj_cost)
    alpha_gpu_compat = alpha_assign

    qubo = build_qubo(
        jobs,
        nodes,
        alpha_assign=alpha_assign,
        alpha_capacity=10.0,
        alpha_gpu_compat=alpha_gpu_compat,
        objective_scale=0.1
    )
    Q = qubo["Q"]
    variables = qubo["variables"]
    _, offset = build_spin_operator(Q)
    
    print(f"\n================ AUDITING {label} ================")
    
    # 1. CP-SAT
    cpsat_res = solve_mapping({"jobs": jobs, "nodes": nodes}, time_limit=10.0, workers=1, allow_multi_node=False)
    cpsat_assign = cpsat_res.get("assignments", {})
    cpsat_val = validate_assignment(cpsat_assign, jobs, nodes)
    print("CP-SAT Validation:")
    print(f"  Valid: {cpsat_val['valid']}")
    print(f"  Violations count: {len(cpsat_val['details'])}")
    for d in cpsat_val['details']:
        print(f"    - {d['type']}: {d['message']}")
        
    # 2. SA
    sa_res = run_sa_solver(qubo, None, None, initial_temperature=100.0, cooling_rate=0.95, iterations=1000, trials=10, seed=42)
    sa_assign = sa_res["summary"]["best_overall"]["assignment"]
    sa_val = validate_assignment(sa_assign, jobs, nodes)
    print("SA Validation:")
    print(f"  Valid: {sa_val['valid']}")
    print(f"  Violations count: {len(sa_val['details'])}")
    for d in sa_val['details']:
        print(f"    - {d['type']}: {d['message']}")
        
    # 3. QAOA
    qaoa_res = run_qaoa_solver(qubo, p=2, optimizer_steps=100, seed=42, shots=0, jobs=jobs, nodes=nodes)
    qaoa_assign = qaoa_res["assignment"]
    qaoa_val = validate_assignment(qaoa_assign, jobs, nodes)
    print("QAOA Validation:")
    print(f"  Valid: {qaoa_val['valid']}")
    print(f"  Violations count: {len(qaoa_val['details'])}")
    for d in qaoa_val['details']:
        print(f"    - {d['type']}: {d['message']}")

if __name__ == "__main__":
    audit_window("small", "small_0")
    audit_window("small", "small_1")
    audit_window("medium", "medium_1")
    audit_window("medium", "medium_3")
