#!/usr/bin/env python3
"""Plot decoded makespan comparison for CP-SAT, SA, and QAOA under Option B."""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def main():
    reports_dir = Path("reports")
    plots_dir = reports_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # Load the datasets
    cpsat_pool = json.loads((reports_dir / "cpsat_pool_results.json").read_text(encoding="utf-8"))
    sa_restarts = json.loads((reports_dir / "sa_restarts_results.json").read_text(encoding="utf-8"))
    qaoa_data = json.loads((reports_dir / "depth_results.json").read_text(encoding="utf-8"))
    
    qaoa_b = {r["label"]: r for r in qaoa_data if r.get("p") == 1}
    
    # The 7 windows that are feasible under Option B (where QAOA succeeded)
    labels = ["small_1", "small_4", "small_6", "medium_3", "large_1", "large_3", "large_13"]
    
    cpsat_ms = []
    sa_ms = []
    qaoa_ms = []
    
    for lbl in labels:
        # QAOA
        q_ms = qaoa_b.get(lbl, {}).get("makespan", 0.0)
        qaoa_ms.append(q_ms)
        
        # SA
        s_ms = sa_restarts.get(lbl, {}).get("best_feasible_makespan")
        sa_ms.append(s_ms if s_ms is not None else 0.0)
        
        # CP-SAT
        c_ms = cpsat_pool.get(lbl, {}).get("best_feasible_makespan")
        cpsat_ms.append(c_ms if c_ms is not None else 0.0)
        
    print("Option B Makespans:")
    for i, lbl in enumerate(labels):
        print(f"{lbl}: CP-SAT={cpsat_ms[i]}, SA={sa_ms[i]}, QAOA={qaoa_ms[i]}")
        
    # Plotting
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'grid.alpha': 0.3,
        'grid.linestyle': '--'
    })
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(labels))
    width = 0.25
    
    colors = {
        'cpsat': '#1f77b4',  # Classic Blue
        'sa': '#ff7f0e',     # Classic Orange
        'qaoa': '#2ca02c'    # Modern Emerald Green
    }
    
    rects1 = ax.bar(x - width, cpsat_ms, width, label='CP-SAT', color=colors['cpsat'], alpha=0.85)
    rects2 = ax.bar(x, sa_ms, width, label='Simulated Annealing', color=colors['sa'], alpha=0.85)
    rects3 = ax.bar(x + width, qaoa_ms, width, label='QAOA (Option B)', color=colors['qaoa'], alpha=0.8)
    
    ax.set_ylabel('Decoded Makespan (seconds) [Log Scale]', fontweight='bold')
    ax.set_title('Decoded Schedule Makespan Comparison (Option B)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha='right', fontweight='bold')
    ax.set_yscale('log')
    ax.grid(True, which="both", axis='y')
    ax.legend(loc='lower left')
    
    # Annotate makespan gap (%) of QAOA vs SA
    for i in range(len(labels)):
        q = qaoa_ms[i]
        s = sa_ms[i]
        
        # Annotate CP-SAT N/A for large_3
        if cpsat_ms[i] == 0:
            ax.text(i - width, 1e4, "N/A\n(No Feasible\nFound)", ha='center', va='bottom', color='red', fontsize=8, fontweight='bold')
            
        if q and s:
            gap_pct = ((q - s) / s) * 100.0
            max_val = max(cpsat_ms[i], sa_ms[i], qaoa_ms[i])
            ax.text(i, max_val * 1.25, f"{gap_pct:+.2f}%", 
                    ha='center', va='bottom', fontsize=9.5, 
                    color='darkgreen' if gap_pct <= 0 else 'darkred', fontweight='bold')
                
    # Adjust y limits for log scale visibility
    ax.set_ylim(1e3, 1e8)
    
    plt.tight_layout()
    plt.savefig(plots_dir / "makespan_comparison_opt_b.png", dpi=300)
    plt.close()
    print("Generated makespan comparison plot at reports/plots/makespan_comparison_opt_b.png")

if __name__ == "__main__":
    main()
