- User Understanding: The user views "Automated Scan" as an "autopilot" or "smart assistant" that removes the need for technical security expertise. They expect a "hands-off" experience where the platform takes full responsibility for identifying the project's tech stack and applying the correct set of the 11 predefined security tools.

- Hidden Assumptions: Users often assume that "Automated" equals "Complete," believing that the system will find 100% of vulnerabilities relevant to their project. They also assume the detection logic is infallible—if a scan completes without NPM or Docker checks, they assume their project doesn't have those components, rather than considering a detection failure.

- Trust Risks: Trust is broken if the system's "applicability" logic fails silently (e.g., failing to detect a `package.json` and skipping NPM Install/Dependency Check). When users find vulnerabilities later that should have been caught by a skipped stage, the "Automated" feature is perceived as a "Simplified" or "Partial" scan rather than a "Smart" one.

- Recommended Wording: "Automated Scan: Automatically detects your project's technology stack and executes all relevant security stages. To ensure efficiency, the system intelligently skips stages that do not apply to your specific project configuration."
