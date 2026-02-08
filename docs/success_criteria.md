- User Success Definition: A user considers a scan successful when they receive a clear, unambiguous report that maps findings to specific project assets, providing them with high confidence that the scan was executed as requested (Manual) or correctly tailored to their tech stack (Automated), and that the results are actionable for remediation.

- User Failure Definition: Failure is defined by the user as a scan that completes but leaves them with more questions than answers. This includes "false negatives" where obviously relevant stages were skipped without explanation, reports that contain undecipherable technical jargon from the underlying tools (raw Kali output), or "successful" scans that yield no results on a known vulnerable codebase.

- Trust-Breaking Behaviors:
  - Silent Failures: Stages failing without notifying the user or marking the scan as 'Failed'.
  - Contextual Inaccuracy: The Automated Scan skipping critical stages (e.g., Docker scan on a project with a Dockerfile) without a visible justification.
  - Data Leaks: A user seeing scan results or project details belonging to another team or project.
  - Non-Deterministic Results: Running the exact same scan on the same code twice and getting wildly different results without any external change.

- Production-Readiness Signals:
  - Explanatory UI: The platform provides clear "Why" and "How" for every automated decision made during the pipeline.
  - Auditability: Every scan generates a permanent, tamper-proof record of what was run, by whom, and with what parameters.
  - Error Gracefulness: When a security tool fails, the platform identifies whether it's a configuration error (user-fixable) or a system error (admin-fixable) rather than crashing the pipeline.
  - Consistent Taxonomy: Vulnerabilities from different tools (Sonar, Trivy, ZAP) are normalized into a single, consistent severity and naming convention.
