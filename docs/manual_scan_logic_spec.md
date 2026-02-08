- Stage Selection Interpretation:
  The `SELECTED_STAGES` parameter is treated as a strict whitelist. Jenkins parses this comma-separated string into a lookup set. Any stage ID not present in this set is immediately marked as "User Excluded" and its execution logic is bypassed entirely.

- Per-Stage Execution Check:
  At the start of every one of the 11 stages, the pipeline evaluates a guard condition: `isStageSelected(STAGE_ID)`. If false, the stage is skipped. If true, the pipeline checks if the stage's hard dependencies (e.g., Git Checkout) were also selected and successfully completed. If a selected stage depends on an unselected or failed stage, it must fail with a "Missing Dependency" error.

- Required Input Enforcement:
  Jenkins relies entirely on environment variables passed by the backend.
  - ZAP Scan: `TARGET_URL` must be provided.
  - Nmap Scan: `TARGET_IP` must be provided.
  - Source-based scans: The workspace must contain the necessary files; however, Jenkins does not "discover" them—it simply attempts execution and fails if they are missing.

- Invalid Execution Handling:
  If a selected stage lacks its required input (e.g., ZAP is selected but `TARGET_URL` is empty), the stage must FAIL immediately. It must NOT attempt to guess a target or skip silently. The failure message must explicitly state: "Manual execution failed: Required input [INPUT_NAME] missing."

- Skip vs Fail Semantics:
  - SKIP: Applied only to stages NOT present in the `SELECTED_STAGES` list. A skip in Manual mode represents a deliberate user exclusion.
  - FAIL: Applied to any selected stage that cannot execute due to missing inputs, failed dependencies, or technical errors. In Manual mode, a selected stage NEVER skips silently.

- Hidden Execution Prevention Rules:
  - No Implicit Stages: Jenkins must not automatically run "NPM Install" just because "Sonar Scanner" was selected; both must be explicitly included in the `SELECTED_STAGES` list by the backend/user.
  - Zero Discovery: The pipeline is forbidden from searching the filesystem to determine eligibility; it must follow the `SELECTED_STAGES` list blindly.
  - Parameter Isolation: Stages must only use the specific parameters provided for that execution, ensuring no carry-over of "auto-detected" state from previous runs.

- Manual Mode Pitfalls:
  - Unintended Dependency Skipping: Failing to select a required setup stage (like Git Checkout) and expecting downstream analysis to work.
  - Silent File Missing: Skipping a selected Docker scan because a `Dockerfile` is missing instead of failing the stage.
  - Trust Erosion: Jenkins "helpfully" running unselected stages to make the pipeline work, which violates the user's explicit control.
