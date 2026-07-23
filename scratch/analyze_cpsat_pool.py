import json
from pathlib import Path

def main():
    pool_path = Path("reports/cpsat_pool_results.json")
    if not pool_path.exists():
        print("Error: reports/cpsat_pool_results.json does not exist.")
        return
        
    data = json.loads(pool_path.read_text(encoding="utf-8"))
    
    print("=== CP-SAT Solution Pool Analysis (Pool Size = 100) ===")
    print()
    print("| Window | Feasible Solutions Found | First Feasible Rank (1-indexed) | Ground State Objective | First Feasible Objective | Objective Gap (%) |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: |")
    
    for lbl, w_data in data.items():
        solutions = w_data.get("solutions", [])
        feasible_indices = [i for i, sol in enumerate(solutions) if sol.get("feasible")]
        
        if feasible_indices:
            first_feas_idx = feasible_indices[0]
            first_feas_sol = solutions[first_feas_idx]
            ground_sol = solutions[0]
            
            ground_obj = ground_sol.get("objective", 0.0)
            feas_obj = first_feas_sol.get("objective", 0.0)
            
            gap_pct = ((feas_obj - ground_obj) / abs(ground_obj) * 100.0) if ground_obj else 0.0
            
            print(f"| **{lbl}** | {len(feasible_indices)}/100 | {first_feas_idx + 1} | {ground_obj:,.2f} | {feas_obj:,.2f} | {gap_pct:.2f}% |")
        else:
            ground_sol = solutions[0] if solutions else {}
            ground_obj = ground_sol.get("objective", 0.0) if ground_sol else 0.0
            print(f"| **{lbl}** | 0/100 | N/A | {ground_obj:,.2f} | N/A | N/A |")

if __name__ == "__main__":
    main()
