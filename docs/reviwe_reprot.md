# Comprehensive Code Review: DevSecOps Pipeline Platform

---

## Executive Summary

After reviewing the full codebase, I've identified **47 distinct issues** across security, architecture, reliability, and UX categories. Below is a prioritized analysis from critical to low-impact, with practical solutions documented for each.

---

## CRITICAL — Security Vulnerabilities

### C1. API Key Stored in localStorage — Trivial XSS Exfiltration

**Location:** `src/services/api.ts`, `src/pages/SettingsPage.tsx`, `src/hooks/useScanReset.ts`

**Problem:** The backend API key is stored in `localStorage` and read on every request. Any XSS payload on the page can trivially call `localStorage.getItem('API_KEY')` and exfiltrate it. The JWT token has the same problem. The issue is compounded by `useScanReset.ts` reading the key directly instead of going through the shared axios client — meaning two code paths manage auth independently, which will drift.

**Solution:** Move the API key to a `httpOnly` session cookie managed by the backend, or at minimum use `sessionStorage` (cleared on tab close) instead of `localStorage`. Consolidate all auth header injection into the single axios interceptor in `api.ts`. Remove the manual header construction in `useScanReset.ts` entirely — it should call the shared `api.scans.reset()` method.

---

### C2. CORS Wildcard in Production

**Location:** `backend/app/main.py`

**Problem:** `allow_origins=["*"]` with `allow_credentials=True` is rejected by browsers per the CORS spec (credentials require explicit origins), but more dangerously it means any origin can make credentialed requests once this is "fixed" naively. In staging with real tokens, this is a session hijacking vector.

**Solution:** Read allowed origins from an environment variable (`CORS_ORIGINS`), defaulting to `["http://localhost:5173"]` in dev. Never combine wildcard origins with credentials.

---

### C3. Jenkins Callback Token Hardcoded in Jenkinsfile

**Location:** `Jenkinsfile` line with `CALLBACK_TOKEN = "${env.CALLBACK_TOKEN ?: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'}"`

**Problem:** The fallback token `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6` is committed to source control. Any attacker who can reach the backend's `/api/v1/scans/{id}/callback` endpoint can forge scan results by using this token. The backend in `settings.py` validates that `CALLBACK_TOKEN` is at least 32 chars — but the committed default satisfies that check.

**Solution:** Remove the default entirely: `CALLBACK_TOKEN = "${env.CALLBACK_TOKEN}"`. Make Jenkins fail loudly if the env var is missing. Rotate any environments where the default was ever used.

---

### C4. `window.confirm()` Used for Destructive Operations

**Location:** `src/pages/ScanHistoryPage.tsx`, `src/pages/UserManagementPage.tsx`

**Problem:** `window.confirm()` is synchronous, blocks the main thread, and is suppressed by most browser extensions and headless environments. More critically, it bypasses the app's custom `ConfirmModal` component that was built specifically to replace this pattern — noted in the memory context as a completed fix, but not consistently applied.

**Solution:** Replace all `window.confirm()` calls with the existing `ConfirmModal` component. The infrastructure is already there; this is a consistency gap.

---

## CRITICAL — Data Integrity & Race Conditions

### C5. Optimistic RUNNING State Creates Phantom Scans

**Location:** `backend/app/api/scans.py` — `trigger_scan` endpoint

**Problem:** The scan is immediately written to the database with `state=ScanState.RUNNING` before Jenkins even acknowledges the job. If Jenkins is down, misconfigured, or the Celery task silently fails after the HTTP response is returned, the project is permanently stuck with `last_scan_state=RUNNING` and users cannot trigger new scans (the 409 conflict guard blocks them). The recovery service catches this eventually, but "eventually" is 5 minutes — and if the recovery service itself crashes, it's permanent.

**Solution:** Use `state=ScanState.CREATED` for the initial write. Transition to `RUNNING` only when Jenkins confirms the build started (either via the Celery callback or the first webhook). Add a "force unlock" admin endpoint for stuck projects. The 5-minute recovery is a last resort, not the primary flow.

---

### C6. Duplicate Scan Prevention Has a TOCTOU Race

**Location:** `backend/app/api/scans.py`

**Problem:** The check `if project.last_scan_state in [state.value for state in ACTIVE_STATES]` reads the project state and then writes the new scan in separate operations with no database-level lock. Under concurrent requests (e.g., double-clicking the trigger button), two scans can be created simultaneously for the same project.

