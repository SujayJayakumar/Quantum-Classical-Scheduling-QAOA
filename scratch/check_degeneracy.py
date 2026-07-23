import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from qubo_builder import node_cost_proxy, node_view
from schedule_decoder import job_optimization_view

def calculate_scheduling_cost(assignment, jobs, nodes):
    cost = 0.0
    opt_jobs = [job_optimization_view(j) for j in jobs]
    opt_nodes = [node_view(n) for n in nodes]
    
    jobs_dict = {j["job_id"]: j for j in jobs}
    nodes_dict = {n["node_id"]: n for n in nodes}
    
    for j_id, n_id in assignment.items():
        job = jobs_dict[j_id]
        node = nodes_dict[n_id]
        cost += node_cost_proxy(job, node)
    return cost

def main():
    reports_dir = Path("reports")
    reduced_dir = Path("data/windows/quantum_windows_reduced")
    
    # Load large_3 window data
    large_file = reduced_dir / "large.json"
    large_data = json.loads(large_file.read_text(encoding="utf-8"))
    large_3_window = None
    for w in large_data.get("windows", []):
        if w["label"] == "large_3":
            large_3_window = w
            break
            
    if not large_3_window:
        print("large_3 window not found.")
        return
        
    jobs = large_3_window["jobs"]
    nodes = large_3_window["candidate_nodes"]
    
    # Filter single-node jobs
    opt_jobs = [job_optimization_view(j) for j in jobs]
    kept_jobs = [j for j, oj in zip(jobs, opt_jobs) if oj["node_req"] == 1]
    
    # 1. CP-SAT Pool Objectives
    cpsat_pool_file = reports_dir / "cpsat_pool_results.json"
    cpsat_pool_data = json.loads(cpsat_pool_file.read_text(encoding="utf-8")) if cpsat_pool_file.exists() else {}
    cpsat_sols = cpsat_pool_data.get("large_3", {}).get("solutions", [])
    
    # 2. SA restarts best feasible
    sa_restarts_file = reports_dir / "sa_restarts_results.json"
    sa_restarts_data = json.loads(sa_restarts_file.read_text(encoding="utf-8")) if sa_restarts_file.exists() else {}
    sa_res = sa_restarts_data.get("large_3", {})
    trials = sa_res.get("trials", [])
    print(f"Number of SA trials: {len(trials)}")
    if trials:
        print(f"First SA trial keys: {list(trials[0].keys())}")
        print(f"First SA trial: {trials[0]}")
    sa_assign = {}
    for i, t in enumerate(trials):
        # Let's check which field indicates feasibility
        if t.get("feasible") or t.get("valid"):
            sa_assign = t.get("assignment", {})
            break
        
    # 3. QAOA best feasible
    # Load from sensitivity_cache since the depth_results list doesn't include the full mapping
    q_cache_file = reports_dir / "sensitivity_cache" / "depth_large_3_p1.json"
    print(f"QAOA cache file exists: {q_cache_file.exists()}")
    if q_cache_file.exists():
        q_cache_data = json.loads(q_cache_file.read_text(encoding="utf-8"))
        print(f"QAOA cache keys: {list(q_cache_data.keys())}")
        q_assign = q_cache_data.get("assignment", {})
    else:
        q_assign = {}
    
    print("=== Scheduling Cost Comparison for large_3 ===")
    print(f"CP-SAT Pool Solutions: {len(cpsat_sols)}")
    if cpsat_sols:
        # Let's count unique objectives in CP-SAT pool
        objs = [s["objective"] for s in cpsat_sols]
        unique_objs = sorted(list(set(objs)))
        print(f"  Unique Objectives in Pool: {unique_objs}")
        print(f"  First 5 CP-SAT Objectives : {objs[:5]}")
        print(f"  Last 5 CP-SAT Objectives  : {objs[-5:]}")
        
    if sa_assign:
        sa_cost = calculate_scheduling_cost(sa_assign, kept_jobs, nodes)
        print(f"SA Best Feasible Scheduling Cost: {sa_cost:,.2f}")
        
    if q_assign:
        q_cost = calculate_scheduling_cost(q_assign, kept_jobs, nodes)
        print(f"QAOA Best Feasible Scheduling Cost: {q_cost:,.2f}")

if __name__ == "__main__":
    main()
