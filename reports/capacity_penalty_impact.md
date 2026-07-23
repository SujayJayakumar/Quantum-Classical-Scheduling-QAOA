# Capacity Penalty Impact Study

This report analyzes the quantitative distribution of QUBO matrix entries contributed by different penalty terms under the current formulation for representative Small, Medium, and Large windows.

---

## Controlled Q-Entry Distribution Analysis

The following table reports the count of Q-matrix entries contributed by each term and their relative percentage of the total active terms:

| Bucket | Representative Window | Variables | Objective Terms | Assignment Terms | GPU Compat Terms | Capacity Terms | Total Terms | Capacity % |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Small** | `gpu_30` | 15 | 15 (11.11%) | 30 (22.22%) | 0 (0.00%) | 90 (66.67%) | 135 | **66.67%** |
| **Small** | `mixed_30` | 15 | 15 (11.11%) | 30 (22.22%) | 0 (0.00%) | 90 (66.67%) | 135 | **66.67%** |
| **Small** | `mixed_20` | 15 | 15 (11.11%) | 30 (22.22%) | 0 (0.00%) | 90 (66.67%) | 135 | **66.67%** |
| **Medium** | `gpu_30` | 24 | 24 (8.33%) | 48 (16.67%) | 0 (0.00%) | 216 (75.00%) | 288 | **75.00%** |
| **Medium** | `mixed_30` | 24 | 24 (8.33%) | 48 (16.67%) | 0 (0.00%) | 216 (75.00%) | 288 | **75.00%** |
| **Medium** | `mixed_20` | 24 | 24 (8.33%) | 48 (16.67%) | 0 (0.00%) | 216 (75.00%) | 288 | **75.00%** |
| **Large** | `gpu_30` | 30 | 30 (7.14%) | 60 (14.29%) | 0 (0.00%) | 330 (78.57%) | 420 | **78.57%** |
| **Large** | `mixed_30` | 30 | 30 (7.14%) | 60 (14.29%) | 0 (0.00%) | 330 (78.57%) | 420 | **78.57%** |
| **Large** | `mixed_20` | 30 | 30 (7.14%) | 60 (14.29%) | 0 (0.00%) | 330 (78.57%) | 420 | **78.57%** |

---

## Key Findings & Insights

1. **Dominance of Capacity Penalties**:
   * Capacity penalty terms dominate the QUBO structure, accounting for **66.7%** in small windows, **75.0%** in medium windows, and **78.6%** in large windows.
   * This high dominance dilutes the objective term (less than 12% in all cases) and assignment uniqueness term, leading to poor optimization landscapes for QAOA.
2. **GPU Compatibility Inactivity**:
   * The GPU compatibility penalty contributes exactly **0 terms** across all instances.
   * *Root Cause*: Candidate node pools for both GPU-only and mixed windows are currently pre-filtered to include only GPU nodes (`kind="gpu"` or `gpu_capacity > 0`). Thus, the incompatibility check (`node["gpu_capacity"] == 0`) is never triggered.
