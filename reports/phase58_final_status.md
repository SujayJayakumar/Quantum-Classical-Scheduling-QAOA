# Phase 5.8 Final Dataset Freeze Status Report

This report documents the final status and statistics of the regenerated, quantum-ready benchmark window dataset.

---

## DATASET SUMMARY

Following the candidate node reduction repair and recovery, we have frozen the benchmark suite. The dataset is partitioned into three budget buckets (Small, Medium, Large) containing 3 windows each, for a total of 9 windows.

*   **Small Windows Count**: 3
*   **Medium Windows Count**: 3
*   **Large Windows Count**: 3
*   **Total Frozen Windows**: 9

---

## WINDOW DETAIL METRICS

The table below lists the job counts, node counts, variable counts (qubits), resource pressures, and job densities before and after candidate reduction for every window:

| Window Name | Budget | Jobs | Nodes (Orig $\rightarrow$ Red) | Qubits | CPU Pressure (Orig $\rightarrow$ Red) | GPU Pressure (Orig $\rightarrow$ Red) | Job Density (Orig $\rightarrow$ Red) | Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `gpu_30` | **Small** | 5 | 3 $\rightarrow$ 3 | 15 | 3.555 $\rightarrow$ 1.667 | 5.500 $\rightarrow$ 1.667 | 10.0 $\rightarrow$ 1.67 | `LAPTOP_SAFE` |
| `mixed_30` | **Small** | 5 | 3 $\rightarrow$ 3 | 15 | 2.409 $\rightarrow$ 0.740 | 1.417 $\rightarrow$ 0.417 | 10.0 $\rightarrow$ 1.67 | `LAPTOP_SAFE` |
| `mixed_20` | **Small** | 5 | 3 $\rightarrow$ 3 | 15 | 1.872 $\rightarrow$ 0.740 | 1.167 $\rightarrow$ 0.417 | 6.67 $\rightarrow$ 1.67 | `LAPTOP_SAFE` |
| `gpu_30` | **Medium** | 8 | 3 $\rightarrow$ 3 | 24 | 3.555 $\rightarrow$ 2.667 | 5.500 $\rightarrow$ 2.667 | 10.0 $\rightarrow$ 2.67 | `LAPTOP_SAFE` |
| `mixed_30` | **Medium** | 8 | 3 $\rightarrow$ 3 | 24 | 2.409 $\rightarrow$ 1.250 | 1.417 $\rightarrow$ 0.500 | 10.0 $\rightarrow$ 2.67 | `LAPTOP_SAFE` |
| `mixed_20` | **Medium** | 8 | 3 $\rightarrow$ 3 | 24 | 1.872 $\rightarrow$ 1.281 | 1.167 $\rightarrow$ 0.417 | 6.67 $\rightarrow$ 2.67 | `LAPTOP_SAFE` |
| `gpu_30` | **Large** | 10 | 3 $\rightarrow$ 3 | 30 | 3.555 $\rightarrow$ 3.010 | 5.500 $\rightarrow$ 3.083 | 10.0 $\rightarrow$ 3.33 | `A100_SAFE` |
| `mixed_30` | **Large** | 10 | 3 $\rightarrow$ 3 | 30 | 2.409 $\rightarrow$ 1.302 | 1.417 $\rightarrow$ 0.583 | 10.0 $\rightarrow$ 3.33 | `A100_SAFE` |
| `mixed_20` | **Large** | 10 | 3 $\rightarrow$ 3 | 30 | 1.872 $\rightarrow$ 1.333 | 1.167 $\rightarrow$ 0.417 | 6.67 $\rightarrow$ 3.33 | `A100_SAFE` |

---

## CLASSIFICATION CRITERIA

*   **`LAPTOP_SAFE`** (< 25 variables/qubits): Small and Medium windows require 15 and 24 qubits respectively. They can be simulated on standard commodity CPU/GPU hardware without massive memory footprints.
*   **`A100_SAFE`** (25 to 32 variables/qubits): Large windows require 30 qubits. They are suitable for simulation using statevector backends (e.g., CUDA-Q) on high-memory nodes or single NVIDIA A100 GPU nodes.
*   **`TOO_LARGE`** (> 32 variables/qubits): No generated windows exceed the 32 qubit threshold.
