## 2026-02-10 - Optimized Scan Status Polling and Re-renders

**Learning:** `JSON.stringify` is a convenient but inefficient way to perform deep equality checks in frequently executing code (like polling loops). While acceptable for tiny arrays, it's a performance anti-pattern for larger or more complex datasets because of the serialization overhead on every tick.

**Action:** Prefer manual property-based comparison or specialized deep equality libraries when checking if API response data has changed to prevent redundant React state updates.

**Learning:** `useEffect` dependency arrays containing objects/arrays that are updated *within* the effect (directly or indirectly) can cause infinite loops or redundant effect restarts.

**Action:** Always verify that state updates within an effect don't inadvertently trigger the same effect again. Use functional updates or separate effects to isolate different data-fetching concerns.

## 2026-02-12 - Parallel API Polling and Terminal State Sync

**Learning:** Sequential `await` calls in a polling loop (e.g., fetching scan status THEN fetching results) create a cumulative latency bottleneck. In high-latency environments, this can significantly delay UI responsiveness. Parallelizing these calls with `Promise.all` can reduce network wait time by ~40-50% per tick.

**Action:** Always parallelize independent API calls in polling intervals. Also ensure terminal state checks cover all backend-to-frontend enum mappings (e.g., both COMPLETED and FINISHED) to prevent zombie polling intervals.
