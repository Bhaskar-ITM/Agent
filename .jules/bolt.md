## 2026-02-10 - Optimized Scan Status Polling and Re-renders

**Learning:** `JSON.stringify` is a convenient but inefficient way to perform deep equality checks in frequently executing code (like polling loops). While acceptable for tiny arrays, it's a performance anti-pattern for larger or more complex datasets because of the serialization overhead on every tick.

**Action:** Prefer manual property-based comparison or specialized deep equality libraries when checking if API response data has changed to prevent redundant React state updates.

**Learning:** `useEffect` dependency arrays containing objects/arrays that are updated *within* the effect (directly or indirectly) can cause infinite loops or redundant effect restarts.

**Action:** Always verify that state updates within an effect don't inadvertently trigger the same effect again. Use functional updates or separate effects to isolate different data-fetching concerns.

## 2026-02-14 - Parallelized API Fetching and Stable Reconciliation

**Learning:** Sequential `await` calls in a polling loop (e.g., fetching Scan followed by Results) creates a network waterfall that increases the total cycle time. Parallelizing these with `Promise.all` significantly reduces latency per tick.

**Action:** Use `Promise.all` for independent API requests in polling hooks.

**Learning:** Frequent state updates with new object/array references cause full React tree re-renders even if the data is identical. Functional updates with deep property comparison are essential for stability.

**Action:** Implement reference-stable reconciliation logic (keeping old object instances for unchanged items) to maximize the effectiveness of `React.memo` in lists.
