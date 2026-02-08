- Scan States:
  - CREATED: The scan record exists in the backend but has not yet been submitted to the execution engine.
  - QUEUED: The scan has been acknowledged by the backend and is waiting for a Jenkins slot or system resources.
  - RUNNING: Jenkins has started the pipeline execution on the Kali Linux agent.
  - COMPLETED: The pipeline finished all intended stages successfully and results have been ingested.
  - FAILED: The pipeline or a critical stage failed to execute, or a system error occurred.
  - CANCELLED: The user or system explicitly aborted the scan before it reached a natural conclusion.

- Valid State Transitions:
  - CREATED -> QUEUED
  - QUEUED -> RUNNING
  - QUEUED -> CANCELLED
  - RUNNING -> COMPLETED
  - RUNNING -> FAILED
  - RUNNING -> CANCELLED

- State Transition Ownership:
  - CREATED -> QUEUED: Owned by the Backend (triggered immediately after validation).
  - QUEUED -> RUNNING: Owned by the Backend (upon receiving a "job started" callback or polling success from Jenkins).
  - QUEUED/RUNNING -> CANCELLED: Triggered by the UI (user intent), enforced by the Backend (sending kill signal to Jenkins).
  - RUNNING -> COMPLETED/FAILED: Triggered by Jenkins (pipeline terminal state), enforced by the Backend (result verification and state update).

- Failure Representation:
  - A FAILED state is terminal. The backend must store a high-level `failure_reason` (e.g., TOOL_TIMEOUT, AGENT_UNAVAILABLE, PIPELINE_CRASH) to inform the user without exposing raw logs.

- Cancellation Handling:
  - When a cancellation is requested, the backend must immediately move the state to CANCELLED and then asynchronously signal Jenkins to terminate the job. Results from a CANCELLED scan are treated as partial/unreliable and are not processed for the final report.

- Retry / Re-run Rules:
  - There is no "resume" or "retry" of an existing scan ID. Any request to re-run a scan results in a NEW scan object with a unique `scan_id`. This preserves the audit trail and ensures deterministic behavior.

- Terminal States Definition:
  - COMPLETED, FAILED, and CANCELLED are terminal states. Once a scan reaches these states, no further transitions are allowed, and its data becomes immutable.
