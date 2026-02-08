- Screen List:
  - Project Dashboard
  - Project Onboarding
  - Project Hub
  - Scan Configuration
  - Live Scan Progress
  - Vulnerability Report

- Screen Purpose (one line each):
  - Project Dashboard: Displays a high-level summary of all projects and their latest security posture.
  - Project Onboarding: Captures project repository details and target environment parameters (IPs/URLs) for first-time setup.
  - Project Hub: Serves as the central interface for a project, displaying historical scan results and the primary action to start a new scan.
  - Scan Configuration: Facilitates the selection between Automated and Manual modes and collects specific execution parameters.
  - Live Scan Progress: Provides real-time feedback on which of the 11 security stages are currently active, pending, or completed.
  - Vulnerability Report: Delivers a prioritized, normalized view of all security findings across all executed stages.

- Navigation Flow:
  - Entry: Project Dashboard.
  - Onboarding: Project Dashboard → Project Onboarding → Project Hub.
  - Execution: Project Hub → Scan Configuration → Live Scan Progress → Vulnerability Report.
  - Review: Project Hub → Vulnerability Report (Historical).

- Primary Control Screen: Project Hub, as it bridges the gap between project identity, configuration state, and the historical timeline of security assessments.

- Screens with Hidden Technical Details: All screens must remain abstracted, but Live Scan Progress and Vulnerability Report are the most critical; they must never show Jenkins console output, Kali terminal commands, or raw tool-specific log formats.
