# Monitoring Dataset Audit

| Table | MIN(timestamp) | MAX(timestamp) | COUNT(*) | Distinct nodes |
|---|---|---|---:|---:|
| nodes.csv | n/a | n/a | 422 | 422 |
| node_status.csv | 2025-06-03 13:00:01+05:30 | 2026-01-31 23:00:01.973237+05:30 | 2450554 | 422 |
| node_metrics.csv | 2025-06-05 14:05:01+05:30 | 2026-01-31 23:55:02+05:30 | 29010295 | n/a |
| cpu_metrics.csv | 2025-06-06 12:02:54+05:30 | 2026-01-31 23:55:02+05:30 | 28900399 | n/a |

## Notes
- node_status distinct node count: 422
- Coverage period should be chosen from the overlap of these timestamp ranges and the job windows used for benchmark extraction.