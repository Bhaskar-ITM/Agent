## 2025-05-18 - Optimized `list_projects` N+1 bottleneck
**Learning:** The `list_projects` endpoint was performing O(N) queries by fetching the latest scan for each project individually inside a loop. By refactoring the `_get_last_scan_map` helper to fetch both the `scan_id` and `created_at` in a single batch query using a subquery for the maximum date per project, the endpoint's execution time was reduced from ~590ms to ~44ms for 1000 projects.
**Action:** Always batch fetch related model data using subqueries or joins when listing collections to avoid N+1 query bottlenecks.