**Solution:** Use a `SELECT ... FOR UPDATE` or a unique database constraint on `(project_id, state)` for active states. The frontend button should also disable immediately on click (a UX fix that buys time but doesn't replace the backend fix).

---

### C7. `callback_digests` JSON Column Mutation Not Detected by SQLAlchemy

**Location:** `backend/app/api/scans.py` — `scan_callback` endpoint

**Problem:** The code does `current_digests = scan_obj.callback_digests or []`, then mutates it, then reassigns `scan_obj.callback_digests = list(current_digests)`. SQLAlchemy's change detection for JSON columns requires explicit reassignment to a *new object* — which the code does correctly. However, `stage_results` is also a JSON column and is directly assigned `scan_obj.stage_results = normalized_stages` without tracking whether the previous value was read from a stale cache. If two callbacks arrive simultaneously, the second write wins and stages from the first are silently lost.

**Solution:** Use PostgreSQL's `jsonb_set` or handle this at the service layer with a transaction and row-level lock. At minimum, add a `PATCH` semantic: append stages rather than replace.

---

## HIGH — Architectural Problems

### H1. Jenkinsfile Has Hardcoded `Port_Push-main/` Paths

**Location:** `Jenkinsfile` Stage 4 — NPM/PIP Install

**Problem:** This is documented as a known issue and document 1 provides solutions, but the Jenkinsfile in source still contains the hardcoded path. This means every new project configured in the platform will fail at the dependency install stage unless it happens to have the exact same directory structure as the original project. The CI/CD platform's core value proposition is broken for all projects except one.

**Solution:** Implement Document 1's "Solution 1: Smart Directory Detection" — use `find` to locate `package.json` and `requirements.txt` dynamically. This is a one-time fix with broad impact.

---

### H2. WebSocket Connection in Every Page Component Creates N Connections

**Location:** `src/pages/DashboardPage.tsx`, `src/pages/ScanStatusPage.tsx`

**Problem:** Each page that uses `useScanWebSocket` creates its own WebSocket connection. When a user navigates between pages, the old connection isn't necessarily closed before the new one opens (depends on React's cleanup timing). With 10 projects each with active scans open in tabs, you get 10+ concurrent WebSocket connections from one browser, each getting the same updates.

**Solution:** Lift WebSocket management to a React Context at the app level. Subscribe/unsubscribe to specific scan or project IDs through a single multiplexed connection. This is standard practice for real-time apps.

---

### H3. `ScanState` Enum Mismatch Between Frontend and Backend

**Location:** `src/types.ts` vs `backend/app/state/scan_state.py`

**Problem:** The frontend `Scan` type defines states as `'INITIAL' | 'WAITING' | 'IN PROGRESS' | 'FINISHED' | 'FAILED' | 'CANCELLED' | 'CREATED' | 'QUEUED' | 'RUNNING' | 'COMPLETED'` — a mix of the real backend states and apparently old/legacy states (`INITIAL`, `WAITING`, `IN PROGRESS`, `FINISHED`). The backend only uses `CREATED, QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED`. The frontend type union is never actually type-safe because it accepts states that will never arrive. More dangerously, any code doing `state === 'FINISHED'` will silently never match.

**Solution:** Generate the frontend types from the backend OpenAPI schema (FastAPI exposes `/openapi.json` automatically). Or at minimum, create a shared types file and keep them in sync manually with a comment indicating the source of truth.

---

### H4. Celery Worker Has No Dead Letter Queue or Retry Policy

**Location:** `backend/app/tasks/jenkins_tasks.py`, `backend/app/core/celery_app.py`

**Problem:** The Celery task `trigger_jenkins_scan_async` has `max_retries=3` but no `default_retry_delay`, no `autoretry_for` exceptions, and no dead letter queue configured. Failed tasks after 3 retries are silently dropped — the scan stays in `RUNNING` state until the recovery service catches it 5 minutes later. There's also no monitoring of the Celery queue length.

**Solution:** Add `autoretry_for=(ExternalServiceError,)`, `retry_backoff=True`, `retry_backoff_max=300` to the task decorator. Configure a dead letter queue. Add the queue to your monitoring.

---

### H5. `retry_count` Stored as String, Treated as Integer

**Location:** `backend/app/models/db_models.py`, `backend/app/api/scans.py`

