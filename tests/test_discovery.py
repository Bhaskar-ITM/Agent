from fastapi.testclient import TestClient
from app.main import app
from app.services.discovery_service import discovery_service
from unittest.mock import patch
import pytest

client = TestClient(app)

def test_project_discovery_during_creation():
    """
    Verifies that project creation triggers discovery and stores metadata.
    """
    project_data = {
        "name": "Discovery Test Project",
        "git_url": "https://github.com/mock/node-app",
        "branch": "main",
        "credentials_id": "cred",
        "sonar_key": "sonar"
    }

    # Mock discovery to return specific node-like metadata
    mock_metadata = {
        "project_type": "node",
        "has_dockerfile": True,
        "has_frontend": True,
        "has_backend": False,
        "dependency_type": "npm"
    }

    with patch("app.services.discovery_service.discovery_service.inspect_repository", return_value=mock_metadata):
        response = client.post("/api/v1/projects", json=project_data)

    assert response.status_code == 200
    data = response.json()
    assert data["project_type"] == "node"
    assert data["has_dockerfile"] is True
    assert data["dependency_type"] == "npm"

def test_discovery_impact_on_scan_gating():
    """
    Verifies that discovered metadata correctly influences scan gating.
    """
    # 1. Setup project with no Docker but with Dependencies (Python)
    project_data = {
        "name": "Python No Docker Project",
        "git_url": "https://github.com/mock/python-app",
        "branch": "main",
        "credentials_id": "cred",
        "sonar_key": "sonar"
    }

    mock_metadata = {
        "project_type": "python",
        "has_dockerfile": False,
        "has_frontend": False,
        "has_backend": False,
        "dependency_type": "pip"
    }

    with patch("app.services.discovery_service.discovery_service.inspect_repository", return_value=mock_metadata):
        project_resp = client.post("/api/v1/projects", json=project_data).json()

    project_id = project_resp["project_id"]

    # 2. Trigger Automated Scan
    scan_resp = client.post("/api/v1/scans", json={"project_id": project_id, "mode": "AUTOMATED"}).json()
    scan_id = scan_resp["scan_id"]

    # 3. Queue scan
    with patch("app.services.jenkins_service.jenkins_service.trigger_pipeline", return_value=True):
        client.post(f"/api/v1/scans/{scan_id}/queue")

    # 4. Verify Gating
    # Stages 7, 8, 9 (Docker related) should be DISABLED because has_dockerfile is False
    # Stage 4, 5 (Dependency related) should be ENABLED because dependency_type is pip
    scan = client.get(f"/api/v1/scans/{scan_id}").json()
    gating = scan["stage_gating"]

    assert gating["4"] == "ENABLED"  # NPM/PIP Install
    assert gating["5"] == "ENABLED"  # Dependency Check
    assert gating["7"] == "DISABLED" # Docker Build
    assert gating["8"] == "DISABLED" # Docker Push
    assert gating["9"] == "DISABLED" # Trivy Image Scan
