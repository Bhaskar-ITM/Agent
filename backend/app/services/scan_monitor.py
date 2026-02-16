import logging
from datetime import datetime
from app.state.scan_state import ScanState
from app.services.jenkins_service import jenkins_service
from app.core.state_machine import transition, InvalidStateTransition
from app.api.projects import projects_db
import os

logger = logging.getLogger(__name__)

def monitor_scans(scans_db):
    """
    Controlled Polling logic as per Phase 5.
    Iterates through scans in QUEUED or RUNNING states and updates them based on Jenkins status.
    """
    for scan_id, scan in scans_db.items():
        if scan.state not in [ScanState.QUEUED, ScanState.RUNNING]:
            continue

        try:
            status = jenkins_service.get_build_status(scan_id)
            building = status.get("building", False)
            result = status.get("result")

            # Rule: QUEUED -> RUNNING
            if scan.state == ScanState.QUEUED and building:
                logger.info(f"Scan {scan_id} detected as RUNNING")
                transition(scan, ScanState.RUNNING)
                scan.started_at = datetime.utcnow()

                # Mock callbacks if in mock mode
                if os.getenv("MOCK_JENKINS", "false").lower() == "true":
                    scan.stage_results = [
                        {"stage": "Git Checkout", "status": "PASS", "summary": "Code successfully cloned"},
                        {"stage": "Sonar Scanner", "status": "RUNNING", "summary": "Analyzing code..."}
                    ]

            # Rule: RUNNING -> COMPLETED / FAILED
            elif scan.state == ScanState.RUNNING and not building and result is not None:
                if result in ["SUCCESS", "UNSTABLE"]:
                    logger.info(f"Scan {scan_id} detected as COMPLETED (Result: {result})")
                    transition(scan, ScanState.COMPLETED)
                    scan.completed_at = datetime.utcnow()

                    # Mock terminal results if in mock mode
                    if os.getenv("MOCK_JENKINS", "false").lower() == "true":
                        scan.stage_results = [
                            {"stage": "Git Checkout", "status": "PASS", "summary": "Code successfully cloned"},
                            {"stage": "Sonar Scanner", "status": "PASS", "summary": "Quality Gate Passed", "findings": {"critical": 0, "high": 0}},
                            {"stage": "NPM / PIP Install", "status": "PASS", "summary": "Dependencies installed"},
                            {"stage": "Dependency Check", "status": "WARN", "summary": "Found 5 medium vulnerabilities", "findings": {"medium": 5}},
                            {"stage": "Trivy FS Scan", "status": "PASS", "summary": "No vulnerabilities in FS"},
                            {"stage": "Docker Build", "status": "PASS", "summary": "Image built"},
                            {"stage": "Docker Push", "status": "PASS", "summary": "Image pushed to registry"},
                            {"stage": "Trivy Image Scan", "status": "PASS", "summary": "No vulnerabilities in image"},
                            {"stage": "Nmap Scan", "status": "PASS", "summary": "No open ports found", "findings": {"low": 1}},
                            {"stage": "ZAP Scan", "status": "PASS", "summary": "Baseline scan completed", "findings": {"medium": 2}}
                        ]
                elif result in ["FAILURE", "ABORTED"]:
                    logger.info(f"Scan {scan_id} detected as FAILED (Result: {result})")
                    transition(scan, ScanState.FAILED)
                    scan.completed_at = datetime.utcnow()

                # Update project state
                if scan.project_id in projects_db:
                    projects_db[scan.project_id]["last_scan_state"] = scan.state

            # Additional terminal detection if build stopped but result is null (unexpected)
            elif scan.state == ScanState.RUNNING and not building and result is None:
                 # In a real system we might wait a few cycles or check for crashes
                 # For now, we stay in RUNNING until a result is reported
                 pass

        except InvalidStateTransition as e:
            logger.error(f"Invalid state transition for scan {scan_id}: {e}")
        except Exception as e:
            logger.error(f"Error polling status for scan {scan_id}: {e}")
