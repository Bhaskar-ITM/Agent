import logging
from app.models.scan import Scan

logger = logging.getLogger(__name__)

class JenkinsService:
    def __init__(self):
        self.should_fail = False
        self._mock_status = {} # scan_id -> {"building": bool, "result": str}

    def trigger_scan_job(self, scan: Scan, project_data: dict):
        """
        Simulates triggering a Jenkins job.
        In production, this would use the Jenkins REST API.
        """
        from app.core.handshake import build_jenkins_payload

        if self.should_fail:
            logger.error(f"Simulating Jenkins trigger failure for scan {scan.scan_id}")
            return False

        payload = build_jenkins_payload(scan, project_data)

        # Simulate a successful handshake
        logger.info(f"Triggering Jenkins job for scan {scan.scan_id} with payload: {payload}")

        # In a real scenario, this would return the Jenkins build number or a success boolean

        # Initialize mock status for polling simulation
        self._mock_status[scan.scan_id] = {"building": False, "result": None}

        return True

    def get_build_status(self, scan_id: str):
        """
        Simulates polling Jenkins API: /job/{job}/{build}/api/json
        Returns a dict with 'building' and 'result' fields.
        """
        return self._mock_status.get(scan_id, {"building": False, "result": None})

    def set_mock_status(self, scan_id: str, building: bool, result: str = None):
        """Helper for tests and simulations"""
        self._mock_status[scan_id] = {"building": building, "result": result}

jenkins_service = JenkinsService()
