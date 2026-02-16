import logging
import requests
import os
import json
from app.models.scan import Scan

logger = logging.getLogger(__name__)

class JenkinsTriggerError(Exception):
    pass

class JenkinsService:
    def __init__(self):
        self.should_fail = False
        self._mock_status = {} # scan_id -> {"building": bool, "result": str}
        self._mock_start_times = {} # scan_id -> float

    def trigger_pipeline(self, scan: Scan, project_data: dict) -> bool:
        """
        Triggers a Jenkins job via buildWithParameters.
        """
        from app.core.handshake import build_jenkins_payload

        # Check for Mock Mode
        if os.getenv("MOCK_JENKINS", "false").lower() == "true":
            logger.info("MOCK_JENKINS is enabled. Simulating trigger for scan_id=%s", scan.scan_id)
            import time
            self._mock_status[scan.scan_id] = {"building": False, "result": None}
            self._mock_start_times[scan.scan_id] = time.time()
            return True

        # 1. Configuration from environment
        base_url = os.getenv("JENKINS_BASE_URL", "http://jenkins:8080")
        job_name = os.getenv("JENKINS_JOB_NAME", "security-pipeline")
        username = os.getenv("JENKINS_USERNAME", "admin")
        api_token = os.getenv("JENKINS_API_TOKEN", "token")

        auth = (username, api_token)
        timeout = 30

        # 2. CSRF Crumb handling
        headers = {}
        try:
            crumb_resp = requests.get(f"{base_url}/crumbIssuer/api/json", auth=auth, timeout=timeout)
            if crumb_resp.status_code == 200:
                crumb_data = crumb_resp.json()
                headers[crumb_data["crumbRequestField"]] = crumb_data["crumb"]
            elif crumb_resp.status_code == 404:
                logger.info("Jenkins crumb issuer not found, assuming CSRF disabled")
            else:
                logger.warning("Failed to fetch Jenkins crumb: %s", crumb_resp.status_code)
        except Exception as e:
            logger.warning("Error fetching Jenkins crumb: %s", e)

        # 3. Build Payload
        payload = build_jenkins_payload(scan, project_data)

        # 4. Trigger Build
        trigger_url = f"{base_url}/job/{job_name}/buildWithParameters"
        params = {"PAYLOAD": json.dumps(payload)}

        try:
            resp = requests.post(trigger_url, auth=auth, params=params, headers=headers, timeout=timeout)
            if resp.status_code in [201, 302]:
                queue_url = resp.headers.get("Location")
                logger.info("Triggered Jenkins job for scan_id=%s, queue_url=%s", scan.scan_id, queue_url)

                # Initialize mock status for polling simulation (required for lifecycle monitor)
                self._mock_status[scan.scan_id] = {"building": False, "result": None}
                return True
            else:
                logger.error("Failed to trigger Jenkins job: %s %s", resp.status_code, resp.text)
                raise JenkinsTriggerError(f"Jenkins returned {resp.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error("Request to Jenkins failed: %s", e)
            raise JenkinsTriggerError(str(e))

    def trigger_scan_job(self, scan: Scan, project_data: dict):
        """
        Legacy alias for backward compatibility during transition.
        """
        return self.trigger_pipeline(scan, project_data)

    def get_build_status(self, scan_id: str):
        """
        Simulates polling Jenkins API: /job/{job}/{build}/api/json
        Returns a dict with 'building' and 'result' fields.
        """
        if os.getenv("MOCK_JENKINS", "false").lower() == "true":
            import time
            start_time = self._mock_start_times.get(scan_id)
            if start_time:
                elapsed = time.time() - start_time
                if elapsed > 10: # After 10s, it's done
                    return {"building": False, "result": "SUCCESS"}
                elif elapsed > 2: # After 2s, it's running
                    return {"building": True, "result": None}
            return {"building": False, "result": None}

        return self._mock_status.get(scan_id, {"building": False, "result": None})

    def set_mock_status(self, scan_id: str, building: bool, result: str = None):
        """Helper for tests and simulations"""
        self._mock_status[scan_id] = {"building": building, "result": result}

jenkins_service = JenkinsService()
