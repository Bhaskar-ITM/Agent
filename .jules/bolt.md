## 2026-02-09 - [Mock API Performance]
**Learning:** In applications using a mock API backed by `localStorage`, repeated `JSON.parse` calls during polling can lead to significant CPU overhead as the data size grows.
**Action:** Always implement a simple in-memory cache for the mock service to ensure O(1) read access while maintaining `localStorage` as the persistent store.

## 2026-02-09 - [Efficient Polling]
**Learning:** Polling intervals that continue after terminal states or reset due to unnecessary dependency updates in `useEffect` waste resources and can cause UI flickering.
**Action:** Ensure polling intervals are cleared immediately upon reaching terminal states and keep the `useEffect` dependency array minimal to avoid redundant resets.
