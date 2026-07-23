import subprocess
import cudaq

def test_n_qubits(n):
    code = f"""
import cudaq
import time
cudaq.reset_target()
kernel = cudaq.make_kernel()
qubits = kernel.qalloc({n})
for i in range({n}):
    kernel.h(qubits[i])
hamiltonian = 1.0 * cudaq.spin.z(0) + 1.0 * cudaq.spin.z({n-1})
start = time.time()
res = cudaq.observe(kernel, hamiltonian)
print(f"Success: Observe completed in {{time.time() - start:.3f}} seconds. Expectation: {{res.expectation()}}")
"""
    try:
        res = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=60)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -999, "", "Timeout"

for n in range(24, 31):
    print(f"Testing {n} qubits...")
    code, out, err = test_n_qubits(n)
    print(f"Result for {n} qubits: code={code}")
    if out:
        print(f"  Stdout: {out}")
    if err:
        print(f"  Stderr: {err}")
    if code != 0:
        print(f"Failed at {n} qubits. Stopping search.")
        break
