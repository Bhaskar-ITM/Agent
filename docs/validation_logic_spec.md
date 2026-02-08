- Project Validation Rules:
  - Project Name: Must be unique within the organization and match the regex `^[a-zA-Z0-9-_]{3,50}$`.
  - Repository URL: Must be a valid Git URI (HTTPS or SSH format).
  - Default Branch: Must not be empty and should follow Git branch naming conventions.

- Automated Scan Validation Rules:
  - Project Status: The project must exist and must not have a scan currently in an 'Active' or 'Queued' state (enforcing one active scan per project).
  - Repository Accessibility: The system performs a basic reachability check on the stored Repository URL.

- Manual Scan Validation Rules:
  - Selection Requirement: At least one of the 11 security stages must be explicitly selected.
  - Mandatory Inputs: For every selected stage that requires external targets, the corresponding input field must be populated.
  - Format Enforcement: Provided inputs (IPs, URLs) must match their respective strict regex patterns.

- Stage-to-Input Validation Map:
  - Nmap Scan: Requires `target_host` (must be a valid IPv4, IPv6, or CIDR range).
  - ZAP Scan: Requires `target_url` (must be a valid HTTP or HTTPS absolute URI).
  - (All other stages rely on the validated Repository URL and Default Branch from the Project definition).

- Error vs Warning Rules:
  - Validation ERROR: Critical issues that prevent execution (e.g., Malformed IP for Nmap, Missing Repository URL, Active Scan Conflict, Authentication failure for private repos).
  - Validation WARNING: Non-blocking observations that suggest potential misconfiguration (e.g., Target URL uses insecure HTTP, Default Branch is not 'main' or 'master', Optional description field is missing).

- Rejection vs Allowance Rules:
  - REJECT: Any request containing one or more Validation ERRORS is immediately terminated with a `400 Bad Request`.
  - ALLOW: Requests with zero ERRORS are permitted to proceed to the execution queue, even if Validation WARNINGS are present.

- Validation Error Communication:
  - The API returns a structured JSON object containing an `errors` array and a `warnings` array.
  - Each entry includes the `field_name` (e.g., `target_url`), a `code` (e.g., `INVALID_FORMAT`), and a human-readable `message` suitable for direct UI display.
