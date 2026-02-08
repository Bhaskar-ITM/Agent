- In-Progress View: A horizontal timeline representing functional scan phases (Preparation, Analysis, Infrastructure, Reporting) with a global progress bar. A live status label provides human-readable context such as "Scanning application for common web vulnerabilities..." or "Verifying code quality against security standards."

- Component Status Representation:
  - Active: A pulsing blue indicator labeled "Running..."
  - Success: A green checkmark labeled "Analysis Complete."
  - Skipped: A subtle gray icon labeled "Optimized" or "Not Applicable."
  - Failed: A red alert icon labeled "Needs Attention."

- Results Summary View: A high-level executive dashboard featuring a severity count breakdown (Critical, High, Medium, Low), a "Security Health" status, and a prioritized list of the top 3 critical findings that require immediate remediation. A summary of "Assessed Areas" indicates which functional domains (e.g., Code, Container, Network) were covered.

- Status Communication Rules:
  - PASS: Communicated as "Healthy" or "No High Risks Found."
  - FAIL: Communicated as "Vulnerabilities Identified" or "Security Gaps Found."
  - WARNING: Communicated as "Action Recommended" or "Minor Issues Detected."
  - SKIPPED: Communicated as "Not Applicable for this Tech Stack" or "Excluded by Configuration."

- Report & Artifact Access Rules: Detailed vulnerability reports are available for download only after the scan reaches a terminal state. Technical evidence and scan artifacts are hidden behind a "Technical Evidence" toggle to prevent overwhelming the user, and no direct access to underlying CI/CD build environments is permitted.

- Forbidden Information: Raw Jenkins logs, terminal command strings (e.g., shell scripts or tool CLI parameters), Kali Linux agent system paths, and internal pipeline trace data.