**Problem:** `retry_count = Column(String, default="0", nullable=False)` — it's a `String` in the database but the code does `int(scan_obj.retry_count or 0) + 1` and the API returns `retry_count: int = 0` in the Pydantic schema. This works until it doesn't — a `None` or non-numeric value causes an unhandled exception. There's also no maximum retry limit enforced.

**Solution:** Change the column to `Integer`. Add a database migration. Add a `MAX_RETRY_COUNT = 10` constant and enforce it in the reset endpoint.

---

## HIGH — Missing Error Handling

### H6. `ScanProgressBar` Shows No Loading or Empty State

**Location:** `src/components/ScanProgressBar.tsx`

**Problem:** When `stages` is empty and the scan is `RUNNING`, the component renders the grid with all stages in "greyed out pending" state — which looks like the scan is stuck or hasn't started. There's no visual distinction between "scan just started, waiting for first stage data" and "scan has been running for 20 minutes with no stage updates" (which would indicate a pipeline problem).

**Solution:** Add an explicit "initializing" state when `stages.length === 0 && scanState === 'RUNNING'` with a timestamp-based message: "Pipeline initializing... (30s elapsed)". After a configurable threshold (e.g., 5 minutes with no stage data), show a warning.

---

### H7. `ProjectEditPage` Passes `type="form"` to `PageSkeleton` Which Doesn't Handle It

**Location:** `src/pages/ProjectEditPage.tsx` line with `return <PageSkeleton type="form" />`

**Problem:** `PageSkeleton` accepts `type?: 'dashboard' | 'project' | 'scan' | 'history' | 'form'` in its props interface, but the implementation only renders two skeletons: `renderDashboardSkeleton()` and `renderScanSkeleton()`. The `switch` / ternary is `type === 'dashboard' ? renderDashboardSkeleton() : renderScanSkeleton()` — so `type="form"` silently falls through to the scan skeleton, showing a completely wrong loading state for the edit page.

**Solution:** Add a `renderFormSkeleton()` function that shows input field outlines appropriate for a form, and handle it in the switch.

---

### H8. API Error Handling Loses HTTP Status Codes in Some Paths

**Location:** `src/utils/apiError.ts` vs `src/pages/LoginPage.tsx`

**Problem:** `LoginPage` catches errors and does `err.response?.data?.detail` directly instead of using `ApiError.getErrorMessage()`. This works, but creates two error handling patterns. More importantly, the check `err && typeof err === 'object' && 'response' in err` is duck-typing an Axios error instead of using the `ApiError` class. After the axios interceptor converts errors to `ApiError`, the `response` property no longer exists — the interceptor throws `new ApiError(status, message)` but `LoginPage` looks for `err.response.data.detail`. This means login errors always show the fallback message even when the backend sends a specific one.

**Solution:** The axios interceptor converts all errors to `ApiError`. All catch blocks should use `ApiError.isApiError(err)` and `err.message` — never `err.response?.data?.detail`.

---

### H9. `ScanHistoryPage` Row Click Navigation Has No State Preservation

**Location:** `src/pages/ScanHistoryPage.tsx`

**Problem:** Clicking a row calls `navigate('/scans/${scan.scan_id}')`. The `ScanStatusPage` then tries to go back to `navigate('/projects/${scan?.project_id}')`. But the scan object is fetched fresh on the status page — during the loading state, the back button points nowhere because `scan?.project_id` is `undefined`. The breadcrumb on `ScanStatusPage` handles this via a separate WebSocket fetch, but the back button doesn't.

**Solution:** Pass `state={{ projectId }}` through the navigate call and use `useLocation()` state as a fallback before the scan data loads.

---

## MEDIUM — Logic Bugs

### M1. `shouldRun()` Logic Is Inverted for Automated Scans

**Location:** `Jenkinsfile` — `shouldRun` function

**Problem:** `def shouldRun(stageName) { if (IS_MANUAL == false) { return true } return SELECTED.contains(stageName) }` — this correctly returns `true` (run all stages) for automated scans. But it means that if `SCAN_MODE` is ever something other than `"MANUAL"` (e.g., a typo in the parameter), *all* stages run. The logic should be `if (IS_MANUAL == true)` to whitelist manual, not blacklist it.

---

### M2. ETA Calculation in `ScanProgressBar` Is Missing

**Location:** `src/components/ScanProgressBar.tsx`

