- Stage Grouping:
  - Source & Environment: Git Checkout, NPM / PIP Install.
  - Code Quality: Sonar Scanner, Sonar Quality Gate.
  - Software Composition Analysis (SCA): Dependency Check, Trivy FS Scan.
  - Container Security: Docker Build, Trivy Image Scan, Docker Push.
  - Dynamic Analysis (DAST/Network): Nmap Scan, ZAP Scan.

- Execution Order & Rationale:
  1. Source & Environment: Provides the foundation for all analysis.
  2. Code Quality: Identifies structural issues early; fails fast.
  3. SCA: Analyzes third-party risks before artifacts are built.
  4. Container Security: Builds and validates artifacts only after source/SCA checks pass.
  5. Dynamic Analysis: Scans external targets/interfaces as the final validation layer.
  Rationale: This sequence moves from high-velocity/low-cost static checks to higher-cost/complex build and dynamic execution phases, ensuring efficient resource usage and early feedback.

- Hard Dependencies:
  - Git Checkout must precede all other stages.
  - NPM / PIP Install must precede Sonar Scanner and Dependency Check.
  - Sonar Scanner must precede Sonar Quality Gate.
  - Docker Build must precede Trivy Image Scan and Docker Push.

- Skippable / Independent Stages:
  - Nmap Scan and ZAP Scan can run independently of code-based stages if external targets are provided.
  - Trivy FS Scan is independent of Sonar stages.
  - In Automated mode, any stage (except Git Checkout) is skippable based on tech-stack discovery.

- Discovery Placement:
  - Discovery must occur immediately after the "Git Checkout" stage. The pipeline inspects the workspace for specific files (e.g., package.json, Dockerfile) to determine the applicability of downstream stages in Automated mode.

- Logging & Visibility Rules:
  - Each stage must log standardized lifecycle markers: `[STAGE START]`, `[STAGE SKIP]`, `[STAGE SUCCESS]`, and `[STAGE FAILURE]`.
  - Skip reasons (e.g., "Dockerfile not found") must be explicitly logged to the console output.
  - Failures in non-critical stages should be clearly marked as "Unstable" rather than "Failed" if they do not block the overall pipeline.

- Maintainability Guidelines:
  - Stage-Specific Logic: Encapsulate the logic for each of the 11 stages into discrete, modular blocks or functions.
  - Contract Adherence: Strictly use parameters passed by the backend as defined in the Jenkins Job Contract.
  - Descriptive Steps: Use the `description` field in Jenkins stages to provide high-level context for each action.
