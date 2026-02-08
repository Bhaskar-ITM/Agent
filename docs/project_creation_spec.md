- Required Fields:
  - Project Name (unique internal identifier)
  - Repository URL (public or private Git repository)
  - Default Branch (the primary branch for security assessments)

- Optional Fields:
  - Target Application URL (entry point for web application security testing)
  - Target Host/IP (hostname or IP for network-level assessments)
  - Repository Access Credentials (SSH key or Token selection)

- Default Values:
  - Default Branch: `main`
  - Repository Access: `None` (Public Access)

- Validation Rules:
  - Project Name: String must be unique within the organization; checked during typing and on submission.
  - Repository URL: Must match a valid Git URI pattern (HTTPS or SSH); checked on field blur.
  - Target Application URL: Must be a valid URI (http/https); checked on field blur.
  - Target Host/IP: Must be a valid IPv4/IPv6 address or a valid FQDN; checked on field blur.

- Explicit Non-Actions:
  - The system must NOT clone or pull the repository during creation.
  - The system must NOT perform any technology fingerprinting or auto-discovery.
  - The system must NOT initiate any of the 11 security stages.
  - The system must NOT ask for tool-specific configuration parameters (e.g., Sonar keys).

- UX Communication Rules:
  - The page title must use "Setup" or "Identity" (e.g., "New Project Setup") to avoid confusion with scan execution.
  - The primary action button must be labeled "Save Project" or "Create Definition," never "Start Scan."
  - UI microcopy must explicitly state: "Defining this project allows you to run repeatable security scans in the future. No scan will be triggered now."
  - The final confirmation screen should present the action "Go to Project Hub" as the next logical step.
