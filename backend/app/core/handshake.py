import json
import hashlib
from app.models.scan import Scan

# Feature 3: Centralized Security Stages Registry
SECURITY_STAGES = {
    1: {"name": "Git Checkout", "requires": []},
    2: {"name": "Sonar Scanner", "requires": []},
    3: {"name": "Sonar Quality Gate", "requires": []},
    4: {"name": "NPM / PIP Install", "requires": ["dependency_type"]},
    5: {"name": "Dependency Check", "requires": ["dependency_type"]},
    6: {"name": "Trivy FS Scan", "requires": []},
    7: {"name": "Docker Build", "requires": ["has_dockerfile"]},
    8: {"name": "Docker Push", "requires": ["has_dockerfile"]},
    9: {"name": "Trivy Image Scan", "requires": ["has_dockerfile"]},
    10: {"name": "Nmap Scan", "requires": ["target_ip"]},
    11: {"name": "ZAP Scan", "requires": ["target_url"]}
}

# Mapping names to indices for backward compatibility/lookup
STAGE_NAME_TO_ID = {v["name"]: k for k, v in SECURITY_STAGES.items()}

def compute_stage_gating(scan: Scan, project_data: dict) -> dict:
    """
    Feature 3: Centralized gating logic.
    Backend is the single source of truth.
    """
    gating = {}

    if scan.mode == "AUTOMATED":
        for stage_id, meta in SECURITY_STAGES.items():
            required = meta["requires"]
            # Check if all required inputs are present in project_data and not empty
            if any(not project_data.get(req) for req in required):
                gating[str(stage_id)] = "DISABLED"
            else:
                gating[str(stage_id)] = "ENABLED"

    elif scan.mode == "MANUAL":
        # Feature 1 & 2 ensured requested_stages contains valid names
        requested_ids = [STAGE_NAME_TO_ID[name] for name in scan.selected_stages if name in STAGE_NAME_TO_ID]
        for stage_id in SECURITY_STAGES.keys():
            gating[str(stage_id)] = (
                "ENABLED"
                if stage_id in requested_ids
                else "DISABLED"
            )

    return gating

def build_jenkins_payload(scan: Scan, project_data: dict) -> dict:
    """
    Constructs the immutable handshake payload for Jenkins as per Feature 2 & 3 spec.
    """
    requested_stages = None
    if scan.mode == 'MANUAL' and scan.selected_stages:
        requested_stages = [STAGE_NAME_TO_ID[s] for s in scan.selected_stages if s in STAGE_NAME_TO_ID]

    # Compute gating for Feature 3
    gating = compute_stage_gating(scan, project_data)

    payload = {
        "scan_id": scan.scan_id,
        "callback_token": scan.callback_token,
        "project_id": project_data.get("project_id"),
        "scan_mode": scan.mode,
        "requested_stages": requested_stages,
        "stage_gating": gating, # Feature 3
        "inputs": {
            "target_ip": project_data.get("target_ip", ""),
            "target_url": project_data.get("target_url", "")
        },
        "git": {
            "repo_url": project_data.get("git_url", ""),
            "branch": project_data.get("branch", ""),
            "credentials_id": project_data.get("credentials_id", "")
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
