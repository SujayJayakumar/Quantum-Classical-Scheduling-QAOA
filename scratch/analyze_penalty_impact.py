import json
from pathlib import Path
import sys
sys.path.append("src")
from qubo_builder import build_qubo

reduced_dir = Path("data/windows/quantum_windows_reduced")
buckets = ["small", "medium", "large"]

results = []

for b in buckets:
    p = reduced_dir / f"{b}.json"
    if not p.exists():
        continue
    data = json.loads(p.read_text(encoding="utf-8"))
    
    # Run on all windows in the bucket
    for w in data["windows"]:
        label = w.get("label")
        jobs = w.get("jobs", [])
        nodes = w.get("candidate_nodes", [])
        
        # Generate QUBO with active capacity and gpu_compat penalties
        qubo = build_qubo(
            jobs,
            nodes,
            alpha_assign=10.0,
            alpha_capacity=10.0,
            alpha_gpu_compat=10.0,
            objective_scale=0.1
        )
        
        meta = qubo["metadata"]
        var_count = meta["variable_count"]
        
        obj = meta["objective_term_count"]
        assign = meta["assignment_term_count"]
        gpu_compat = meta["gpu_compatibility_term_count"]
        capacity = meta["cpu_capacity_term_count"] + meta["gpu_capacity_term_count"]
        
        total = obj + assign + gpu_compat + capacity
        
        results.append({
            "bucket": b.upper(),
            "window": label,
            "variables": var_count,
            "obj": obj,
            "assign": assign,
            "gpu_compat": gpu_compat,
            "capacity": capacity,
            "total": total
        })

print(json.dumps(results, indent=2))
