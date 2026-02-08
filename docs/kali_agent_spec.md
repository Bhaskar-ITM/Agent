- Kali Agent Responsibilities:
  - Executing the 11 predefined security tools as directed by the Jenkins pipeline.
  - Providing a consistent, hardened environment with all necessary binaries and libraries pre-installed.
  - Managing temporary workspace files and ensuring local scan results are available for backend ingestion.
  - Ensuring outbound network reachability for tools that require external scanning (Nmap, ZAP) or database updates (Trivy, Dependency Check).

- Kali Agent Non-Responsibilities:
  - Storing long-term scan results, reports, or historical data.
  - Managing user authentication, project membership, or platform-level permissions.
  - Making business logic decisions about which stages to run or determining project tech stacks.
  - Persisting repository secrets or sensitive credentials between discrete scan executions.

- Baseline OS & Permission Assumptions:
  - OS: Standard Kali Linux distribution optimized for headless execution.
  - User: A dedicated non-privileged service user (e.g., `jenkins-agent`) for all execution.
  - Permissions: Strict "Principle of Least Privilege"; `sudo` access is forbidden except for specific, audited exceptions required for containerization.
  - Filesystem: Standardized, high-speed ephemeral storage for workspaces with enforced disk quotas.

- Required Tool Categories:
  - Version Control & Source Access: Git CLI.
  - Language Runtimes & Dependency Managers: Node.js/NPM, Python/PIP.
  - Static & Dependency Analysis: Sonar Scanner CLI, Dependency Check, Trivy.
  - Containerization Engine: Docker (Buildx supported).
  - Network & Web Security Assessment: Nmap, OWASP ZAP (Headless).

- Workspace & Cleanup Rules:
  - Mandatory Isolation: Each `scan_id` must operate within a unique, isolated workspace directory.
  - Immediate Post-Scan Cleanup: Cloned source code, temporary build artifacts, and intermediate Docker layers must be purged once the scan reaches a terminal state.
  - Garbage Collection: Automated system-level cleanup to prune unused Docker images, volumes, and stale caches.

- Concurrency & Reuse Behavior:
  - Concurrent Capability: The agent must support multiple concurrent jobs within the bounds of available CPU and Memory.
  - No State Bleed: Each job must be deterministic; execution of one scan must not modify the environment or data available to another.
  - Safe Optimization: Shared read-only caches (e.g., vulnerability databases) are permitted to improve performance.

- Agent Misconfiguration Risks:
  - Binary Path Inconsistency: Discrepancies between tool versions across different agents or environment variable drift.
  - Workspace Pollution: Failing to clean up between scans, leading to storage exhaustion or data leakage.
  - Root Execution: Running security tools with elevated privileges, creating a significant security risk for the agent host.
  - Network Blindness: Restrictive egress rules that prevent Trivy from updating vulnerability databases or ZAP from reaching the target URL.
