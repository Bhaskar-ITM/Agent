- Error Categories:
  - **Validation Errors**: Client-side or API-level input issues (e.g., invalid repository URL, malformed IP address). Handled synchronously before a scan is created.
  - **Execution Errors**: Failures within the 11 pipeline stages (e.g., tool crash, network timeout during scan, target host unreachable).
  - **Infrastructure Errors**: Failures of the underlying platform (e.g., Jenkins offline, Kali agent disk exhaustion, connection loss between backend and orchestrator).
  - **User-Initiated Errors**: Explicit termination of a scan by a user (Cancellation).

- Error-to-State Mapping:
  - **Validation Error**: Request rejected; scan status remains `CREATED` or is not persisted.
  - **Execution Error (Soft Fail)**: Pipeline continues; stage status marked as `FAILED`; final scan state is `COMPLETED` (with warnings).
  - **Execution Error (Hard Fail)**: Pipeline stops; stage status marked as `FAILED`; final scan state is `FAILED`.
  - **Infrastructure Error**: Backend detects system failure; marks active scan as `FAILED` with a system-level reason.
  - **User-Initiated**: Backend signals Jenkins to stop; marks scan as `CANCELLED`.

- Partial Failure Representation:
  - Terminal scan reports (FAILED or CANCELLED) must include results from all stages that reached a terminal status before the error.
  - The UI summary will explicitly label the report as "Partial Results" and identify the stage where execution halted.

- Retry & Re-run Rules:
  - **No Resume**: Resuming a failed or cancelled scan is strictly prohibited to ensure data integrity and determinism.
  - **Manual Re-run**: Any retry generates a completely new `scan_id` with a fresh workspace.
  - **Idempotency Protection**: Automated retries are forbidden for active scanning stages (Nmap, ZAP) to prevent unintended denial-of-service on target systems.

- Recovery Scenarios:
  - **Jenkins Restart**: Backend reconciliation logic detects "lost" jobs; affected scans are transitioned to `FAILED` with the reason `SYSTEM_RESTARTED`.
  - **Agent Crash**: Pipeline heartbeat or timeout triggers; backend marks scan as `FAILED` and releases project-level execution locks.
  - **Network Interruption**: Backend implements transient retry logic for Jenkins API calls; if the partition persists, the scan is marked as `FAILED` with `ORCHESTRATION_TIMEOUT`.

- User-Facing Error Communication:
  - Map technical error codes to functional categories: "Target Connection Failed," "Source Code Access Denied," "System Capacity Reached," "Scan Cancelled by User."
  - Prohibit the display of raw Jenkins console logs, Kali terminal outputs, or system file paths to maintain abstraction.

- Reliability Pitfalls & Preventive Measures:
  - **Pitfall**: Ghost Scans (jobs that run but aren't tracked). **Measure**: Backend-enforced TTL and mandatory periodic state synchronization with Jenkins.
  - **Pitfall**: Resource Leaks. **Measure**: Automated reaping of orphaned processes/containers and 24-hour workspace TTL on the Kali agent.
  - **Pitfall**: Silent Failure. **Measure**: Every stage must produce a terminal status artifact (`summary.json`); absence of this artifact triggers a Hard Fail.
