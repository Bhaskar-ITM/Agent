- Stage Failure Classification:
  - HARD FAIL (Structural/Foundation):
    - Git Checkout: Foundational for all repository-based scans.
    - NPM / PIP Install: Required for source analysis and dependency checking.
    - Docker Build: Required for subsequent image scanning and pushing.
  - SOFT FAIL (Security Analysis):
    - Sonar Scanner: Analysis failure should be recorded, but SCA can proceed.
    - Sonar Quality Gate: A failed gate is a finding; it should not stop later stages.
    - Dependency Check: Vulnerability detection must not block container or network scans.
    - Trivy FS Scan: Independent source scan.
    - Trivy Image Scan: Specific to the built artifact.
    - Nmap Scan: Independent network scan.
    - ZAP Scan: Independent web application scan.
  - NON-BLOCKING (Infrastructure):
    - Docker Push: Failure to push an image is an infrastructure issue and should not invalidate security results.

- Sonar Quality Gate Policy:
  - A Quality Gate failure is classified as a "Finding," not a tool error. The pipeline continues execution to provide a complete security profile, but the final report summary will flag the project as "Failed Quality Gate."

- Tool Error vs Finding Handling:
  - Tool Error: Technical failures (timeouts, crashes, auth errors) result in a "FAILED" stage status. No security data is produced for that stage.
  - Finding: When a tool runs successfully but detects vulnerabilities. The stage status is "COMPLETED," but the result is flagged with severity counts.

- Automated vs Manual Failure Differences:
  - Automated mode: If a HARD FAIL occurs in a foundation stage, dependent stages are silently skipped as they are no longer applicable.
  - Manual mode: If a HARD FAIL occurs, dependent stages that were explicitly selected must be marked as "FAILED" with a "Dependency Error" reason to ensure user expectations are met.

- Partial Result Handling:
  - Upon a HARD FAIL or user cancellation, Jenkins must immediately finalize and publish all results collected from completed stages. The backend treats this as a partial report with a terminal state of FAILED or CANCELLED.

- Failure Communication Rules:
  - Jenkins must populate the `summary.json` with a specific `error_category` (e.g., SYSTEM_ERROR, TARGET_UNREACHABLE, AUTH_FAILURE) and a sanitized message. Technical logs are excluded from this high-level summary.

- Failure Policy Pitfalls:
  - Monolithic Failures: Letting a failure in a late, independent stage (like ZAP) wipe out valid earlier results (like Sonar).
  - Silent Finding Failures: Treating a tool crash as "No vulnerabilities found" instead of an execution failure.
  - Lack of Rationale: Skipping selected stages in Manual mode without explaining that a required prerequisite (like Docker Build) failed.
