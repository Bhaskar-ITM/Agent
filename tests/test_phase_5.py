from fastapi.testclient import TestClient
from app.main import app
from app.api.scans import scans_db
from app.services.jenkins_service import jenkins_service
from app.services.scan_monitor import monitor_scans
import pytest

client = TestClient(app)

def test_phase_5_lifecycle_polling():
    # 1. Setup: Create and Queue a scan
    project_data = {
        "name": "Phase 5 Project",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key"
    }
    resp = client.post("/api/v1/projects", json=project_data)
    project_id = resp.json()["project_id"]

    resp = client.post("/api/v1/scans", json={"project_id": project_id, "mode": "AUTOMATED"})
    scan_id = resp.json()["scan_id"]
    client.post(f"/api/v1/scans/{scan_id}/queue")

    # State should be QUEUED
    assert scans_db[scan_id].state == "QUEUED"

    # 2. Simulate Jenkins Starting (building=true)
    jenkins_service.set_mock_status(scan_id, building=True)

    # Run monitor manually for deterministic test
    monitor_scans(scans_db)

    # Verify transition: QUEUED -> RUNNING
    assert scans_db[scan_id].state == "RUNNING"
    assert scans_db[scan_id].started_at is not None

    # 3. Simulate Jenkins Finished (building=false, result=SUCCESS)
    jenkins_service.set_mock_status(scan_id, building=False, result="SUCCESS")
    monitor_scans(scans_db)

    # Verify transition: RUNNING -> COMPLETED
    assert scans_db[scan_id].state == "COMPLETED"
    assert scans_db[scan_id].completed_at is not None

def test_phase_5_failed_lifecycle():
    # Setup
    project_data = {"name": "Phase 5 Fail", "git_url": "x", "branch": "x", "credentials_id": "x", "sonar_key": "x"}
    pid = client.post("/api/v1/projects", json=project_data).json()["project_id"]
    sid = client.post("/api/v1/scans", json={"project_id": pid, "mode": "AUTOMATED"}).json()["scan_id"]
    client.post(f"/api/v1/scans/{sid}/queue")

    # RUNNING
    jenkins_service.set_mock_status(sid, building=True)
    monitor_scans(scans_db)

    # Simulate Jenkins Failure
    jenkins_service.set_mock_status(sid, building=False, result="FAILURE")
    monitor_scans(scans_db)

    # Verify transition: RUNNING -> FAILED
    assert scans_db[sid].state == "FAILED"

def test_phase_5_unstable_as_completed():
    # UNSTABLE should be COMPLETED as per Phase 5 mapping
    project_data = {"name": "Phase 5 Unstable", "git_url": "x", "branch": "x", "credentials_id": "x", "sonar_key": "x"}
    pid = client.post("/api/v1/projects", json=project_data).json()["project_id"]
    sid = client.post("/api/v1/scans", json={"project_id": pid, "mode": "AUTOMATED"}).json()["scan_id"]
    client.post(f"/api/v1/scans/{sid}/queue")

    jenkins_service.set_mock_status(sid, building=True)
    monitor_scans(scans_db)

    jenkins_service.set_mock_status(sid, building=False, result="UNSTABLE")
    monitor_scans(scans_db)

    assert scans_db[sid].state == "COMPLETED"
