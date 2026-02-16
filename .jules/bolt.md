## 2026-02-10 - Optimized Scan Status Polling and Re-renders

**Learning:** `JSON.stringify` is a convenient but inefficient way to perform deep equality checks in frequently executing code (like polling loops). While acceptable for tiny arrays, it's a performance anti-pattern for larger or more complex datasets because of the serialization overhead on every tick.

**Action:** Prefer manual property-based comparison or specialized deep equality libraries when checking if API response data has changed to prevent redundant React state updates.

**Learning:** `useEffect` dependency arrays containing objects/arrays that are updated *within* the effect (directly or indirectly) can cause infinite loops or redundant effect restarts.

**Action:** Always verify that state updates within an effect don't inadvertently trigger the same effect again. Use functional updates or separate effects to isolate different data-fetching concerns.

## 2026-02-12 - Parallelizing Polling and Object Reference Stability

**Learning:** Sequential `await` calls in polling loops create a cumulative network bottleneck. Parallelizing with `Promise.all` can significantly reduce the "active" time of each poll tick. Furthermore, returning a new array from a state setter (like `setResults`) triggers re-renders for all list children unless object references for individual unchanged items are preserved, even if the child components are wrapped in `React.memo`.

**Action:** Use `Promise.all` for independent API calls in effects. When updating lists in state, map over the new data and keep references to old objects if their properties haven't changed to maximize the effectiveness of `React.memo`.
## 2026-02-16 - Reference Stability in Polling
**Learning:** Returning a new object reference in a React state setter *always* triggers a re-render, even if the data is identical. In polling views, this can lead to massive CPU waste as the entire page and its children re-render every few seconds.
**Action:** Use reference-preserving diffing in state setters (`setResults(prev => ...)`). Only return a new array/object if data has actually changed, and reuse existing object references for unchanged items in a list to enable `React.memo` to skip child re-renders.

## 2026-02-16 - Parallelizing Polling Requests
**Learning:** Sequential `await` calls in a polling loop multiply network latency. If you fetch status then results, the total time is sum of both, which can delay the UI update.
**Action:** Use `Promise.all` to fire independent API requests in parallel, reducing the total latency per polling tick to the slowest single request.
