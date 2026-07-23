# QAOA Execution Plan Report

This report classifies all expanded benchmark windows into priority tiers for progressive simulation execution on the Nvidia A100 GPU platform.

| Tier | Window ID | Qubits | Statevector Memory | Expected Sim Runtime | Priority |
| :--- | :--- | :---: | :---: | :--- | :---: |
| Tier 1 (A100/Laptop) | `small_0` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_1` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_2` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_3` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_4` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_5` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_6` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_7` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_8` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_9` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_10` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_11` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_12` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_13` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 1 (A100/Laptop) | `small_14` | 16 | 1.00 MB | < 1 second | HIGH (Must Run) |
| Tier 2 (A100 Priority) | `medium_0` | 24 | 256.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_1` | 20 | 16.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_2` | 24 | 256.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_3` | 20 | 16.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_4` | 20 | 16.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_5` | 24 | 256.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_6` | 24 | 256.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_7` | 24 | 256.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_8` | 20 | 16.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_9` | 24 | 256.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_10` | 24 | 256.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_11` | 20 | 16.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_12` | 24 | 256.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_13` | 24 | 256.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 2 (A100 Priority) | `medium_14` | 20 | 16.00 MB | ~834 seconds | MEDIUM (Pilot) |
| Tier 3 (A100 Only) | `large_0` | 32 | 64.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_1` | 30 | 16.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_2` | 32 | 64.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_3` | 30 | 16.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_4` | 30 | 16.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_5` | 32 | 64.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_6` | 32 | 64.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_7` | 32 | 64.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_8` | 32 | 64.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_9` | 32 | 64.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_10` | 30 | 16.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_11` | 32 | 64.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_12` | 32 | 64.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_13` | 30 | 16.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |
| Tier 3 (A100 Only) | `large_14` | 30 | 16.00 GB | ~5-8 hours (CPU fallback) | LOW (Stretch Goal) |