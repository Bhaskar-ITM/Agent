## 2026-02-10 - Optimized Scan Status Polling and Re-renders

**Learning:** `JSON.stringify` is a convenient but inefficient way to perform deep equality checks in frequently executing code (like polling loops). While acceptable for tiny arrays, it's a performance anti-pattern for larger or more complex datasets because of the serialization overhead on every tick.

**Action:** Prefer manual property-based comparison or specialized deep equality libraries when checking if API response data has changed to prevent redundant React state updates.

**Learning:** `useEffect` dependency arrays containing objects/arrays that are updated *within* the effect (directly or indirectly) can cause infinite loops or redundant effect restarts.

**Action:** Always verify that state updates within an effect don't inadvertently trigger the same effect again. Use functional updates or separate effects to isolate different data-fetching concerns.

## 2026-02-12 - Parallelizing Polling and Object Reference Stability

**Learning:** Sequential `await` calls in polling loops create a cumulative network bottleneck. Parallelizing with `Promise.all` can significantly reduce the "active" time of each poll tick. Furthermore, returning a new array from a state setter (like `setResults`) triggers re-renders for all list children unless object references for individual unchanged items are preserved, even if the child components are wrapped in `React.memo`.

**Action:** Use `Promise.all` for independent API calls in effects. When updating lists in state, map over the new data and keep references to old objects if their properties haven't changed to maximize the effectiveness of `React.memo`.
