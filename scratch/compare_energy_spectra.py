import json
from pathlib import Path

def main():
    reports_dir = Path("reports")
    
    cpsat_pool_file = reports_dir / "cpsat_pool_results.json"
    cpsat_pool_data = json.loads(cpsat_pool_file.read_text(encoding="utf-8")) if cpsat_pool_file.exists() else {}
    
    sa_restarts_file = reports_dir / "sa_restarts_results.json"
    sa_restarts_data = json.loads(sa_restarts_file.read_text(encoding="utf-8")) if sa_restarts_file.exists() else {}
    
    depth_file = reports_dir / "depth_results.json"
    depth_data = json.loads(depth_file.read_text(encoding="utf-8")) if depth_file.exists() else []
    qaoa_b = {r["label"]: r for r in depth_data if r.get("p") == 1}
    
    lbl = "large_3"
    print(f"=== Energy Spectrum Comparison for {lbl} ===")
    print()
    
    # 1. CP-SAT Solution Pool Objectives
    cpsat_sols = cpsat_pool_data.get(lbl, {}).get("solutions", [])
    if cpsat_sols:
        print(f"CP-SAT Solution Pool Size: {len(cpsat_sols)}")
        print(f"  Rank 1 (Ground State) Objective : {cpsat_sols[0].get('objective'):,.2f}")
        print(f"  Rank 100 Objective              : {cpsat_sols[-1].get('objective'):,.2f}")
    else:
        print("No CP-SAT solutions found.")
        
    # 2. SA restarts best feasible objective
    sa_res = sa_restarts_data.get(lbl, {})
    if sa_res:
        print(f"SA Restarts:")
        print(f"  Feasible Count                  : {sa_res.get('feasible_count')}/100")
        print(f"  Best Feasible Makespan          : {sa_res.get('best_feasible_makespan')}s")
        print(f"  Min QUBO Energy (any solution)  : {sa_res.get('energy_min'):,.2f}")
        print(f"  Best Feasible QUBO Energy       : {sa_res.get('best_feasible_energy'):,.2f}")
        
    # 3. QAOA best feasible objective
    q_res = qaoa_b.get(lbl, {})
    if q_res:
        print(f"QAOA (p=1):")
        print(f"  Feasible                        : {q_res.get('feasible')}")
        print(f"  Makespan                        : {q_res.get('makespan')}s")
        print(f"  QUBO Energy                     : {q_res.get('energy'):,.2f}")

if __name__ == "__main__":
    main()
