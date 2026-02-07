## 2026-02-07 - [Infinite Polling Anti-pattern]
**Learning:** In polling-based applications, failing to stop the interval when a terminal state is reached causes unnecessary CPU and network usage (or localStorage access in this mock's case). Additionally, React's `useEffect` dependencies can trigger redundant fetches if they include objects that change on every render due to state updates.
**Action:** Always ensure polling intervals are cleared when data reaches a final state (COMPLETED/FAILED). Split initial data fetching from polling logic to avoid redundant calls on component mount.
