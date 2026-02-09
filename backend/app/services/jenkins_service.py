import logging
from app.models.scan import Scan

logger = logging.getLogger(__name__)

class JenkinsService:
    def __init__(self):
        self.should_fail = False

    def trigger_scan_job(self, scan: Scan, project_data: dict):
        """
        Simulates triggering a Jenkins job.
        In production, this would use the Jenkins REST API.
        """
        import json
        if self.should_fail:
            logger.error(f"Simulating Jenkins trigger failure for scan {scan.scan_id}")
            return False

        # Convert project_data keys to camelCase for Jenkinsfile compatibility
        # If it's already a dict from a Pydantic model with aliases, this might be redundant
        # but let's be explicit.

        payload = {
            "SCAN_ID": scan.scan_id,
            "MODE": scan.mode,
            "PROJECT_DATA": json.dumps({
                "project_id": project_data.get("project_id"),
                "name": project_data.get("name"),
                "git_url": project_data.get("git_url"),
                "branch": project_data.get("branch"),
                "credentials_id": project_data.get("credentials_id"),
                "sonar_key": project_data.get("sonar_key"),
                "target_ip": project_data.get("target_ip"),
                "target_url": project_data.get("target_url")
            }),
            "SELECTED_STAGES": json.dumps(scan.selected_stages)
        }

        # Simulate a successful handshake
        logger.info(f"Triggering Jenkins job for scan {scan.scan_id} with payload: {payload}")

        # In a real scenario, this would return the Jenkins build number or a success boolean
        return True

jenkins_service = JenkinsService()
