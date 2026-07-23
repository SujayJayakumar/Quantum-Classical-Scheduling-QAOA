# A100 Deployment Checklist

This document outlines the system configuration, hardware pre-requisites, software environments, and directory targets required for launching Phase 7 benchmark runs on the Nvidia A100 GPU cluster.

---

## 1. System & Software Environment

*   **[ ] CUDA-Q Version Check**:
    *   Target: **CUDA-Q Version 0.12.0**
    *   Command: `python3 -c "import cudaq; print(cudaq.__version__)"`
*   **[ ] Required Python Packages**:
    *   `cuda-quantum` == 0.12.0
    *   `ortools` (Google OR-Tools for CP-SAT baseline execution)
    *   Verify: `python3 -c "import ortools; print(ortools.__version__)"`
*   **[ ] GPU Target Backend**:
    *   Recommended default: **`nvidia`** target (single-GPU accelerated statevector simulation).
    *   Optional multi-GPU target: **`nvidia-mgpu`** (for scaling multi-GPU tensor network simulations).
    *   Set backend command: `cudaq.set_target("nvidia")`

---

## 2. Hardware Pre-requisites & Memory Auditing

*   **[ ] A100 GPU Availability**:
    *   Verify GPU detection: `nvidia-smi`
    *   Ensure at least **1x Nvidia A100 (80GB VRAM)** is active.
*   **[ ] Qubit Statevector Memory Audit**:
    *   **Small Bucket (16 qubits)**: Requires **~1.00 MB** VRAM.
    *   **Medium Bucket (20–24 qubits)**: Requires **~16.00 MB to 256.00 MB** VRAM.
    *   **Large Bucket (30–32 qubits)**: Requires **~16.00 GB to 64.00 GB** VRAM.
    *   *Constraint: 32-qubit simulations require a minimum of 64GB GPU VRAM. Ensure no other massive processes are utilizing the A100 VRAM before executing the Large bucket.*

---

## 3. Directory Layout & Expected Output Targets

*   **[ ] Workspace Directory Verification**:
    *   Ensure the repository is unpacked and working directory contains `src/` and `data/` folders.
*   **[ ] Input Benchmarks Presence**:
    *   Verify data files are present:
        *   `data/windows/quantum_windows_reduced/small.json`
        *   `data/windows/quantum_windows_reduced/medium.json`
        *   `data/windows/quantum_windows_reduced/large.json`
*   **[ ] Expected Output Locations**:
    *   Small: `reports/benchmarks/qaoa/small/small_{0..14}_result.json`
    *   Medium: `reports/benchmarks/qaoa/medium/medium_{0..14}_result.json`
    *   Large: `reports/benchmarks/qaoa/large/large_{0..14}_result.json`
    *   Failures Log: `reports/benchmarks/qaoa/failures.log`
