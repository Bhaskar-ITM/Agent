from app.infrastructure.http.client import HttpClient
from app.core.config import settings


class JenkinsClient:
    def __init__(self):
        self.client = HttpClient(
            base_url=settings.JENKINS_BASE_URL,
            default_headers={
                "Authorization": f"Bearer {settings.JENKINS_TOKEN}",
                "Content-Type": "application/json",
            },
        )

    def trigger_pipeline(self, job_name: str, parameters: dict):
        return self.client.request(
            method="POST",
            path=f"job/{job_name}/buildWithParameters",
            data=parameters,
        )

    def get_build_status(self, job_name: str, build_number: int):
        return self.client.request(
            method="GET",
            path=f"job/{job_name}/{build_number}/api/json",
        )
