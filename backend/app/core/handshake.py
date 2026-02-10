import json
from app.models.scan import Scan

def build_jenkins_payload(scan: Scan, project_data: dict) -> dict:
    """
    Constructs the immutable handshake payload for Jenkins.
    """
    return {
        "SCAN_ID": scan.scan_id,
        "CALLBACK_TOKEN": scan.callback_token,
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