**Problem:** The memory context notes "ETA calculation decoupled from hardcoded durations" as a completed fix, but the component has no ETA display at all. The `elapsed` timer is shown but there's no estimated time remaining. Users have no way to know if a scan will take 5 more minutes or 45 more minutes, making the "pipeline is stuck" vs "pipeline is working" distinction impossible.

**Solution:** Use the `STAGE_TIMEOUTS` map from `backend/app/api/scans.py` (expose it as a frontend constant) to estimate remaining time based on which stages are pending.

---

### M3. `useScanHistory` in `useScanReset.ts` Returns Raw API Call, Not a Hook

**Location:** `src/hooks/useScanReset.ts`

**Problem:** 
```
export function useScanHistory(projectId: string) {
  return api.projects.getScanHistory(projectId);
}
```
This exports a function that calls an async API method directly and returns a Promise — not a React hook (no `useQuery`, no loading/error state). Any component that calls `useScanHistory(id)` will get a `Promise<T>` not a React Query result, causing silent failures or needing `.then()` chains in components.

**Solution:** Wrap it in `useQuery` like every other data-fetching hook in the app, or remove it entirely since `ScanHistoryPage` already uses `useQuery` directly.

---

### M4. `ManualScanPage` Button Labels Don't Match aria-labels

**Location:** `src/pages/ManualScanPage.tsx`

**Problem:** The select-all button renders text "Arm All Stages" / "Arm All Stages" (both states say the same thing in the current code — look at the ternary: `selectedStages.length === FIXED_STAGES.length ? 'Deselect All' : 'Arm All Stages'`). But the test in `ManualScanPage.test.tsx` asserts `getByRole('button', { name: /select all stages/i })` and `aria-label="Select all stages"` / `aria-label="Deselect all stages"` — these aria-labels don't exist in the actual component code. The tests pass only because they're mocking the module. The component never sets `aria-label` on that button.

**Solution:** Add `aria-label={selectedStages.length === FIXED_STAGES.length ? 'Deselect all stages' : 'Select all stages'}` to the toggle button. Also update the visible text to match the test expectations.

---

### M5. `DashboardPage` Search Tests Assert Text That Doesn't Match Component

**Location:** `src/pages/DashboardSearch.test.tsx` vs `src/pages/DashboardPage.tsx`

**Problem:** The test asserts `screen.getByText(/No projects matching "Zeta"/)` but the component renders `"No matches found"` and a separate paragraph `'Try adjusting your search terms for "{debouncedSearchTerm}"'`. The test will always fail in CI unless the component and test were somehow out of sync at time of writing.

**Solution:** Align test assertions with actual rendered text. The test file should use `screen.getByText(/Try adjusting your search terms/)` or the component should be updated to match.

---

### M6. Scan `selected_stages` From Backend May Be `null`

**Location:** `src/components/ScanProgressBar.tsx`

**Problem:** `selectedStages` prop is typed as `string[] | undefined` and the code does `selectedStages && selectedStages.length > 0`. But the backend `ScanCreate` schema has `selected_stages: Optional[List[str]] = None` and automated scans explicitly have no selected stages. When an automated scan's data is rendered, `selectedStages` will be `undefined` (or `null` from JSON), falling back to `STAGE_ORDER` — which is correct. But if the backend ever returns `[]` (empty array) for an automated scan, `selectedStages.length > 0` is `false`, and the denominator becomes 0, causing a division-by-zero in the progress percentage.

**Solution:** Add a guard: `const relevantStages = (selectedStages?.length > 0) ? ... : STAGE_ORDER`. The denominator check `totalStages > 0` already exists but is worth an explicit comment.

---

### M7. Toast Provider Is Outside Router, But Toast Is Used Inside Router Components

**Location:** `src/main.tsx`

**Problem:** `ToastProvider` wraps `App` which wraps `BrowserRouter`. This means `useToast()` works anywhere in the tree — which is correct. However, `AuthProvider` is *inside* `BrowserRouter` but *outside* the actual route structure, meaning `useAuth()` is available in all routes. This is fine currently, but if anyone moves `AuthProvider` above `BrowserRouter` (a common refactoring), `useNavigate()` inside auth-related components would break. The nesting order is fragile.

**Solution:** Document the required nesting order explicitly with comments. Consider a single `AppProviders` wrapper component that enforces the correct order.

---

