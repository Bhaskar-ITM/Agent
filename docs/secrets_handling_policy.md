- Secret Storage & Reference Model:
  - Centralized Vault: All actual secret values (Git SSH keys, API tokens, Registry credentials) are stored in an enterprise-grade vault (e.g., HashiCorp Vault or Jenkins Credentials Store).
  - UUID References: The backend and UI only store and transmit unique identifiers (UUIDs) for these secrets, never the raw values.
  - Runtime Injection: Raw secrets are injected as environment variables or temporary memory-backed files ONLY on the Kali execution agent at the moment of use.

- Secret Lifecycle:
  - Request: Backend identifies required secrets based on project metadata.
  - Injection: Jenkins retrieves secret values from the vault and passes them to the Kali agent via secure environment masking.
  - Usage: Security tools consume secrets from environment variables.
  - Disposal: Secrets are purged from the environment immediately upon stage completion or scan termination. No secrets are persisted in workspaces.

- Forbidden Secret Exposure Areas:
  - Jenkins Console Logs: All secrets must be explicitly masked using Jenkins log filtering.
  - Application UI: The UI must only display redacted metadata (e.g., "SSH Key Added on 2023-01-01").
  - Scan Artifacts: Raw tool reports and normalized summaries must be scrubbed of any credential strings.
  - Backend Database: Only encrypted credential references are permitted.

- Secret Scoping Rules:
  - Project Scope: General repository access credentials (Git/Sonar).
  - Stage Scope: Ephemeral credentials for specific actions (e.g., temporary registry tokens for Docker Push).
  - Environment Isolation: Secrets used for development projects must be strictly isolated from production-level scan credentials.

- Leakage Detection & Prevention:
  - Mandatory Masking: All CI/CD output is passed through a pattern-matching filter to catch unmasked strings.
  - Audit Logging: Every secret access event (who, when, what scan) is recorded in a tamper-proof audit trail.
  - Tool Hardening: Security tools are configured to read from standard input or environment variables rather than command-line arguments to avoid `ps` exposure.

- Rotation & Update Strategy:
  - Blue/Green Rotation: New credentials can be added as a separate reference; projects are updated to the new reference without interrupting active scans.
  - Automatic Expiry: Support for time-bound, ephemeral credentials for high-risk operations (e.g., cloud provider OIDC tokens).

- Secrets Handling Pitfalls:
  - Logging to Disk: Allowing tools to write credentials to temporary debug logs in the workspace.
  - Command-Line Exposure: Passing passwords as cleartext arguments (visible in process lists).
  - Global Scoping: Using the same high-privileged service account for all scans regardless of the project's risk profile.
  - Manual Secret Management: Relying on manual updates of raw strings in pipeline configurations instead of central vault references.
