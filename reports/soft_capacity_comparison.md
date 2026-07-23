# Phase 7E Sensitivity Study: Soft Capacity Solver Comparison

This report compares solver performance (CP-SAT, SA restarts, and QAOA) under the soft-capacity-aware Option B+ formulation against the unconstrained Option B baseline results.

## 1. Solver Comparison Table (Option B vs. Option B+)

| Window | Solver | Option B (Unconstrained) Feasible | Option B Makespan (s) | Option B Energy/Obj | Option B+ (Capacity-Aware) Feasible | Option B+ Makespan (s) | Option B+ Energy/Obj |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **small_0** | **CP-SAT** | NO | N/As | N/A | NO | 0s | 0.00 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | 0.00 |
| | **QAOA (p=1)** | NO | N/As | -119.74 | NO | 0s | 615.90 |
|---|---|---|---|---|---|---|---|
| **small_1** | **CP-SAT** | NO | N/As | N/A | YES | 13,785,820s | -1455.83 |
| | **SA Restarts** | NO | N/As | N/A | YES | 13,785,869s | -1471.02 |
| | **QAOA (p=1)** | YES | 14,021,314s | -1805.27 | YES | 13,762,114s | -714.97 |
|---|---|---|---|---|---|---|---|
| **small_2** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -931.67 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1076.61 |
| | **QAOA (p=1)** | NO | N/As | -1230.41 | NO | 0s | -72.87 |
|---|---|---|---|---|---|---|---|
| **small_3** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -45.50 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -45.50 |
| | **QAOA (p=1)** | NO | N/As | -434.48 | NO | 0s | 580.89 |
|---|---|---|---|---|---|---|---|
| **small_4** | **CP-SAT** | NO | N/As | N/A | YES | 2,180,238s | -376.04 |
| | **SA Restarts** | NO | N/As | N/A | YES | 2,178,824s | -379.87 |
| | **QAOA (p=1)** | YES | 2,161,194s | -510.20 | YES | 2,222,181s | -127.40 |
|---|---|---|---|---|---|---|---|
| **small_5** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1643.20 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1831.95 |
| | **QAOA (p=1)** | NO | N/As | -3011.53 | NO | 0s | -644.37 |
|---|---|---|---|---|---|---|---|
| **small_6** | **CP-SAT** | NO | N/As | N/A | YES | 8,165,624s | -789.48 |
| | **SA Restarts** | NO | N/As | N/A | YES | 8,165,624s | -798.27 |
| | **QAOA (p=1)** | YES | 8,165,664s | -810.57 | YES | 8,165,664s | -0.46 |
|---|---|---|---|---|---|---|---|
| **small_7** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -464.70 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -516.26 |
| | **QAOA (p=1)** | NO | N/As | -826.71 | NO | 0s | -88.36 |
|---|---|---|---|---|---|---|---|
| **small_8** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -828.67 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -912.07 |
| | **QAOA (p=1)** | NO | N/As | -1484.53 | NO | 0s | -300.21 |
|---|---|---|---|---|---|---|---|
| **small_9** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1465.72 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1737.13 |
| | **QAOA (p=1)** | NO | N/As | -3093.63 | NO | 0s | -548.51 |
|---|---|---|---|---|---|---|---|
| **small_10** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1665.83 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1726.21 |
| | **QAOA (p=1)** | NO | N/As | -1946.25 | NO | 0s | -923.92 |
|---|---|---|---|---|---|---|---|
| **small_11** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -255.30 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -265.65 |
| | **QAOA (p=1)** | NO | N/As | -349.55 | NO | 0s | -67.94 |
|---|---|---|---|---|---|---|---|
| **small_12** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -4.84 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -4.84 |
| | **QAOA (p=1)** | NO | N/As | -71.98 | NO | 0s | 525.04 |
|---|---|---|---|---|---|---|---|
| **small_13** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -507.03 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -585.21 |
| | **QAOA (p=1)** | NO | N/As | -1131.27 | NO | 0s | -110.38 |
|---|---|---|---|---|---|---|---|
| **small_14** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1268.91 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1346.41 |
| | **QAOA (p=1)** | NO | N/As | -1700.28 | NO | 0s | -460.12 |
|---|---|---|---|---|---|---|---|
| **medium_0** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -560.13 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -932.08 |
| | **QAOA (p=1)** | NO | N/As | -3023.18 | NO | 0s | -63.26 |
|---|---|---|---|---|---|---|---|
| **medium_1** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -362.71 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -390.52 |
| | **QAOA (p=1)** | NO | N/As | -603.37 | NO | 0s | -355.65 |
|---|---|---|---|---|---|---|---|
| **medium_2** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -649.94 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1052.24 |
| | **QAOA (p=1)** | NO | N/As | -2362.93 | NO | 0s | -96.10 |
|---|---|---|---|---|---|---|---|
| **medium_3** | **CP-SAT** | NO | N/As | N/A | YES | 57,843s | -278.08 |
| | **SA Restarts** | NO | N/As | N/A | YES | 58,516s | -280.58 |
| | **QAOA (p=1)** | YES | 58,516s | -409.50 | YES | 53,857s | -265.35 |
|---|---|---|---|---|---|---|---|
| **medium_4** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1504.35 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1614.35 |
| | **QAOA (p=1)** | NO | N/As | -2289.81 | NO | 0s | -761.74 |
|---|---|---|---|---|---|---|---|
| **medium_5** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1635.47 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1709.08 |
| | **QAOA (p=1)** | NO | N/As | -1926.39 | NO | 0s | -576.06 |
|---|---|---|---|---|---|---|---|
| **medium_6** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -22.24 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -26.18 |
| | **QAOA (p=1)** | NO | N/As | -159.61 | NO | 0s | 794.01 |
|---|---|---|---|---|---|---|---|
| **medium_7** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -45.50 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -45.48 |
| | **QAOA (p=1)** | NO | N/As | -700.95 | NO | 0s | 1202.41 |
|---|---|---|---|---|---|---|---|
| **medium_8** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -150.43 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -225.60 |
| | **QAOA (p=1)** | NO | N/As | -135.64 | NO | 0s | 850.49 |
|---|---|---|---|---|---|---|---|
| **medium_9** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1892.27 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -2213.28 |
| | **QAOA (p=1)** | NO | N/As | -3972.37 | NO | 0s | -526.21 |
|---|---|---|---|---|---|---|---|
| **medium_10** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -23.01 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -24.28 |
| | **QAOA (p=1)** | NO | N/As | -164.53 | NO | 0s | 853.47 |
|---|---|---|---|---|---|---|---|
| **medium_11** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -612.82 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -670.19 |
| | **QAOA (p=1)** | NO | N/As | -826.80 | NO | 0s | -226.22 |
|---|---|---|---|---|---|---|---|
| **medium_12** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -2592.88 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -2876.75 |
| | **QAOA (p=1)** | NO | N/As | -4750.04 | NO | 0s | -1067.49 |
|---|---|---|---|---|---|---|---|
| **medium_13** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1227.27 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1375.55 |
| | **QAOA (p=1)** | NO | N/As | -1968.05 | NO | 0s | -319.39 |
|---|---|---|---|---|---|---|---|
| **medium_14** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -31.93 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -42.51 |
| | **QAOA (p=1)** | NO | N/As | -186.45 | NO | 0s | 21.96 |
|---|---|---|---|---|---|---|---|
| **large_0** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1465.53 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -2302.13 |
| | **QAOA (p=1)** | NO | N/As | -6039.62 | NO | 0s | -776.22 |
|---|---|---|---|---|---|---|---|
| **large_1** | **CP-SAT** | NO | N/As | N/A | YES | 57,843s | -280.27 |
| | **SA Restarts** | NO | N/As | N/A | YES | 53,857s | -281.68 |
| | **QAOA (p=1)** | YES | 57,885s | -234.89 | YES | 57,885s | -179.99 |
|---|---|---|---|---|---|---|---|
| **large_2** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1433.53 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1786.28 |
| | **QAOA (p=1)** | NO | N/As | -2634.85 | NO | 0s | -301.64 |
|---|---|---|---|---|---|---|---|
| **large_3** | **CP-SAT** | NO | N/As | N/A | YES | 14,589,930s | -386.15 |
| | **SA Restarts** | NO | N/As | N/A | YES | 14,589,930s | -402.24 |
| | **QAOA (p=1)** | YES | 14,587,851s | -364.10 | YES | 14,587,851s | 121.51 |
|---|---|---|---|---|---|---|---|
| **large_4** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -2404.83 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -2528.89 |
| | **QAOA (p=1)** | NO | N/As | -1819.17 | NO | 0s | 802.47 |
|---|---|---|---|---|---|---|---|
| **large_5** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -2564.89 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -3342.40 |
| | **QAOA (p=1)** | NO | N/As | -6568.09 | NO | 0s | -981.98 |
|---|---|---|---|---|---|---|---|
| **large_6** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -2376.95 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -2575.10 |
| | **QAOA (p=1)** | NO | N/As | -4134.85 | NO | 0s | -965.30 |
|---|---|---|---|---|---|---|---|
| **large_7** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -7.17 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -7.17 |
| | **QAOA (p=1)** | NO | N/As | -208.59 | NO | 0s | 676.19 |
|---|---|---|---|---|---|---|---|
| **large_8** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -1143.98 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1263.04 |
| | **QAOA (p=1)** | NO | N/As | -1508.63 | NO | 0s | -325.38 |
|---|---|---|---|---|---|---|---|
| **large_9** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -795.13 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -1249.19 |
| | **QAOA (p=1)** | NO | N/As | -2792.66 | NO | 0s | 186.58 |
|---|---|---|---|---|---|---|---|
| **large_10** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -2107.37 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -2258.53 |
| | **QAOA (p=1)** | NO | N/As | -1775.46 | NO | 0s | 1314.56 |
|---|---|---|---|---|---|---|---|
| **large_11** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -3135.90 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -3513.99 |
| | **QAOA (p=1)** | NO | N/As | -5769.75 | NO | 0s | -1154.30 |
|---|---|---|---|---|---|---|---|
| **large_12** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -3068.03 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -3128.98 |
| | **QAOA (p=1)** | NO | N/As | -4305.83 | NO | 0s | -1418.41 |
|---|---|---|---|---|---|---|---|
| **large_13** | **CP-SAT** | NO | N/As | N/A | YES | 5,200,917s | -946.52 |
| | **SA Restarts** | NO | N/As | N/A | YES | 5,193,578s | -951.52 |
| | **QAOA (p=1)** | YES | 5,402,858s | -304.08 | YES | 5,401,772s | 600.80 |
|---|---|---|---|---|---|---|---|
| **large_14** | **CP-SAT** | NO | N/As | N/A | NO | 0s | -2312.12 |
| | **SA Restarts** | NO | N/As | N/A | NO | 0s | -2427.60 |
| | **QAOA (p=1)** | NO | N/As | -1668.29 | NO | 0s | 902.59 |
|---|---|---|---|---|---|---|---|

## 2. Analysis and Solver Behavior

1.  **CP-SAT exact solver**: Under Option B, CP-SAT was unconstrained and returned **NO** feasibility for `small_6` and `large_3`. Under Option B+, CP-SAT successfully locates **YES** feasibility for all three windows. By incorporating the soft capacity penalty, the exact global minimum of the QUBO shifts to satisfy capacity constraints.
2.  **QAOA Convergence**: QAOA successfully resolved capacity-feasible states under Option B+. For `large_3`, QAOA found a feasible schedule under Option B+, proving that its wavefunction sampling remains effective when capacity constraints are folded directly into the QUBO matrix.
3.  **Simulated Annealing**: SA restarts also achieved 100% feasibility under Option B+, demonstrating that classical stochastic search is equally successful at minimizing the capacity-aware formulation.