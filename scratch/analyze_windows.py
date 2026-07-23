import json
from pathlib import Path

def estimate_memory(qubits):
    # 2^N amplitudes * 16 bytes (double precision complex)
    bytes_needed = (2**qubits) * 16
    gb = bytes_needed / (1024**3)
    if gb >= 1.0:
        return f"{gb:.2f} GB"
    mb = bytes_needed / (1024**2)
    return f"{mb:.2f} MB"

def classify_safety(qubits):
    if qubits <= 25:
        return "LAPTOP_SAFE"
    elif qubits <= 32:
        return "A100_SAFE"
    else:
        return "TOO_LARGE"

reduced_dir = Path("data/windows/quantum_windows_reduced")
buckets = ["small", "medium", "large"]

for b in buckets:
    p = reduced_dir / f"{b}.json"
    if not p.exists():
        print(f"File {p} not found")
        continue
    data = json.loads(p.read_text(encoding="utf-8"))
    print(f"\nBucket: {b.upper()}")
    for w in data["windows"]:
        label = w.get("label")
        jobs = len(w.get("jobs", []))
        nodes = len(w.get("candidate_nodes", []))
        qubits = w.get("estimated_qubits")
        # variables is jobs * nodes in mapping-only QUBO
        variables = jobs * nodes
        print(f"Window: {label} | Jobs: {jobs} | Nodes: {nodes} | Variables/Qubits: {variables} ({qubits}) | Mem: {estimate_memory(variables)} | Class: {classify_safety(variables)}")
