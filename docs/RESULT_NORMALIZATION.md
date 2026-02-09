- Standard Result Schema:
  Every stage must produce a `summary.json` following this structure:
  - `scan_id`: Unique identifier for the scan.
  - `stage_id`: The fixed stage key (e.g., `sonar-scanner`, `zap-scan`).
  - `status`: Execution outcome (PASS, FAIL, WARN, SKIPPED).
  - `findings`: An object mapping severity levels (`critical`, `high`, `medium`, `low`, `info`) to integer counts.
  - `artifact_ref`: A UUID reference to the raw, tool-specific output file.
  - `timestamp`: ISO-8601 completion time.
  - `error_info`: (Optional) Detailed category and message for FAIL statuses.

- Result Status Definitions:
  - PASS: The tool executed successfully and detected zero issues above the organization's risk threshold.
  - FAIL: A technical execution error occurred (e.g., timeout, auth failure) OR a critical quality gate was not met.
  - WARN: The tool executed successfully but detected vulnerabilities that require review (e.g., Medium/High findings).
  - SKIPPED: The stage was not applicable to the tech stack (Automated) or was not selected by the user (Manual).

- Severity Representation & Aggregation:
  - Tool-specific severities (e.g., Sonar's "Blocker", ZAP's "High") are mapped to the platform's standard five-tier scale.
  - Scan-level results aggregate these counts by summing the findings from all successful stages.

- Raw Output Referencing Rules:
  - Raw artifacts must NEVER be exposed directly in the primary UI.
  - The UI/Backend uses the `artifact_ref` to fetch detailed evidence only when explicitly requested by an "Advanced User."
  - Retention of raw artifacts is separate from the lifecycle of the normalized summary data.

- Partial Result Handling:
  - Upon pipeline failure or cancellation, the platform must ingest all available `summary.json` files from completed stages.
  - Unfinished stages are marked as SKIPPED with a metadata flag indicating "Pipeline Aborted."

- Automated vs Manual Result Consistency:
  - The reporting schema is identical for both modes.
  - In Manual mode, user-excluded stages are explicitly marked as SKIPPED to ensure the total of 11 stages is always accounted for in the report.

- Result Normalization Pitfalls:
  - Tool Leakage: Allowing tool-specific terminology (e.g., "Vulnerability" vs "Bug") to reach the executive dashboard.
  - Severity Mismatch: Inconsistent mapping where one tool's "Medium" is treated as another's "Low."
  - Silent Discard: Failing to report a FAILED stage status, leading users to believe an area was "clean" when it was actually not scanned.
