# System Design: Security Scanning Platform

## End-to-End Flow

### Automated Scan (Default)
1. **UI**: User clicks "Run Automated Scan" on a project card.
2. **Backend**:
   - Validates project and ensures no concurrent scan.
   - Generates unique `scan_id`.
   - Transitions state: `CREATED` -> `QUEUED`.
   - Triggers Jenkins with `mode=AUTOMATED`.
3. **Jenkins (Orchestrator)**:
   - Receives parameters and starts job.
   - Transitions state: `QUEUED` -> `RUNNING` (via Backend observation).
4. **Kali Agent (Execution)**:
   - Performs `Git Checkout`.
   - Executes Discovery Logic (file-based).
   - Runs eligible stages; silently skips inapplicable ones.
   - Produces `summary.json` and raw artifacts.
5. **Backend**:
   - Detects completion.
   - Ingests and normalizes results.
   - Transitions state: `RUNNING` -> `COMPLETED`.
6. **UI**: Displays normalized severity dashboard and findings.

### Manual Scan (Advanced)
1. **UI**: User selects specific stages and provides mandatory targets (IP/URL).
2. **Backend**:
   - Performs strict input validation (regex/format).
   - Generates unique `scan_id`.
   - Transitions state: `CREATED` -> `QUEUED`.
   - Triggers Jenkins with `mode=MANUAL` and `selected_stages`.
3. **Jenkins (Orchestrator)**:
   - Starts job.
   - Transitions state: `QUEUED` -> `RUNNING`.
4. **Kali Agent (Execution)**:
   - Performs `Git Checkout`.
   - Bypasses discovery; iterates strictly through `selected_stages`.
   - Fails immediately if a selected stage lacks required input.
   - Produces `summary.json` and raw artifacts.
5. **Backend**:
   - Ingests results.
   - Transitions state: `RUNNING` -> `COMPLETED` (or `FAILED` on execution error).
6. **UI**: Displays results for explicitly selected stages.

---

## Layer-by-Layer Responsibilities

### 1. Web UI
- **Role**: Intent capture and visualization.
- **Constraints**: Never decides eligibility; never exposes Jenkins/Kali internals.
- **Inputs**: User interaction and API responses.
- **Outputs**: Display of scan status, severity counts, and prioritized findings.

### 2. Backend API
- **Role**: Orchestrator and Single Source of Truth.
- **Constraints**: Validates all requests; owns the Scan State Machine; stores results and audit logs.
- **Inputs**: User intent (via UI), execution status (via Jenkins).
- **Outputs**: Scan identity (`scan_id`), normalized results, and immutable audit trails.

### 3. Jenkins
- **Role**: Execution Engine.
- **Constraints**: Statless; never stores authoritative data; applies mode-specific gating (Discovery vs. Whitelist).
- **Inputs**: `scan_id`, `repo_url`, `mode`, `selected_stages`, `targets`.
- **Outputs**: `summary.json` (per-stage status) and structured tool artifacts.

### 4. Kali Linux Agent
- **Role**: Tool Execution Host.
- **Constraints**: Isolated workspaces; mandatory post-scan cleanup; no decision-making authority.
- **Inputs**: Process commands and local workspace access.
- **Outputs**: Raw tool reports and technical logs (offloaded immediately).

---

## Deterministic Behavior

- **Scan Identity**: Every execution is assigned a UUID v4; re-runs generate fresh identities.
- **State Machine**: Strict transitions: `CREATED` -> `QUEUED` -> `RUNNING` -> `TERMINAL (COMPLETED/FAILED/CANCELLED)`.
- **Skip Semantics**:
  - `SKIP`: Silent omission due to ineligibility (Automated) or user exclusion (Manual).
- **Fail Semantics**:
  - `FAIL`: Tool error, missing mandatory input (Manual), or structural dependency failure.
- **Concurrency**: Strict serialization per Project; only one active scan allowed at a time.

---

## Production-Ready Reasoning

- **Reliability**: Per-stage and global timeouts prevent hung scans from exhausting resources.
- **Security**: Secrets are injected just-in-time at the execution layer and never persisted or logged.
- **Observability**: Standardized logging (`[STAGE START]`, `[STAGE SUCCESS]`) ensures auditability without leaking technical noise to end-users.
- **Abstraction**: Users interact with functional security concepts (e.g., "Code Analysis"), while the platform manages the complexity of Kali and Jenkins.
