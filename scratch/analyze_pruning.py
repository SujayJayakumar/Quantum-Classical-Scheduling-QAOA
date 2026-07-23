import json
from pathlib import Path
import sys
sys.path.append("src")
from qubo_builder import build_variable_map

reduced_dir = Path("data/windows/quantum_windows_reduced")
buckets = ["small", "medium", "large"]

results = []

for b in buckets:
    p = reduced_dir / f"{b}.json"
    if not p.exists():
        continue
    data = json.loads(p.read_text(encoding="utf-8"))
    
    for w in data["windows"]:
        label = w.get("label")
        jobs = w.get("jobs", [])
        nodes = w.get("candidate_nodes", [])
        
        # Before pruning
        before_vars = len(jobs) * len(nodes)
        
        # After pruning
        variables, _ = build_variable_map(jobs, nodes)
        after_vars = len(variables)
        
        results.append({
            "bucket": b.upper(),
            "window": label,
            "before": before_vars,
            "after": after_vars,
            "reduction_pct": (1.0 - after_vars / before_vars) * 100.0 if before_vars > 0 else 0.0
        })

print(json.dumps(results, indent=2))
