import json
from pathlib import Path

def main():
    reports_dir = Path("reports")
    
    sa_restarts_file = reports_dir / "sa_restarts_results.json"
    sa_restarts_data = json.loads(sa_restarts_file.read_text(encoding="utf-8")) if sa_restarts_file.exists() else {}
    
    depth_file = reports_dir / "depth_results.json"
    depth_data = json.loads(depth_file.read_text(encoding="utf-8")) if depth_file.exists() else []
    qaoa_b = {r["label"]: r for r in depth_data if r.get("p") == 1}
    
    solved_labels = ["small_6", "medium_3", "large_1", "large_3"]
    
    print("=== Makespan Comparison: QAOA vs. SA (Option B) ===")
    print()
    print("| Window | QAOA Makespan (s) | SA Best Feasible Makespan (s) | Makespan Gap (QAOA - SA) | Relative Gap (%) |")
    print("| :--- | :---: | :---: | :---: | :---: |")
    
    for lbl in solved_labels:
        q_ms = qaoa_b.get(lbl, {}).get("makespan", 0.0)
        sa_res = sa_restarts_data.get(lbl, {})
        sa_ms = sa_res.get("best_feasible_makespan")
        
        if sa_ms is None:
            # check trials
            trials = sa_res.get("trials", [])
            for t in trials:
                if t.get("feasible"):
                    sa_ms = t.get("makespan")
                    break
                    
        if q_ms and sa_ms:
            gap = q_ms - sa_ms
            pct = (gap / sa_ms) * 100.0
            print(f"| **{lbl}** | {q_ms:,} | {sa_ms:,} | {gap:+,} | {pct:+.2f}% |")
        else:
            print(f"| **{lbl}** | QAOA: {q_ms} | SA: {sa_ms} | N/A | N/A |")

if __name__ == "__main__":
    main()
