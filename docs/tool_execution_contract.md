- Standard Tool Inputs:
  - Isolated Workspace: A dedicated filesystem path for the current scan execution.
  - Scan Target: The specific asset to analyze (Git repository path, Target IP, or Target URL).
  - Mode Context: Flags indicating if the execution is part of an Automated or Manual scan.
  - Output Destination: A predefined path where all reports and logs must be saved.
  - Secrets & Credentials: Environment variables injected at runtime (never stored on disk).

- Standard Tool Outputs:
  - Native Report: The raw output file produced by the tool (e.g., XML, JSON, HTML).
  - Normalized Summary: A standardized JSON file containing execution status and a high-level severity breakdown (Critical, High, Medium, Low).
  - Execution Logs: Standard output and error streams captured for technical debugging.

- Exit Code Interpretation:
  - 0: Successful Execution (The tool ran to completion, regardless of findings).
  - 1-125: Execution Error (Tool crash, misconfiguration, or invalid target).
  - 126+: Infrastructure Error (Tool binary not found, permission denied, or system timeout).

- Findings vs Execution Failure Rules:
  - Findings: A stage is considered successful if it exits with 0 and produces a valid report, even if it detects vulnerabilities.
  - Execution Failure: Any non-zero exit code or failure to produce the Normalized Summary constitutes an execution failure. The backend must ignore results from failed stages.

- Logging Rules:
  - Lifecycle Logs: High-level start/stop/status messages are logged to the Jenkins console.
  - Tool Verbosity: Detailed tool logs are redirected to a dedicated log file artifact.
  - Scrubbing: All logs must be passed through a filter to mask sensitive data (keys, tokens).

- Artifact Handling Rules:
  - Naming Convention: `{scan_id}-{stage_key}.[raw|summary|log]`.
  - Persistence: Artifacts are ephemeral on the agent and must be offloaded by the backend immediately upon scan completion.
  - Referencing: The backend uses the `scan_id` and `stage_key` to programmatically retrieve specific reports.

- Isolation Rules:
  - Process Isolation: Every tool executes as a discrete process with its own environment space.
  - Filesystem Isolation: Tools must only have write access to their designated output directory and the current workspace.
  - Network Isolation: Tools should only have the minimum required network egress for their specific scanning purpose.

- Tool Integration Pitfalls:
  - Exit Code Ambiguity: Interpreting "vulnerabilities found" as a tool error (non-zero exit), which falsely triggers pipeline failure alerts.
  - Raw Output Dependency: Relying on parsing tool-specific terminal output instead of structured reports.
  - Workspace Pollution: Tools creating files outside of the designated output path, causing cleanup failures or data leakage.
  - Silent Errors: Tools exiting with code 0 even when they failed to connect to a target or scan any files.
