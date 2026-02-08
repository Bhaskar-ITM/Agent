- Scan Identity Rules:
  - Every scan is assigned a universally unique identifier (UUID v4) by the backend at the moment of request ingestion.
  - This `scan_id` is the primary key for all telemetry, logs, and artifacts associated with the execution.

- Idempotency Rules:
  - All scan initiation requests must include a client-generated `idempotency_key` (UUID).
  - The backend will cache this key for 24 hours; subsequent requests with the same key for the same project will return the original `scan_id` and its current state instead of triggering a new execution.

- Project-Level Concurrency Policy:
  - Strict Serialization: Only ONE active scan (states: QUEUED or RUNNING) is allowed per Project at any given time.
  - This prevents workspace collisions on the Kali agent and ensures that results are logically tied to a specific point-in-time state of the repository.

- Isolation or Locking Strategy:
  - Pessimistic Locking: When a scan request is validated, the backend attempts to acquire an exclusive lock on the `project_id`.
  - If a lock is already held (indicating an active scan), the request is rejected with a `409 Conflict` error, informing the user that "A scan is already in progress for this project."

- Retry vs New Scan Rules:
  - All retries (manual or system-triggered) are treated as NEW scans with a fresh `scan_id`.
  - There is no "resume" capability; failure in any critical stage moves the `scan_id` to a FAILED terminal state, requiring a clean start for the next attempt.

- Race Condition Scenarios & Mitigations:
  - Double-Trigger: Two users click "Run Scan" simultaneously. Mitigation: Database-level transaction isolation (Serializable) ensures only one request can successfully transition from "No active scan" to "Locked for execution."
  - Ghost Scans: Jenkins job fails to report back. Mitigation: Backend enforces a "stale scan" timeout; if no status update is received within a defined TTL, the lock is forcefully released and the scan is marked as FAILED with a system timeout reason.
