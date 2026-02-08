- Stage Eligibility Definitions:
  - Git Checkout: Always eligible; the foundation of all repository-based scans.
  - Sonar Scanner: Eligible if source code is detected post-checkout.
  - Sonar Quality Gate: Eligible only if the Sonar Scanner stage successfully publishes a report.
  - NPM / PIP Install: Eligible if a `package.json` (NPM) or `requirements.txt` (PIP) is detected.
  - Dependency Check: Eligible if the environment is prepared via NPM / PIP Install or if lockfiles are present.
  - Trivy FS Scan: Always eligible if a filesystem is available after Git Checkout.
  - Docker Build: Eligible if a `Dockerfile` is detected in the project root.
  - Docker Push: Eligible only if the Docker Build stage successfully completes.
  - Trivy Image Scan: Eligible only if the Docker Build stage successfully completes.
  - Nmap Scan: Eligible if a valid `TARGET_IP` or hostname is provided in the scan context.
  - ZAP Scan: Eligible if a valid `TARGET_URL` is provided in the scan context.

- Discovery Signals:
  - File Presence: `package.json`, `requirements.txt`, `Dockerfile`.
  - Contextual Parameters: `TARGET_IP`, `TARGET_URL` (passed from backend).
  - Pipeline State: Success status of preceding hard-dependency stages.

- Skip vs Fail Rules:
  - SKIP: Triggered when discovery signals are absent (e.g., no `Dockerfile` detected). A skip is silent and does not count as a failure.
  - FAIL: Triggered when an eligible stage begins execution but encounters a technical error (e.g., network timeout, tool binary crash, invalid syntax).

- Optional Input Handling:
  - If optional targets (`TARGET_IP`, `TARGET_URL`) are missing, the corresponding stages (Nmap, ZAP) are marked as "Skipped: Input Not Provided."
  - The pipeline must not error out due to missing optional parameters in Automated mode.

- Early Failure Behavior:
  - Pipeline Termination: Failure in "Git Checkout" is a fatal error that terminates the entire run.
  - Dependency Cascading: If a stage fails, all stages that list it as a hard dependency (e.g., Docker Build -> Trivy Image Scan) are automatically skipped.
  - Non-Blocking Failures: Failures in analysis stages (e.g., Sonar Quality Gate, Nmap) do not block the execution of unrelated downstream stages.

- Predictability & Explainability Rules:
  - Every decision to skip or execute a stage must be logged with a clear rationale in the Jenkins console output.
  - The final `summary.json` must include a status for all 11 stages to ensure the user understands exactly what was run and what was omitted.
  - Heuristics are forbidden; the pipeline must use deterministic file-matching or parameter-checking logic.

- Automation Pitfalls:
  - False Skips: Misinterpreting a transient tool failure as a reason to skip subsequent independent stages.
  - Discovery Bloat: Triggering stages based on secondary or sample files found deep in subdirectories (logic should favor root-level or defined-path signals).
  - Silent Dependency Failures: Proceeding with a stage when its required predecessor failed but was not correctly caught by the eligibility check.
