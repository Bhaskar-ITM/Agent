## 2026-02-10 - Optimized Scan Status Polling and Re-renders

**Learning:** `JSON.stringify` is a convenient but inefficient way to perform deep equality checks in frequently executing code (like polling loops). While acceptable for tiny arrays, it's a performance anti-pattern for larger or more complex datasets because of the serialization overhead on every tick.

**Action:** Prefer manual property-based comparison or specialized deep equality libraries when checking if API response data has changed to prevent redundant React state updates.

**Learning:** `useEffect` dependency arrays containing objects/arrays that are updated *within* the effect (directly or indirectly) can cause infinite loops or redundant effect restarts.

**Action:** Always verify that state updates within an effect don't inadvertently trigger the same effect again. Use functional updates or separate effects to isolate different data-fetching concerns.

## 2026-02-11 - Parallelization and State Alignment in Polling

**Learning:** Sequential awaits in polling loops (e.g., awaiting scan status, then awaiting scan results) multiply network latency. Mismatches between frontend terminal state checks (e.g., 'FINISHED') and backend status enums (e.g., 'COMPLETED') cause "zombie" polling intervals that never clear, wasting client and server resources.

**Action:** Use `Promise.all` to parallelize independent API calls in polling functions. Ensure terminal state checks in the frontend are inclusive of all possible backend success/failure enums to ensure polling correctly terminates.
