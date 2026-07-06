## 2025-06-07 - [Optimization of Project Listing and Dashboard Performance]
**Learning:** The dashboard previously suffered from N+1 query patterns on the backend (fetching scan details individually for each project) and multiple redundant API calls from the frontend to fetch report summaries. Inlining report summaries in the projects list significantly reduces network overhead and improves load times.
**Action:** Use batch fetching for related entities (Scans, Reports) and inline critical metadata in list endpoints to reduce frontend-to-backend roundtrips.