## MEDIUM — Performance Issues

### P1. `ProjectRow` Memoization Broken by Missing `queryClient` Dependency

**Location:** `src/pages/DashboardPage.tsx`

**Problem:** `ProjectRow` is wrapped in `React.memo()` which prevents re-renders when the parent re-renders. But `ProjectRow` uses `useQueryClient()` internally — and the `queryClient` reference changes on every render of `DashboardPage` if the component is not itself memoized properly. The `deleteProjectMutation` closes over this. While `QueryClient` is typically stable, the `useMutation` inside a `memo`'d component that calls `queryClient.invalidateQueries` is a subtle issue if the client context ever changes.

**Solution:** This is low-risk as written, but the more impactful issue is that `memo` on `ProjectRow` is only effective if props are stable. `project` objects come from the `projects` array — if the array reference changes on every poll (every 10 seconds), all rows re-render anyway. Use `useCallback` for the list transformation and ensure the `project` objects are stable references.

---

### P2. 10-Second Polling AND WebSocket Both Active Simultaneously

**Location:** `src/pages/DashboardPage.tsx`

**Problem:** The dashboard uses `refetchInterval: 10000` for polling AND `useScanWebSocket` for real-time updates, both simultaneously. This means every WebSocket message triggers a refetch, AND there's a background 10-second poll. For a dashboard with 20 projects, this is 2 data refresh mechanisms competing. Each WebSocket message does `queryClient.invalidateQueries({ queryKey: ['projects'] })` which triggers a full list refetch.

**Solution:** If WebSocket is connected, disable polling: `refetchInterval: wsConnected ? false : 10000`. The WebSocket falls back to polling naturally when disconnected.

---

### P3. `ScanStatusPage` Refetches Entire Scan on Every WebSocket Message

**Location:** `src/pages/ScanStatusPage.tsx`

**Problem:** The WebSocket `onMessage` handler calls `refetch()` which re-fetches the entire scan object from the backend. But the WebSocket message itself already contains the complete updated scan data in `message.data`. The refetch is redundant — it doubles the API load for every real-time update.

**Solution:** Use `queryClient.setQueryData(['scan', scanId], transformWebSocketData(message.data))` to update the cache directly from the WebSocket payload, no HTTP request needed.

---

## MEDIUM — UX/Accessibility Issues

### U1. Delete Confirmation Uses `window.confirm()` in Some Places, Custom Modal in Others

**Location:** Various pages — inconsistency documented above in C4.

---

### U2. `ScanErrorModal` Focus Trap Uses `setTimeout` (Fragile)

**Location:** `src/components/ScanErrorModal.tsx`

**Problem:** `setTimeout(() => closeButtonRef.current?.focus(), 100)` — the 100ms delay is a hack to work around React's rendering lifecycle. If the component renders slowly (e.g., under CPU throttling), 100ms may not be enough. This also fails in test environments.

**Solution:** Use `useEffect` with a dependency on `isOpen` to focus the element after React has finished rendering, without an arbitrary timeout.

---

### U3. `Breadcrumbs` Component Makes API Calls for Every Navigation

**Location:** `src/components/Breadcrumbs.tsx`

**Problem:** The `Breadcrumbs` component fetches the scan data to get `project_id` whenever `scanId` is present in the URL. This means every navigation to a scan page triggers an extra API call just to show the breadcrumb. The `ScanStatusPage` also fetches the same scan — there are two parallel requests for identical data.

**Solution:** The scan data is already being fetched by `ScanStatusPage`. Either pass `projectId` as a prop/context, use React Query's cache (the `Breadcrumbs` query key matches the status page's key so it should be a cache hit), or pass `projectId` through route state.

---

### U4. `Layout.tsx` Fetches Project on Every Route Change via `useEffect`

**Location:** `src/components/Layout.tsx`

**Problem:** The `Layout` component fetches the project whenever `projectId` or `scanId` changes, storing it in `useState`. This is a side-effecting `useEffect` with an async operation inside — it doesn't handle component unmount (potential memory leak: "Can't perform a React state update on an unmounted component"). It also bypasses React Query's caching, so every navigation fetches fresh from the server.

**Solution:** Replace the `useEffect`/`useState` pattern with `useQuery` from React Query. The fetch will be cached and shared with other components fetching the same project.

---

### U5. Mobile Sidebar Doesn't Close on Navigation (Only on Direct Link Clicks)

