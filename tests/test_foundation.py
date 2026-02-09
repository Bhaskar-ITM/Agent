from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "DevSecOps Control Plane is live"}

def test_create_project():
    project_data = {
        "name": "Test Project",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key"
    }
    response = client.post("/api/projects", json=project_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data
    return data["id"]

def test_trigger_automated_scan():
    project_id = test_create_project()
    scan_data = {
        "project_id": project_id,
        "mode": "AUTOMATED"
    }
    response = client.post("/api/scans", json=scan_data)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "AUTOMATED"
    # Note: State is RUNNING because Jenkins handshake succeeds immediately in mock
    assert data["state"] == "RUNNING"
    assert "scan_id" in data

def test_trigger_manual_scan_missing_stages():
    project_id = test_create_project()
    scan_data = {
        "project_id": project_id,
        "mode": "MANUAL"
    }
    response = client.post("/api/scans", json=scan_data)
    assert response.status_code == 400
    assert "Manual scan requires selected stages" in response.json()["detail"]

def test_trigger_manual_scan_missing_ip_for_nmap():
    project_id = test_create_project()
    scan_data = {
        "project_id": project_id,
        "mode": "MANUAL",
        "selected_stages": ["Nmap Scan"]
    }
    response = client.post("/api/scans", json=scan_data)
    assert response.status_code == 400
    assert "Nmap scan requires target IP" in response.json()["detail"]

def test_trigger_manual_scan_success():
    # Create project with targets
    project_data = {
        "name": "Target Project",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key",
        "target_ip": "1.2.3.4",
        "target_url": "http://example.com"
    }
    project_resp = client.post("/api/projects", json=project_data)
    project_id = project_resp.json()["id"]

    scan_data = {
        "project_id": project_id,
        "mode": "MANUAL",
        "selected_stages": ["Nmap Scan", "ZAP Scan"]
    }
    response = client.post("/api/scans", json=scan_data)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "MANUAL"
    assert "Nmap Scan" in data["selected_stages"]

if __name__ == "__main__":
    # Run tests using pytest or just call them
    pytest.main([__file__])
