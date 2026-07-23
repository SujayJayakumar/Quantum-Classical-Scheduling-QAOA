# Runtime Propagation Audit Report

This report documents the results of the runtime propagation audit, tracing the job execution runtime field from the raw trace dataset through all stages of the benchmark generation pipeline.

> [!IMPORTANT]
> **First Point of Corruption identified**: The runtime values become zero at the very first processing stage in the pipeline: during the generation of **`overlap_jobs.jsonl`** from `merged_all_jobs.jsonl` by `src/overlap_dataset_builder.py`.

---

## 1. Stage-by-Stage Propagation Analysis

### Stage 1: `merged_all_jobs.jsonl`
- **File Path**: [merged_all_jobs.jsonl](file:///home/sim/Desktop/Quantum/data/merged_all_jobs.jsonl)
- **Field name used**: `resources_used.walltime` (Format: `hh:mm:ss`, e.g. `"01:57:58"`)
- **Number of jobs**: 210,287
- **Number of non-zero runtimes**: 204,508
- **Min / Mean / Max runtime**: 1 / 21,986.76 / 302,478 seconds

### Stage 2: `overlap_jobs.jsonl`
- **File Path**: [overlap_jobs.jsonl](file:///home/sim/Desktop/Quantum/data/overlap_jobs.jsonl)
- **Field name used**: `optimization.estimated_runtime_seconds`
- **Number of jobs**: 69,562
- **Number of non-zero runtimes**: **0** (All runtimes are now 0)
- **Min / Mean / Max runtime**: 0 / 0.00 / 0 seconds

### Stage 3: `state_aware_source.json`
- **File Path**: [state_aware_source.json](file:///home/sim/Desktop/Quantum/data/windows/state_aware_source.json)
- **Field name used**: `optimization.estimated_runtime_seconds` (under `windows[].jobs[].optimization`)
- **Number of jobs**: 180 (across all windows)
- **Number of non-zero runtimes**: 0
- **Min / Mean / Max runtime**: 0 / 0.00 / 0 seconds

### Stage 4: `state_aware_windows`
- **Directory Path**: [state_aware_windows/](file:///home/sim/Desktop/Quantum/data/windows/state_aware_windows)
- **Field name used**: `optimization.estimated_runtime_seconds` (in `jobs[].optimization` inside individual JSON window files)
- **Number of jobs**: 180 (sum of all jobs across 18 window files)
- **Number of non-zero runtimes**: 0
- **Min / Mean / Max runtime**: 0 / 0.00 / 0 seconds

### Stage 5: `quantum_windows_state_aware`
- **Directory Path**: [quantum_windows_state_aware/](file:///home/sim/Desktop/Quantum/data/windows/quantum_windows_state_aware)
- **Field name used**: `jobs` (In these files, the windows only contain high-level metadata; `jobs` is an integer count field and the individual job lists/runtimes are not present)
- **Number of windows**: 9
- **Number of non-zero runtimes**: N/A (Individual job records are omitted)
- **Min / Mean / Max runtime**: N/A

### Stage 6: `quantum_windows_reduced`
- **Directory Path**: [quantum_windows_reduced/](file:///home/sim/Desktop/Quantum/data/windows/quantum_windows_reduced)
- **Field name used**: `estimated_runtime_seconds` (under `windows[].jobs[]` in `small.json`, `medium.json`, and `large.json`)
- **Number of jobs**: 69 (total across all 9 windows)
- **Number of non-zero runtimes**: 0
- **Min / Mean / Max runtime**: 0 / 0.00 / 0 seconds

---

## 2. Root Cause Analysis

The diagnostic audit reveals a combination of **C) Runtime field parsing format mismatch** and **D) Runtime overwritten by default values**:

1. **Format Mismatch**: In the raw trace log `merged_all_jobs.jsonl`, the walltime is stored as a formatted string representing hours, minutes, and seconds (`"hh:mm:ss"`), such as `"01:57:58"`.
2. **Parsing Failure**: In [overlap_dataset_builder.py:L57](file:///home/sim/Desktop/Quantum/src/overlap_dataset_builder.py#L57), the script tries to extract the walltime using:
   ```python
   "estimated_runtime_seconds": parse_int(row.get("resources_used.walltime")) or 0,
   ```
   The helper function `parse_int` is defined in [overlap_dataset_builder.py:L37-L43](file:///home/sim/Desktop/Quantum/src/overlap_dataset_builder.py#L37-L43) as:
   ```python
   def parse_int(value: Any) -> int | None:
       if value is None:
           return None
       try:
           return int(float(str(value).strip()))
       except ValueError:
           return None
   ```
   Because the string `"01:57:58"` contains colons, `float("01:57:58")` fails with a `ValueError`. This causes `parse_int` to return `None`.
3. **Default Overwrite**: The `or 0` clause in the builder default-assigns `0` when `parse_int` returns `None`. As a result, the runtimes of **all** 69,562 overlap jobs are silently set to `0` seconds.
4. **Downstream Propagation**: Every subsequent script in the pipeline (`real_trace_window_generator.py`, `candidate_node_reducer.py`, `reduce_quantum_windows.py`) simply copied this `0` value, propagating it all the way to the final frozen benchmark files.

## 3. Conclusion
Runtimes were successfully extracted from the raw PBS logs, but were lost in the very first stage (`overlap_jobs.jsonl`) due to a string-to-int parsing format mismatch in `overlap_dataset_builder.py`. No code modifications have been made at this stage, as per audit constraints.