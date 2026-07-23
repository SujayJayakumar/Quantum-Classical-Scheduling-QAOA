import json
from pathlib import Path
import numpy as np

def main():
    reports_dir = Path("reports")
    sa_restarts_file = reports_dir / "sa_restarts_results.json"
    if not sa_restarts_file.exists():
        print("Error: reports/sa_restarts_results.json not found.")
        return
        
    data = json.loads(sa_restarts_file.read_text(encoding="utf-8"))
    
    print("=== Simulated Annealing Restart-Level Statistics ===")
    print()
    print("| Window | Feasible Restarts (out of 100) | Single-Trial Feasibility Prob (p) | Std Dev (Bernoulli) | R=5 Success Prob | R=10 Success Prob |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: |")
    
    for lbl, w_res in data.items():
        feasible_count = w_res.get("feasible_count", 0)
        p = feasible_count / 100.0
        
        # Standard deviation of a single Bernoulli trial: sqrt(p * (1-p))
        std_dev = np.sqrt(p * (1.0 - p))
        
        # Probability of success in R trials: 1 - (1-p)^R
        p_success_5 = (1.0 - (1.0 - p)**5) * 100.0
        p_success_10 = (1.0 - (1.0 - p)**10) * 100.0
        
        # Only print windows where SA found at least one feasible solution
        if feasible_count > 0:
            print(f"| **{lbl}** | {feasible_count}/100 | {p:.2f} | {std_dev:.3f} | {p_success_5:.1f}% | {p_success_10:.1f}% |")

if __name__ == "__main__":
    main()
