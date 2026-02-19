import logging
from app.models.scan import Scan
from app.infrastructure.jenkins.jenkins_client import JenkinsClient
from app.core.exceptions import ExternalServiceError
from app.core.config import settings

logger = logging.getLogger(__name__)

class JenkinsService:
    def __init__(self):
        self.should_fail = False
        self.client = JenkinsClient()

    def trigger_scan_job(self, scan: Scan, project_data: dict):
        """
        Simulates triggering a Jenkins job.
        In production, this would use the Jenkins REST API.
        """
        import json
        if settings.MOCK_EXECUTION:
            logger.info(f"MOCK_EXECUTION enabled; simulating Jenkins enqueue for scan {scan.scan_id}")
            return True, None

        if self.should_fail:
            logger.error(f"Simulating Jenkins trigger failure for scan {scan.scan_id}")
            return False, None

        # Convert project_data keys to camelCase for Jenkinsfile compatibility
        # If it's already a dict from a Pydantic model with aliases, this might be redundant
        # but let's be explicit.

        payload = {
            "SCAN_ID": scan.scan_id,
            "MODE": scan.scan_mode.upper(),
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
            "SELECTED_STAGES": json.dumps(scan.selected_stages),
        }

        # Centralized outbound call via standardized JenkinsClient
        try:
            logger.info(f"Triggering Jenkins job for scan {scan.scan_id}")
            trigger_response = self.client.trigger_pipeline(
                job_name="security-pipeline",
                parameters=payload
            )
            queue_id = None
            if isinstance(trigger_response, dict):
                queue_id = trigger_response.get("queue_id") or trigger_response.get("queueId")
            return True, queue_id
        except ExternalServiceError as e:
            logger.error(f"Jenkins trigger failed: {str(e)}")
            return False, None

jenkins_service = JenkinsService()
