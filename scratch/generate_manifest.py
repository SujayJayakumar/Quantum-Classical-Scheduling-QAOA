import re
from pathlib import Path

def main():
    suite_path = Path("reports/expanded_benchmark_suite.md")
    baseline_path = Path("reports/expanded_baseline_summary.md")
    
    if not suite_path.exists() or not baseline_path.exists():
        print("Missing reports.")
        return
        
    suite_content = suite_path.read_text(encoding="utf-8")
    baseline_content = baseline_path.read_text(encoding="utf-8")
    
    # Parse suite_content
    # Line format: | `SMALL` | `small_0` | 2025-08-15 00:35:10+05:30 | 8 | 3 | 2 | 16 | 4.000 | 4.000 | 12.000 | VALID |
    suite_data = {}
    for line in suite_content.split("\n"):
        if line.strip().startswith("|") and "`" in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 11:
                bucket = parts[0].replace("`", "")
                window_id = parts[1].replace("`", "")
                jobs = int(parts[3])
                nodes = int(parts[5])
                qubits = int(parts[6])
                suite_data[window_id] = {
                    "bucket": bucket,
                    "jobs": jobs,
                    "nodes": nodes,
                    "qubits": qubits
                }
                
    # Parse baseline_content
    # Line format: | `small_0` | 63,322 | 0.1280 | False | 0.021 | 63,322 | 0.1280 | False | 0.054 |
    baseline_data = {}
    for line in baseline_content.split("\n"):
        if line.strip().startswith("|") and "`" in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 9:
                window_id = parts[0].replace("`", "")
                cpsat_obj = float(parts[2])
                sa_obj = float(parts[6])
                baseline_data[window_id] = {
                    "cpsat_obj": cpsat_obj,
                    "sa_obj": sa_obj
                }
                
    # Generate reports/a100_execution_manifest.md
    manifest_lines = [
        "# A100 Master Execution Manifest",
        "",
        "This manifest lists all 45 frozen benchmark windows, their structural parameters, classical baseline objective costs, and the expected output result files on the A100 platform.",
        "",
        "| Window ID | Bucket | Jobs | Nodes | Qubits | CP-SAT Obj | SA Obj | Expected Output Filename |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |"
    ]
    
    # Sort windows small_0..14, medium_0..14, large_0..14
    sorted_windows = []
    for b in ["small", "medium", "large"]:
        for idx in range(15):
            sorted_windows.append(f"{b}_{idx}")
            
    for w_id in sorted_windows:
        s_info = suite_data.get(w_id, {"bucket": "UNKNOWN", "jobs": 0, "nodes": 0, "qubits": 0})
        b_info = baseline_data.get(w_id, {"cpsat_obj": 0.0, "sa_obj": 0.0})
        expected_fn = f"reports/benchmarks/qaoa/{s_info['bucket'].lower()}/{w_id}_result.json"
        
        manifest_lines.append(
            "| `{window_id}` | {bucket} | {jobs} | {nodes} | {qubits} | {cpsat_obj:.4f} | {sa_obj:.4f} | `{expected_fn}` |".format(
                window_id=w_id,
                bucket=s_info["bucket"],
                jobs=s_info["jobs"],
                nodes=s_info["nodes"],
                qubits=s_info["qubits"],
                cpsat_obj=b_info["cpsat_obj"],
                sa_obj=b_info["sa_obj"],
                expected_fn=expected_fn
            )
        )
        
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "a100_execution_manifest.md").write_text("\n".join(manifest_lines), encoding="utf-8")
    print("Wrote reports/a100_execution_manifest.md")

if __name__ == "__main__":
    main()
