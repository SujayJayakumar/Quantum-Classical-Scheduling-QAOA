# Raw Walltime Format Audit Report

This report documents the audit of the raw walltime field `resources_used.walltime` in the job trace log `merged_all_jobs.jsonl`, along with the specification and validation of a robust parser function.

---

## 1. Summary Metrics

*   **Total jobs inspected**: 210,287
*   **Jobs containing walltime field**: 206,401 (98.1521%)
*   **Jobs missing walltime field (null)**: 3,886 (1.8479%)

---

## 2. Detected Formats

Our audit ran over all 210,287 records and classified the walltime values into five expected format categories:

| Format Category | Regex / Match Rule | Count | Percentage | Representative Examples |
| :--- | :--- | :---: | :---: | :--- |
| **`HH:MM:SS`** | `^\d+:\d{2}:\d{2}$` | 206,401 | 98.1521% | `01:57:58`, `00:01:19`, `00:02:00`, `00:02:01`, `16:41:24` |
| **`D:HH:MM:SS`** | `^\d+:\d+:\d{2}:\d{2}$` | 0 | 0.0000% | *None detected* |
| **`integer_seconds`** | `^\d+$` | 0 | 0.0000% | *None detected* |
| **`null` / `empty`** | `None` or `""` | 3,886 | 1.8479% | *Missing/Null value* |
| **`other_malformed`** | Any other string pattern | 0 | 0.0000% | *None detected* |

---

## 3. Robust Parser Specification

To ensure robust execution across all potential environments and handle any edge cases in future logs, we implement the following robust parsing logic in Python:

```python
from typing import Any

def parse_walltime(value: Any) -> int | None:
    if value is None:
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    
    # 1. Pure integer seconds support
    if val_str.isdigit():
        return int(val_str)
        
    parts = val_str.split(":")
    
    # 2. HH:MM:SS format support
    if len(parts) == 3:
        try:
            h = int(parts[0])
            m = int(parts[1])
            s = int(parts[2])
            return h * 3600 + m * 60 + s
        except ValueError:
            print(f"[ERROR] Failed to parse HH:MM:SS components from '{val_str}'")
            return None
            
    # 3. D:HH:MM:SS format support
    if len(parts) == 4:
        try:
            d = int(parts[0])
            h = int(parts[1])
            m = int(parts[2])
            s = int(parts[3])
            return d * 86400 + h * 3600 + m * 60 + s
        except ValueError:
            print(f"[ERROR] Failed to parse D:HH:MM:SS components from '{val_str}'")
            return None
            
    print(f"[ERROR] Invalid walltime format: '{val_str}'")
    return None
```

---

## 4. Parser Validation Suite

We programmatically validate the parser logic against every format required:

| Tested Input | Expected Category | Expected Output (Seconds) | Validator Verdict |
| :--- | :--- | :---: | :---: |
| `"01:57:58"` | `HH:MM:SS` | 7,078 | **PASS** |
| `"00:02:00"` | `HH:MM:SS` | 120 | **PASS** |
| `"1:12:34:56"` | `D:HH:MM:SS` | 131,696 | **PASS** |
| `"3600"` | `integer_seconds` | 3,600 | **PASS** |
| `None` | `null` | `None` | **PASS** |
| `""` | `empty` | `None` | **PASS** |
| `"invalid"` | `malformed` | `None` | **PASS** |
| `"12:34"` | `malformed` | `None` | **PASS** |

All tests pass successfully. This parser has been integrated into `src/overlap_dataset_builder.py`.