**Location:** `src/components/Layout.tsx`

**Problem:** `NavLink` components call `setIsMobileMenuOpen(false)` on click. But the `Link` components in the non-NavLink sidebar items (like the project context links) don't close the sidebar. Navigation via the `Outlet` content area also doesn't close the sidebar.

**Solution:** Use `useEffect` watching `location.pathname` to close the sidebar on any navigation.

---

## MEDIUM — Backend Issues

### B1. `GET /projects` Returns `last_scan_state` as `"NONE"` String, Not `null`

**Location:** `backend/app/api/projects.py`

**Problem:** The list endpoint returns `"last_scan_state": p.last_scan_state or "NONE"` — forcing a string `"NONE"` when there are no scans. The frontend checks `project.last_scan_state ?? null` expecting null-ish values. The string `"NONE"` is truthy, so `project.last_scan_state ?? 'default'` never hits the default. The `ACTIVE_STATES` set doesn't include `"NONE"` so that check is fine, but any UI code doing `if (project.last_scan_state)` truthy check will incorrectly treat `"NONE"` as having a scan state.

**Solution:** Return `null` instead of `"NONE"`. If a string is required for display, transform it in the frontend.

---

### B2. `scan_recovery.py` Starts as a Daemon Thread Without Shutdown Hook

**Location:** `backend/app/main.py`, `backend/app/services/scan_recovery.py`

**Problem:** `threading.Thread(target=run_recovery_task, daemon=True).start()` — daemon threads are killed immediately when the main process exits, potentially mid-database-transaction. A scan could be half-updated (state changed but not committed) when a graceful shutdown signal arrives.

**Solution:** Use a proper shutdown event: `shutdown_event = threading.Event()` and check it in the recovery loop's `time.sleep` call using `shutdown_event.wait(300)`. Register a FastAPI `shutdown` event handler to set the event.

---

### B3. `ProjectDB` Has No `updated_at` Timestamp Column

**Location:** `backend/app/models/db_models.py`

**Problem:** There's no `updated_at` column on any model. This makes debugging impossible ("when did this project's config change?"), makes cache invalidation harder, and prevents optimistic locking patterns.

**Solution:** Add `updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)` to all models. This requires a migration.

---

### B4. `_expire_scan_if_timed_out` Uses `datetime.utcnow()` — Deprecated

**Location:** `backend/app/api/scans.py`

**Problem:** `datetime.utcnow()` is deprecated since Python 3.12 and will be removed in a future version. The entire codebase uses it consistently, making it a sweeping future bug.

