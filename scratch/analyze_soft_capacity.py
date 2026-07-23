import json
from pathlib import Path

def main():
    reports_dir = Path("reports")
    
    # 1. Option B+ results
    results_path = reports_dir / "soft_capacity_study_results.json"
    if not results_path.exists():
        print("Error: soft_capacity_study_results.json not found.")
        return
    data_bp = json.loads(results_path.read_text(encoding="utf-8"))
    solver_bp = data_bp["solver_results"]
    
    # 2. Option B results
    depth_file = reports_dir / "depth_results.json"
    depth_data = json.loads(depth_file.read_text(encoding="utf-8")) if depth_file.exists() else []
    qaoa_b = {r["label"]: r for r in depth_data if r.get("p") == 1}
    
    cpsat_pool_file = reports_dir / "cpsat_pool_results.json"
    cpsat_pool_data = json.loads(cpsat_pool_file.read_text(encoding="utf-8")) if cpsat_pool_file.exists() else {}
    
    sa_restarts_file = reports_dir / "sa_restarts_results.json"
    sa_restarts_data = json.loads(sa_restarts_file.read_text(encoding="utf-8")) if sa_restarts_file.exists() else {}
    
    selected_labels = [f"small_{i}" for i in range(15)] + [f"medium_{i}" for i in range(15)] + [f"large_{i}" for i in range(15)]
    
    print("=== Comparison of Option B (Unconstrained) vs. Option B+ (Capacity-Aware) ===")
    print()
    
    for solver in ["cpsat", "sa", "qaoa"]:
        print(f"--- SOLVER: {solver.upper()} ---")
        
        # Option B stats
        b_feas = 0
        b_makespans = []
        for lbl in selected_labels:
            if solver == "cpsat":
                # First solution in pool is the unconstrained CP-SAT optimal
                sol = cpsat_pool_data.get(lbl, {}).get("solutions", [{}])[0]
                if sol.get("feasible"):
                    b_feas += 1
                    b_makespans.append(sol.get("makespan", 0))
            elif solver == "sa":
                res = sa_restarts_data.get(lbl, {})
                if res.get("feasible_count", 0) > 0:
                    b_feas += 1
                    if res.get("best_feasible_makespan") is not None:
                        b_makespans.append(res.get("best_feasible_makespan"))
            elif solver == "qaoa":
                res = qaoa_b.get(lbl, {})
                if res.get("feasible"):
                    b_feas += 1
                    b_makespans.append(res.get("makespan", 0))
                    
        # Option B+ stats
        bp_feas = 0
        bp_makespans = []
        for lbl in selected_labels:
            res = solver_bp.get(lbl, {}).get(solver, {})
            if res.get("feasible"):
                bp_feas += 1
                bp_makespans.append(res.get("makespan", 0))
                
        b_feas_pct = (b_feas / len(selected_labels)) * 100.0
        bp_feas_pct = (bp_feas / len(selected_labels)) * 100.0
        
        avg_b_ms = sum(b_makespans) / len(b_makespans) if b_makespans else 0.0
        avg_bp_ms = sum(bp_makespans) / len(bp_makespans) if bp_makespans else 0.0
        
        print(f"  Option B (Unconstrained + Filter) Feasibility : {b_feas}/{len(selected_labels)} ({b_feas_pct:.1f}%)")
        print(f"  Option B Avg Makespan (Feasible Only)         : {avg_b_ms:,.2f}s")
        print(f"  Option B+ (Capacity-Aware QUBO) Feasibility   : {bp_feas}/{len(selected_labels)} ({bp_feas_pct:.1f}%)")
        print(f"  Option B+ Avg Makespan (Feasible Only)        : {avg_bp_ms:,.2f}s")
        print()

if __name__ == "__main__":
    main()
