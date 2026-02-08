- Required Jenkins Inputs:
  - `SCAN_ID`: Unique UUID identifying the specific execution.
  - `PROJECT_ID`: Unique UUID identifying the project.
  - `REPO_URL`: The Git repository URL to be analyzed.
  - `REPO_BRANCH`: The branch or tag to be checked out.
  - `SCAN_MODE`: Selection between `AUTOMATED` or `MANUAL`.

- Optional Jenkins Inputs:
  - `TARGET_URL`: Required for web-application scanning (ZAP).
  - `TARGET_IP`: Required for network-level scanning (Nmap).
  - `SELECTED_STAGES`: A comma-separated list of stage identifiers (required if `SCAN_MODE` is `MANUAL`).
  - `REPO_CREDENTIAL_ID`: The Jenkins identifier for repository access credentials.

- Scan Identity Handling:
  - Jenkins must treat the `SCAN_ID` as the immutable primary key for the duration of the job.
  - All logs and generated artifacts must be tagged or named using the `SCAN_ID` to ensure reliable ingestion by the backend.

- Automated vs Manual Signaling:
  - Mode is controlled by the `SCAN_MODE` parameter.
  - If `SCAN_MODE` is `MANUAL`, Jenkins is forbidden from executing any stage not present in `SELECTED_STAGES`.
  - If `SCAN_MODE` is `AUTOMATED`, Jenkins triggers its internal discovery logic to determine which of the 11 stages are applicable.

- Manual Stage Representation:
  - Stages are represented by a fixed set of 11 keys: `git-checkout`, `sonar-scanner`, `sonar-quality-gate`, `install-dependencies`, `dependency-check`, `trivy-fs`, `docker-build`, `docker-push`, `trivy-image`, `nmap-scan`, `zap-scan`.

- Read-Only vs Runtime Variables:
  - Read-Only: All input parameters (`SCAN_ID`, `REPO_URL`, etc.) are immutable once the job initiates.
  - Runtime: Workspace paths, temporary credentials, and individual stage execution statuses are runtime-only and managed exclusively within the pipeline.

- Jenkins Non-Responsibilities:
  - Jenkins must NEVER decide if a user has permission to trigger a scan.
  - Jenkins must NEVER store long-term scan history or project metadata.
  - Jenkins must NEVER fetch project configuration from external sources (must receive all data as parameters).
  - Jenkins must NEVER attempt to remediate vulnerabilities or update source code.

- Execution Status Reporting (High-Level):
  - Jenkins must produce a standardized terminal artifact (`summary.json`) containing the status (Success/Failure/Skipped) for each of the 11 stages.
  - The backend is responsible for monitoring the job status via the Jenkins API and ingesting the summary artifact once the job reaches a terminal state.