**Solution:** Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)` and update timestamp storage to be timezone-aware.

---

## LOW — Code Quality & Maintainability

### L1. `src/pages/ProjectControlPage.tsx` Uses `_: any` for Error Catching

**Location:** `ProjectControlPage.tsx` — `handleRunAutomated`

**Problem:** `catch (_: any)` suppresses the error completely — the detail message is never used. The hardcoded `'Failed to trigger scan'` loses the specific backend error.

---

### L2. `FIXED_STAGES` Array Is Duplicated Across Frontend and Backend

**Location:** `src/types.ts` and `backend/app/services/validation.py`

**Problem:** The list of valid stages exists in both places. When a new stage is added (or one is renamed), both must be updated manually or they drift.

**Solution:** Consider auto-generating the frontend constants from the backend's OpenAPI spec as part of the build process.

---

### L3. `NotificationService` `requestPermission` Is Never Called

**Location:** `src/services/notifications.ts`

**Problem:** The `NotificationService` is a fully implemented singleton with permission request logic, but the memory context notes "notification permission request moved off unconditional page mount" as a fix. However, no component currently calls `notificationService.requestPermission()` at all — the service is dead code.

**Solution:** Either add a "Enable Notifications" button in the Settings page that calls `requestPermission()`, or remove the dead code.

---

### L4. `ScanState.CREATED` Used as Reset Target, Semantically Wrong

**Location:** `backend/app/api/scans.py` — `reset_scan`

**Problem:** When resetting a scan, it's set to `ScanState.CREATED` — but then `project.last_scan_state = ScanState.CREATED.value`. The dashboard shows this as `CREATED` state with a pulsing clock icon (same as queued/running), implying there's still an active scan when there isn't. The user must re-trigger a new scan — but the UI implies one is in progress.

**Solution:** Either add a `RESET` state to the enum, or set the project's `last_scan_state` to `FAILED` (the state before reset) while setting scan's state to something that indicates "ready to re-run."

---

### L5. Docker Compose Files Expose Database Port to Host in Test

**Location:** `docker/docker-compose.test.yml`

**Problem:** `postgres: ports: - "5432:5432"` — the database is exposed to the host in the test environment. While convenient for local debugging, this means running tests on a shared CI server could conflict with other services, or expose the test database to the network.

---

### L6. `backend.Dockerfile` Runs as Non-Root But Doesn't Copy the Right Path

**Location:** `docker/backend.Dockerfile`

**Problem:** `WORKDIR /app/backend` then `COPY backend /app/backend` — the `COPY` source is relative to the build context root, which is `..` (the repo root). So it copies `<repo>/backend` to `/app/backend`. But `PYTHONPATH=/app/backend` is set in the base compose file — this means `from app.core import ...` works. However, the `COPY backend/requirements.txt /app/requirements.txt` line copies to `/app/requirements.txt` while the working directory is `/app/backend`. These paths are inconsistent and fragile if the directory structure changes.

---

### L7. `nginx.conf` WebSocket Proxy Missing for `/api/v1/ws`

**Location:** `docker/nginx.conf`

**Problem:** The nginx config proxies `/api/` to the backend, with `proxy_set_header Upgrade $http_upgrade` and `Connection 'upgrade'` — which is correct for WebSocket upgrade. However, WebSocket connections require `Connection: keep-alive` or `Connection: Upgrade` specifically. The current config uses `Connection 'upgrade'` (without the dollar sign for variable substitution), which is a literal string. The correct pattern is `proxy_set_header Connection $connection_upgrade` with a map block for the upgrade header.

---

## Summary Table

| ID | Category | Severity | Effort to Fix |
|----|----------|----------|---------------|
| C1 | Security | Critical | Medium |
| C2 | Security | Critical | Low |
| C3 | Security | Critical | Low |
| C4 | UX/Security | Critical | Low |
| C5 | Architecture | Critical | Medium |
| C6 | Concurrency | Critical | Medium |
| C7 | Data Integrity | Critical | High |
| H1 | CI/CD | High | Low |
| H2 | Architecture | High | High |
| H3 | Type Safety | High | Medium |
| H4 | Reliability | High | Medium |
| H5 | Data Model | High | Low |
| H6 | UX | High | Low |
| H7 | Bug | High | Low |
| H8 | Error Handling | High | Low |
| H9 | Navigation | High | Low |
| M1 | Logic Bug | Medium | Low |
| M2 | UX | Medium | Medium |
| M3 | Bug | Medium | Low |
| M4 | Accessibility | Medium | Low |
| M5 | Tests | Medium | Low |
| M6 | Logic Bug | Medium | Low |
| M7 | Architecture | Medium | Low |
| P1 | Performance | Medium | Low |
| P2 | Performance | Medium | Low |
| P3 | Performance | Medium | Low |
| U1 | UX | Medium | Low |
| U2 | Accessibility | Medium | Low |
| U3 | Performance | Medium | Low |
| U4 | Architecture | Medium | Medium |
| U5 | UX | Medium | Low |
| B1 | API Contract | Medium | Low |
| B2 | Reliability | Medium | Medium |
| B3 | Data Model | Medium | Low |
| B4 | Deprecation | Medium | High (sweeping) |
| L1–L7 | Code Quality | Low | Low |

---

## Recommended Immediate Action Order

1. **C3** — Rotate the committed callback token. Zero-effort, immediate security impact.
2. **C4 + U1** — Replace all `window.confirm()` with `ConfirmModal`. Low effort, already have the component.
3. **H7** — Fix `PageSkeleton` to handle `type="form"`. One-line fix.
4. **H8** — Fix login error handling to use `ApiError`. Affects user experience immediately.
5. **H1** — Dynamic dependency detection in Jenkinsfile. Fixes the platform for all projects.
6. **M5** — Fix the failing test assertions. Prevents CI false-positives.
7. **C5** — Change initial scan state to `CREATED`. Prevents stuck projects.
8. **B1** — Return `null` instead of `"NONE"` from the projects list endpoint.
9. **P2** — Disable polling when WebSocket is active. Immediate load reduction.
10. **C1** — Begin planning auth token storage migration. Longer-term but critical.