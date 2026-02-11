import json
import hashlib
from app.models.scan import Scan

STAGE_MAP = {
    'Git Checkout': 1,
    'Sonar Scanner': 2,
    'Sonar Quality Gate': 3,
    'NPM / PIP Install': 4,
    'Dependency Check': 5,
    'Trivy FS Scan': 6,
    'Docker Build': 7,
    'Docker Push': 8,
    'Trivy Image Scan': 9,
    'Nmap Scan': 10,
    'ZAP Scan': 11
}

def build_jenkins_payload(scan: Scan, project_data: dict) -> dict:
    """
    Constructs the immutable handshake payload for Jenkins as per Feature 2 spec.
    """
    requested_stages = None
    if scan.mode == 'MANUAL' and scan.selected_stages:
        requested_stages = [STAGE_MAP[s] for s in scan.selected_stages if s in STAGE_MAP]

    payload = {
        "scan_id": scan.scan_id,
        "callback_token": scan.callback_token, # Security requirement
        "project_id": project_data.get("project_id"),
        "scan_mode": scan.mode,
        "requested_stages": requested_stages,
        "inputs": {
            "target_ip": project_data.get("target_ip", ""),
            "target_url": project_data.get("target_url", "")
        },
        "git": {
            "repo_url": project_data.get("git_url", ""),
            "branch": project_data.get("branch", ""),
            "credentials_id": project_data.get("credentials_id", "") # Required for execution
        },
        "sonar": {
            "sonar_key": project_data.get("sonar_key", "")
        }
    }
    return payload

def calculate_checksum(payload: dict) -> str:
    """
    Calculates SHA-256 checksum of the payload.
    """
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()
