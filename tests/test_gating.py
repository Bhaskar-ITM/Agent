from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_automated_gating_no_inputs():
    # 1. Create project with no IP/URL
    project_data = {
        "name": "Gating Project No Inputs",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key"
    }
    response = client.post("/api/v1/projects", json=project_data)
    project_id = response.json()["project_id"]

    # 2. Trigger scan
    scan_data = {"project_id": project_id, "mode": "AUTOMATED"}
    response = client.post("/api/v1/scans", json=scan_data)
    scan_id = response.json()["scan_id"]

    # 3. Queue scan (Trigger gating computation)
    response = client.post(f"/api/v1/scans/{scan_id}/queue")

    # 4. Verify gating (Nmap 10 and ZAP 11 should be DISABLED)
    response = client.get(f"/api/v1/scans/{scan_id}")
    gating = response.json()["stage_gating"]
    assert gating["10"] == "DISABLED"
    assert gating["11"] == "DISABLED"
    assert gating["1"] == "ENABLED"

def test_automated_gating_with_inputs():
    # 1. Create project with IP/URL
    project_data = {
        "name": "Gating Project With Inputs",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key",
        "target_ip": "1.1.1.1",
        "target_url": "https://test.com"
    }
    response = client.post("/api/v1/projects", json=project_data)
    project_id = response.json()["project_id"]

    # 2. Trigger scan
    scan_data = {"project_id": project_id, "mode": "AUTOMATED"}
    response = client.post("/api/v1/scans", json=scan_data)
    scan_id = response.json()["scan_id"]

    # 3. Queue scan
    client.post(f"/api/v1/scans/{scan_id}/queue")

    # 4. Verify gating (All enabled)
    response = client.get(f"/api/v1/scans/{scan_id}")
    gating = response.json()["stage_gating"]
    assert gating["10"] == "ENABLED"
    assert gating["11"] == "ENABLED"

def test_manual_gating():
    # 1. Create project
    project_data = {
        "name": "Gating Project Manual",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key"
    }
    response = client.post("/api/v1/projects", json=project_data)
    project_id = response.json()["project_id"]

    # 2. Trigger manual scan with specific stages [1, 5]
    scan_data = {
        "project_id": project_id,
        "mode": "MANUAL",
        "selected_stages": ["Git Checkout", "Dependency Check"]
    }
    response = client.post("/api/v1/scans", json=scan_data)
    scan_id = response.json()["scan_id"]

    # 3. Queue scan
    client.post(f"/api/v1/scans/{scan_id}/queue")

    # 4. Verify gating
    response = client.get(f"/api/v1/scans/{scan_id}")
    gating = response.json()["stage_gating"]
    assert gating["1"] == "ENABLED"
    assert gating["5"] == "ENABLED"
    assert gating["2"] == "DISABLED"
    assert gating["10"] == "DISABLED"
