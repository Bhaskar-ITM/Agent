- Per-Stage Timeout Policy:
  - Fast-Static (Git, NPM Install, Trivy FS): 15 minutes.
  - Deep-Analysis (Sonar, Dependency Check): 45 minutes.
  - Build-Heavy (Docker Build, Push): 60 minutes.
  - Active-Scan (Nmap, ZAP): 60 minutes.
  - These are maximum thresholds; stages should typically complete in much less time.

- Per-Scan Timeout Policy:
  - Global Scan Limit: 4 hours. Any pipeline exceeding this duration is forcefully terminated by Jenkins to prevent resource starvation.

- Timeout Classification Rules:
  - Stage Timeout: Classified as a "SOFT FAIL" for the specific stage. The stage status is marked as FAILED with the reason `STAGE_TIMEOUT`. The pipeline attempts to proceed to independent downstream stages.
  - Global Timeout: Classified as a "HARD FAIL" for the entire scan. The scan status is marked as FAILED with the reason `SCAN_TIMEOUT`.

- Resource Limit Principles:
  - CPU/Memory: Enforced via container-level constraints (CGroups) or process-level limits (ulimit). No single tool should consume more than 75% of available agent resources.
  - Disk: Enforced via workspace volume quotas. Scans must not exceed a predefined storage limit (e.g., 50GB) for repositories and build artifacts.

- Over-Limit Handling:
  - Immediate Termination: Any process or container exceeding CPU, Memory, or Disk quotas must be immediately SIGKILLed by the agent/orchestrator.
  - Error Reporting: The stage must report a terminal FAILURE with a `RESOURCE_EXCEEDED` reason.

- Cleanup Rules:
  - Success/Fail/Cancel: In all terminal states, the workspace directory must be recursively deleted.
  - Image Purging: Temporary Docker images created during "Docker Build" must be removed immediately after "Docker Push" or scan termination.
  - Cache Management: Only verified tool caches (e.g., Sonar/NPM) are retained between scans; all other ephemeral data is purged.

- Orphaned Resource Handling:
  - Label-Based Reaping: All processes and containers must be tagged with the unique `scan_id`.
  - Automated Reaper: A periodic background process on the Kali agent identifies and kills any resource with an active `scan_id` whose Jenkins job is no longer running.
  - Workspace TTL: Any workspace older than 24 hours is automatically deleted, regardless of status.

- Timeout & Cleanup Pitfalls:
  - Zombie Processes: Tools that fork sub-processes (like Nmap) not being properly cleaned up on stage timeout.
  - Disk Exhaustion: Repeated failed scans that bypass cleanup logic, leading to agent-wide failure.
  - Silent Stalling: Tools that hang indefinitely without consuming resources, requiring strict active-timer enforcement.
