from fastapi.testclient import TestClient
from app.main import app
from app.services.jenkins_service import jenkins_service
import pytest

client = TestClient(app)

def test_trigger_automated_scan_running():
    # 1. Create project
    project_data = {
        "name": "Jenkins Project",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key"
    }
    project_resp = client.post("/api/projects", json=project_data)
    project_id = project_resp.json()["id"]

    # 2. Trigger scan
    scan_data = {
        "project_id": project_id,
        "mode": "AUTOMATED"
    }
    response = client.post("/api/scans", json=scan_data)
    assert response.status_code == 200
    data = response.json()

    # 3. Assert state is RUNNING (meaning handshake succeeded)
    assert data["state"] == "RUNNING"
    assert "scan_id" in data

def test_trigger_manual_scan_running():
    # 1. Create project with targets
    project_data = {
        "name": "Jenkins Manual Project",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key",
        "target_ip": "1.2.3.4"
    }
    project_resp = client.post("/api/projects", json=project_data)
    project_id = project_resp.json()["id"]

    # 2. Trigger manual scan
    scan_data = {
        "project_id": project_id,
        "mode": "MANUAL",
        "selected_stages": ["Nmap Scan"]
    }
    response = client.post("/api/scans", json=scan_data)
    assert response.status_code == 200
    data = response.json()

    # 3. Assert state is RUNNING
    assert data["state"] == "RUNNING"

def test_trigger_scan_jenkins_failure():
    # 1. Create project
    project_data = {
        "name": "Failed Project",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key"
    }
    project_resp = client.post("/api/projects", json=project_data)
    project_id = project_resp.json()["id"]

    # 2. Simulate failure
    jenkins_service.should_fail = True

    # 3. Trigger scan
    try:
        response = client.post("/api/scans", json={"project_id": project_id, "mode": "AUTOMATED"})
        assert response.status_code == 500
        assert "Failed to trigger scan in Jenkins" in response.json()["detail"]
    finally:
        # Reset for other tests
        jenkins_service.should_fail = False

if __name__ == "__main__":
    pytest.main([__file__])
