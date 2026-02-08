- Backend Responsibilities:
  - Project Lifecycle Management: Managing repository links, access credentials, and target definitions.
  - Scan State Orchestration: Tracking the lifecycle of a scan (Created, Queued, Running, Terminal) and persisting this state.
  - Jenkins Interaction: Mapping scan requests to Jenkins job triggers and passing necessary parameters.
  - Results Normalization: Aggregating diverse tool outputs from Jenkins/Kali into a unified vulnerability schema.
  - Logic for Automated Applicability: Determining which of the 11 stages should run in Automated mode based on project metadata.

- Backend Non-Responsibilities:
  - Security Tool Execution: The backend never runs Nmap, ZAP, or other tools directly.
  - Pipeline Step Definition: The internal sequence and implementation of the 11 stages live in the Jenkinsfile, not the backend.
  - Real-time UI Presentation: The backend provides state data but does not handle UI logic or rendering.
  - Agent Configuration: Management of the Kali Linux environment and tool versions is an infrastructure/Jenkins concern.

- Source of Truth:
  - Project & Configuration Data: The Backend Database is authoritative for user-provided settings and historical results.
  - Execution Status: Jenkins is the authoritative source for whether a job is currently active or completed.
  - Tool Artifacts: Raw reports and logs are owned by Jenkins/Kali until the backend successfully ingests and normalizes them.

- Intent Interpretation Rules:
  - Manual Mode: Backend transmits a literal "inclusion list" of stages selected by the user; Jenkins must strictly follow this list.
  - Automated Mode: Backend evaluates the project definition (e.g., presence of URLs or Docker configurations) to generate a "recommended inclusion list" before triggering Jenkins.

- Validation vs Execution Boundary:
  - Validation (Backend): Must perform all security and format checks (e.g., IP range restrictions, URL validatity, credential validation) before initiating any external execution.
  - Execution (Jenkins): Responsible for the reliable sequential execution of validated instructions and the collection of raw tool data.

- Architecture Pitfalls:
  - Tool-Specific Leakage: Hardcoding stage-specific logic (e.g., Nmap command flags) in the backend instead of the pipeline layer.
  - Blocking Job Initiation: Designing the backend to wait synchronously for scan completion, leading to timeout issues and poor scalability.
  - State Fragmentation: Allowing the UI to poll Jenkins directly, bypassing the backend and creating inconsistent views of the scan state.
