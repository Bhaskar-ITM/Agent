# Task Backlog

*Future work items, prioritized*

---

## High Priority

### 1. Complete Backend `scans/` Module Migration
**Status:** Foundation created, needs completion
**Files to create:**
- `backend/app/api/scans/callbacks.py` - Jenkins callback endpoint
- `backend/app/api/scans/results.py` - GET scan results, overview endpoints
- `backend/app/api/scans/management.py` - Reset, cancel, force-unlock endpoints
- `backend/app/api/scans/history.py` - Project scan history endpoint
**Source:** Extract from `backend/app/api/scans.py` (732 lines)
**Risk:** Medium - must update all imports

### 2. Split ScanStatusPage.tsx
**Status:** Hook extracted (`useScanStatus.ts`), page still 651 lines
**Action:** Split into `ScanStatusView.tsx` (UI) + keep hooks for logic
**Risk:** Low - hook already exists

### 3. Split ProjectControlPage.tsx
**Status:** 449 lines, mixes UI with scan actions
**Action:** Extract `ProjectActions.tsx` component or `useProjectActions.ts` hook
**Risk:** Low

---

## Medium Priority

### 4. Add Toast Notification System
**Status:** Toast component exists (`src/components/Toast.tsx`) but not integrated
**Action:** Add toast provider, integrate with project deletion, scan trigger, cancel, reset
**Risk:** Low

### 5. Fix Notification Permission Timing
**Status:** Requests permission on component mount
**Action:** Only request when scan enters RUNNING state, or add opt-in banner
**Risk:** Low

### 6. Add Click-Through to Scan History
**Status:** Rows not clickable
**Action:** Make each row link to `/scans/:id`
**Risk:** Low

---

## Low Priority

### 7. Mobile Responsiveness
**Status:** Sidebar always w-64, stacks awkwardly on tablet
**Action:** Add hamburger menu for screens below lg breakpoint
**Risk:** Medium - CSS changes

### 8. Improve ETA Calculation
**Status:** Uses hardcoded stage durations
**Action:** Base on `started_at` + average historical duration, or show elapsed time
**Risk:** Low

### 9. Add Settings Page for API Key
**Status:** API key required but no UI guidance
**Action:** Add settings page or one-time setup banner
**Risk:** Low

---

## Icebox

### 10. Dark Mode
**Status:** Sidebar already bg-slate-900, palette supports it
**Action:** Add dark mode toggle
**Risk:** Low - Tailwind supports it natively

---

*When starting work, move the top task to current.md*
