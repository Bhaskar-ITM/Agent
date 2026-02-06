Default User:
- Background: Software developer or QA engineer with basic security awareness.
- Goal: Quickly identify and remediate common vulnerabilities in their application.
- Cares About: Actionable insights, easy-to-understand severity levels, and automated "one-click" scanning.
- Must Not See: Raw Jenkins pipeline DSL, Kali Linux terminal sessions, or complex regular expression configurations for scanners.

Advanced User:
- Background: Security specialist or Penetration Tester familiar with the Kali Linux ecosystem and CI/CD automation.
- Goal: Conduct exhaustive security assessments and customize scan payloads for specific targets.
- Cares About: Granular control over tool parameters, access to raw scan artifacts (e.g., PCAP files), and API access for scripting.
- Must Not See: Hardcoded "wizards" that restrict choice, simplified "health scores" that hide technical details, or UI-only workflows that cannot be automated.

Platform Admin:
- Background: DevOps or System Administrator responsible for maintaining the infrastructure and platform availability.
- Goal: Maintain the stability, scalability, and security of the scanning platform itself.
- Cares About: System resource metrics (CPU/RAM/Disk), Jenkins node health, user management, and audit trails.
- Must Not See: Specific vulnerability details within user reports (Separation of Duties), or manual security testing tools (Kali tools) that are not relevant to platform maintenance.
