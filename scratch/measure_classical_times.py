#!/usr/bin/env python3
"""Measure actual CPU runtimes of CP-SAT pool and SA restarts on the 15 representative windows.
"""

import json
import time
import sys
from pathlib import Path

# Add src/ to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from analyze_cpsat_solution_pool import enumerate_cpsat_solutions, REPRESENTATIVE_WINDOWS
from analyze_sa_restarts import analyze_sa_for_window

def main():
    reduced_dir = Path("data/windows/quantum_windows_reduced")
    
    results = {}
    
    for bucket, labels in REPRESENTATIVE_WINDOWS.items():
        file_path = reduced_dir / f"{bucket}.json"
        if not file_path.exists():
            continue
            
        data = json.loads(file_path.read_text(encoding="utf-8"))
        all_w = {w["label"]: w for w in data.get("windows", [])}
        
        for label in labels:
            if label not in all_w:
                continue
                
            w = all_w[label]
            print(f"Timing {label}...")
            
            # Time CP-SAT Pool
            t0 = time.perf_counter()
            _ = enumerate_cpsat_solutions(w, limit=100)
            cpsat_time = time.perf_counter() - t0
            
            # Time SA Restarts
            t0 = time.perf_counter()
            _ = analyze_sa_for_window(w, bucket)
            sa_time = time.perf_counter() - t0
            
            results[label] = {
                "cpsat_pool_time": cpsat_time,
                "sa_restarts_time": sa_time
            }
            
            print(f"  CP-SAT Pool: {cpsat_time:.4f}s, SA Restarts: {sa_time:.4f}s")
            
    # Save measurement to reports/classical_solver_runtimes.json
    output_path = Path("reports/classical_solver_runtimes.json")
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote classical runtimes to {output_path}")

if __name__ == "__main__":
    main()
