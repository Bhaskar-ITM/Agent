## 2026-06-15 - Eliminate Dashboard N+1 bottlenecks
**Learning:** The Dashboard list was performing N+1 network requests (fetching report summaries for each project) and N+1 database queries (fetching scan details per project). Inlining these summaries into the main project list endpoint and batch-fetching metadata significantly reduces overhead.
**Action:** Always check if list views require additional data that can be efficiently aggregated and inlined in the primary list endpoint.
