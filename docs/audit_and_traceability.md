- Scan-Level Audit Data:
  - Unique Identifiers: `scan_id` (UUID v4) and `project_id` (UUID v4).
  - Actor Information: `triggered_by` (User ID or System/Webhook source).
  - Scan Context: `scan_mode` (AUTOMATED | MANUAL) and `selected_stages` (for Manual mode).
  - Source Metadata: `repo_url`, `repo_branch`, and the resolved `commit_hash`.
  - Execution Parameters: Snapshotted `target_ip`, `target_url`, and environment versioning.
  - Lifecycle Timestamps: Timestamps for when the scan was created, queued, started, and finished.
  - Results Integrity: A SHA-256 `findings_summary_hash` of the final normalized result set.

- User-Action Audit Data:
  - `action_id`: Unique identifier for the specific event.
  - `user_id` and `source_ip`: Identification of the human or system actor.
  - `action_type`: Categories such as `CREATE_PROJECT`, `TRIGGER_SCAN`, `CANCEL_SCAN`, or `DOWNLOAD_ARTIFACT`.
  - `resource_id`: Reference to the scan or project affected by the action.
  - `outcome`: Success or failure of the requested action.

- Traceability Model:
  - **Snapshotting**: All project configuration and target details are copied into the scan record at the time of initiation to ensure a point-in-time record.
  - **Chain of Custody**: The `scan_id` is propagated through every layer (Backend -> Jenkins -> Kali Agent) and must appear in every log entry and artifact filename.
  - **Version Anchoring**: Every code-based scan is anchored to a specific `commit_hash`, ensuring results can be mapped back to the exact state of the source code.

- Incident & Compliance Support:
  - **Forensic Reconstruction**: Enables SOC teams to reconstruct the exact conditions of a scan during security incidents.
  - **Compliance Proof**: Provides evidence that mandated security stages (e.g., SCA, DAST) were executed within required timeframes.
  - **Tamper Detection**: Comparison of stored result summaries against their original hashes to verify data integrity.

- Retention Principles:
  - **Audit Metadata & Logs**: Retained for a minimum of 7 years to meet enterprise compliance standards.
  - **Normalized Results**: Retained for 2 years to support year-over-year security posture analysis.
  - **Raw Artifacts**: ephemerally stored for 90 days before automated purge, balancing forensic needs with storage costs.

- Immutable Audit Data:
  - Once a scan reaches a terminal state, its `scan_id`, `timestamps`, `actor`, `commit_hash`, and `findings_summary_hash` must be protected against modification or deletion.
  - User action logs must be append-only and immutable.

- Audit & Traceability Pitfalls:
  - **Context Loss**: Failing to record the resolved commit hash, leaving the team guessing which code version was scanned.
  - **Parameter Drift**: Referencing "Current Project Config" in old reports instead of the snapshotted execution context.
  - **Log Fragmentation**: Allowing technical logs on the Kali agent to be rotated and lost before they are correlated with the `scan_id`.
  - **Silent Skips**: Failing to log the specific rationale for skipped stages in Automated mode, creating compliance gaps.
