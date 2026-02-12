## 2026-02-10 - Optimized Scan Status Polling and Re-renders

**Learning:** `JSON.stringify` is a convenient but inefficient way to perform deep equality checks in frequently executing code (like polling loops). While acceptable for tiny arrays, it's a performance anti-pattern for larger or more complex datasets because of the serialization overhead on every tick.

**Action:** Prefer manual property-based comparison or specialized deep equality libraries when checking if API response data has changed to prevent redundant React state updates.

**Learning:** `useEffect` dependency arrays containing objects/arrays that are updated *within* the effect (directly or indirectly) can cause infinite loops or redundant effect restarts.

**Action:** Always verify that state updates within an effect don't inadvertently trigger the same effect again. Use functional updates or separate effects to isolate different data-fetching concerns.
## 2026-02-12 - Parallelizing Polling and React Re-render Optimization
**Learning:** In a polling-based dashboard, sequential API calls multiply the latency per tick. Furthermore, React's default behavior re-renders components on every state update with a new object/array reference from an API, even if the content is identical. Parallelizing calls with `Promise.all` and implementing manual deep/property-based comparison before calling state setters significantly reduces both network bottleneck and CPU-bound UI lag.
**Action:** Always check if polling logic can be parallelized and implement manual diffing for state updates that receive repeated data from the backend.
