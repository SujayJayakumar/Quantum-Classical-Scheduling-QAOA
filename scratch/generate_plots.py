#!/usr/bin/env python3
"""Plotting script for Phase 7B campaign.

Generates high-quality sensitivity curves and bar plots from JSON outputs.
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def main():
    reports_dir = Path("reports")
    plt.rcParams.update({
        'font.weight': 'bold',
        'axes.labelweight': 'bold',
        'axes.titleweight': 'bold',
        'figure.titleweight': 'bold'
    })
    plots_dir = reports_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # 1. Depth scaling plots
    depth_file = reports_dir / "depth_results.json"
    if depth_file.exists():
        data = json.loads(depth_file.read_text(encoding="utf-8"))
        p_vals = sorted(list(set(r["p"] for r in data)))
        buckets = sorted(list(set(r["bucket"] for r in data)))
        
        # Plot Feasibility vs p per bucket
        plt.figure(figsize=(8, 5))
        offsets = {"small": -0.04, "medium": 0.0, "large": 0.04}
        markers = {"small": "o", "medium": "s", "large": "^"}
        linestyles = {"small": "-", "medium": "--", "large": "-."}
        
        for b in buckets:
            b_data = [r for r in data if r["bucket"] == b]
            feas_rates = []
            for p in p_vals:
                p_data = [r for r in b_data if r["p"] == p]
                feas_rates.append(np.mean([1 if r["feasible"] else 0 for r in p_data]) * 100.0)
            
            x_vals = [p + offsets.get(b, 0.0) for p in p_vals]
            plt.plot(x_vals, feas_rates, marker=markers.get(b, "o"), linestyle=linestyles.get(b, "-"), label=b.upper(), linewidth=2)
            
        plt.title("QAOA Feasibility vs. Ansatz Depth (p)")
        plt.xlabel("Depth (p)")
        plt.ylabel("Feasibility Rate (%)")
        plt.xticks(p_vals)
        plt.ylim(-5, 105)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_dir / "feasibility_vs_p.png", dpi=300)
        plt.close()
        
        # Plot Energy Gap vs p
        plt.figure(figsize=(8, 5))
        for b in buckets:
            b_data = [r for r in data if r["bucket"] == b]
            energy_gaps = []
            for p in p_vals:
                p_data = [r for r in b_data if r["p"] == p]
                energy_gaps.append(np.mean([r["energy_gap"] for r in p_data]))
            
            x_vals = [p + offsets.get(b, 0.0) for p in p_vals]
            plt.plot(x_vals, energy_gaps, marker=markers.get(b, "s"), linestyle=linestyles.get(b, "-"), label=b.upper(), linewidth=2)
            
        plt.title("QAOA Energy Gap vs. Ansatz Depth (p)")
        plt.xlabel("Depth (p)")
        plt.ylabel("Energy Gap vs CP-SAT")
        plt.xticks(p_vals)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_dir / "energy_gap_vs_p.png", dpi=300)
        plt.close()

    # 2. Shot sensitivity plots
    shot_file = reports_dir / "shot_results.json"
    if shot_file.exists():
        data = json.loads(shot_file.read_text(encoding="utf-8"))
        shot_vals = sorted(list(set(r["shots"] for r in data)))
        
        plt.figure(figsize=(8, 5))
        buckets = ["small", "medium", "large"]
        labels = ["Expectation" if s == 0 else f"{s} Shots" for s in shot_vals]
        x_indices = np.arange(len(shot_vals))
        
        offsets = {"small": -0.04, "medium": 0.0, "large": 0.04}
        markers = {"small": "o", "medium": "s", "large": "^"}
        linestyles = {"small": "-", "medium": "--", "large": "-."}
        
        for b in buckets:
            b_data = [r for r in data if b in r["label"].lower()]
            if not b_data:
                continue
            rates = []
            for s in shot_vals:
                s_data = [r for r in b_data if r["shots"] == s]
                if s_data:
                    rates.append(np.mean([1 if r["feasible"] else 0 for r in s_data]) * 100.0)
                else:
                    rates.append(0.0)
            
            x_vals = [x + offsets.get(b, 0.0) for x in x_indices]
            plt.plot(x_vals, rates, marker=markers.get(b, "o"), linestyle=linestyles.get(b, "-"), label=b.upper(), linewidth=2)
            
        plt.title("QAOA Feasibility vs. Shot Count per Bucket")
        plt.xlabel("Shot Configuration")
        plt.ylabel("Feasibility Rate (%)")
        plt.xticks(x_indices, labels)
        plt.ylim(-5, 105)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_dir / "feasibility_vs_shots.png", dpi=300)
        plt.close()

    # 3. Noise robustness plots
    noise_file = reports_dir / "noise_results.json"
    if noise_file.exists():
        data = json.loads(noise_file.read_text(encoding="utf-8"))
        levels = ["noise-free", "low-noise", "med-noise", "high-noise"]
        levels = [l for l in levels if any(r["noise_level"] == l for r in data)]
        x_indices = np.arange(len(levels))
        
        plt.figure(figsize=(8, 5))
        buckets = ["small", "medium"]
        
        offsets = {"small": -0.04, "medium": 0.04}
        markers = {"small": "o", "medium": "s"}
        linestyles = {"small": "-", "medium": "--"}
        
        for b in buckets:
            b_data = [r for r in data if b in r["label"].lower()]
            if not b_data:
                continue
            rates = []
            for l in levels:
                l_data = [r for r in b_data if r["noise_level"] == l]
                if l_data:
                    rates.append(np.mean([1 if r["feasible"] else 0 for r in l_data]) * 100.0)
                else:
                    rates.append(0.0)
            
            x_vals = [x + offsets.get(b, 0.0) for x in x_indices]
            plt.plot(x_vals, rates, marker=markers.get(b, "s"), linestyle=linestyles.get(b, "-"), label=b.upper(), linewidth=2)
            
        plt.title("QAOA Feasibility Robustness Under Noise")
        plt.xlabel("Noise Configuration")
        plt.ylabel("Feasibility Rate (%)")
        plt.xticks(x_indices, levels)
        plt.ylim(-5, 105)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_dir / "noise_robustness.png", dpi=300)
        plt.close()

    # 4. Runtime scaling plots
    scaling_file = reports_dir / "scaling_results.json"
    if scaling_file.exists():
        data = json.loads(scaling_file.read_text(encoding="utf-8"))
        qubits = sorted(list(set(r["qubits"] for r in data)))
        
        plt.figure(figsize=(8, 5))
        # Plot runtimes vs qubits
        qaoa_times = []
        sa_times = []
        cpsat_times = []
        for q in qubits:
            q_data = [r for r in data if r["qubits"] == q]
            qaoa_times.append(np.mean([r["qaoa_t"] for r in q_data]))
            sa_times.append(np.mean([r["sa_t"] for r in q_data]))
            cpsat_times.append(np.mean([r["cpsat_t"] for r in q_data]))
            
        plt.plot(qubits, qaoa_times, marker="o", color="blue", label="QAOA (A100)")
        plt.plot(qubits, sa_times, marker="s", color="orange", label="SA (Classical)")
        plt.plot(qubits, cpsat_times, marker="d", color="green", label="CP-SAT (Exact)")
        
        plt.yscale("log")
        plt.title("Solver Runtime Scaling Profile")
        plt.xlabel("Number of Qubits")
        plt.ylabel("Execution Time (s) [Log Scale]")
        plt.grid(True, which="both", linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_dir / "runtime_scaling.png", dpi=300)
        plt.close()

    print("Generated all validation plots in reports/plots/.")

if __name__ == "__main__":
    main()
