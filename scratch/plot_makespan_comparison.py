#!/usr/bin/env python3
"""Plot decoded makespan comparison for CP-SAT, SA, and QAOA under Option B+."""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def main():
    plots_dir = Path("reports/plots")
    plots_dir.mkdir(exist_ok=True)
    
    # 7 windows that are feasible under Option B+
    labels = ["small_1", "small_4", "small_6", "medium_3", "large_1", "large_3", "large_13"]
    
    # Makespan values in seconds from reports/soft_capacity_comparison.md
    cpsat_ms = [13785820, 2180238, 8165624, 57843, 57843, 14589930, 5200917]
    sa_ms = [13785869, 2178824, 8165624, 58516, 53857, 14589930, 5193578]
    qaoa_ms = [13762114, 2222181, 8165664, 53857, 57885, 14587851, 5401772]
    
    # Set styling
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'grid.alpha': 0.3,
        'grid.linestyle': '--'
    })
    
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(labels))
    width = 0.25
    
    # Color palette matching feasible_fraction_comparison
    colors = {
        'cpsat': '#1f77b4',  # Classic Blue
        'sa': '#ff7f0e',     # Classic Orange
        'qaoa': '#2ca02c'    # Modern Emerald Green
    }
    
    rects1 = ax.bar(x - width, cpsat_ms, width, label='CP-SAT (Exact QUBO)', color=colors['cpsat'], alpha=0.85)
    rects2 = ax.bar(x, sa_ms, width, label='SA Restarts (100 runs)', color=colors['sa'], alpha=0.85)
    rects3 = ax.bar(x + width, qaoa_ms, width, label='QAOA (p=1, shots=0)', color=colors['qaoa'], alpha=0.8)
    
    ax.set_ylabel('Decoded Makespan (seconds) [Log Scale]')
    ax.set_title('Decoded Schedule Makespan Comparison under Option B+ Formulation')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha='right')
    ax.set_yscale('log')
    ax.grid(True, which="both", axis='y')
    ax.legend(loc='lower left')
    
    # Annotate relative makespan gaps between QAOA and SA / CP-SAT
    for i in range(len(labels)):
        q = qaoa_ms[i]
        s = sa_ms[i]
        gap_pct = ((q - s) / s) * 100.0
        # Print annotation above the bars
        ax.text(i, max(cpsat_ms[i], sa_ms[i], qaoa_ms[i]) * 1.2, f"{gap_pct:+.1f}%", 
                ha='center', va='bottom', fontsize=9, color='darkgreen' if gap_pct <= 0 else 'darkred', fontweight='bold')
                
    plt.tight_layout()
    plt.savefig(plots_dir / "makespan_comparison.png", dpi=300)
    plt.close()
    print("Generated makespan comparison plot at reports/plots/makespan_comparison.png")

if __name__ == "__main__":
    main()
