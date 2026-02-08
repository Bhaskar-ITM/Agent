- User Interpretation: An advanced user interprets Manual Scan as a surgical tool for precise security testing. Their mental model is that of a 1:1 deterministic engine where they have absolute control over the scope and sequence, allowing them to isolate specific vulnerabilities or test individual assets without triggering unrelated stages.

- Risks of Extra Execution: Secretly running additional stages destroys the predictability of the platform. It can lead to unintended network traffic that triggers intrusion detection system (IDS) alerts, violates "Rules of Engagement" in sensitive environments, and causes significant resource waste by executing heavy scans (like ZAP) that the user intended to skip.

- Risks of Missing Inputs: Missing or incorrect inputs (e.g., a malformed URL for ZAP or an incorrect CIDR range for Nmap) result in either immediate pipeline failure or, more dangerously, the targeting of unintended assets. This leads to wasted engineering hours and potential legal/compliance risks if unauthorized systems are scanned due to a lack of strict input enforcement.

- Non-Negotiable Rules:
  1. Strict Selection: Only stages explicitly checked by the user are allowed to run; no implicit dependencies or "helper" stages can be added.
  2. Parameter Mandatory: Any stage selected by the user that requires specific inputs must have those inputs validated before the pipeline initiates.
  3. Zero Discovery: No auto-discovery or technology fingerprinting shall occur in Manual mode; the system must rely entirely on user-provided data.
  4. Transparent Inactivity: Stages not selected must be clearly marked as "User Excluded" in the final audit log, not simply omitted.
