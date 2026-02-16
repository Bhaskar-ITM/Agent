from fastapi.testclient import TestClient
from app.main import app
from app.api.scans import scans_db
from app.services.jenkins_service import jenkins_service
from app.services.scan_monitor import monitor_scans
import pytest
import json

client = TestClient(app)

def test_infrastructure_sanity():
    # Verify Backend API reachability
    response = client.get("/")
    assert response.status_code == 200
    assert "live" in response.json()["message"]

def test_full_automated_scan_validation():
    """
    Validates the entire execution chain for an automated scan.
    """
    # 1. Setup Project
    project_data = {
        "name": "Integration Automated",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key",
        "target_ip": "10.0.0.1",
        "target_url": "https://test.com"
    }
    resp = client.post("/api/v1/projects", json=project_data)
    project_id = resp.json()["project_id"]

    # 2. Trigger Scan Intent
    resp = client.post("/api/v1/scans", json={"project_id": project_id, "mode": "AUTOMATED"})
    scan_id = resp.json()["scan_id"]
    assert resp.json()["state"] == "CREATED"

    # 3. Queue Scan (Handshake start)
    resp = client.post(f"/api/v1/scans/{scan_id}/queue")
    assert resp.status_code == 200
    assert scans_db[scan_id].state == "QUEUED"
    token = scans_db[scan_id].callback_token

    # 4. Simulate Jenkins Started (Polling)
    jenkins_service.set_mock_status(scan_id, building=True)
    monitor_scans(scans_db)
    assert scans_db[scan_id].state == "RUNNING"

    # 5. Simulate Stage Results (Callbacks)
    # Stage 1: PASSED
    client.post(f"/api/v1/scans/{scan_id}/started", headers={"X-Callback-Token": token})

    stages_report = [
        {"stage": "Git Checkout", "status": "PASSED", "summary": "Code checked out"},
        {
            "stage": "Dependency Check",
            "status": "PASSED",
            "summary": "Vulnerabilities found",
            "findings": {"critical": 0, "high": 2, "medium": 5, "low": 10},
            "artifacts": ["report.html"]
        }
    ]

    # Final Callback (as per Jenkinsfile post block)
    report = {
        "scanId": scan_id,
        "status": "SUCCESS",
        "stages": stages_report
    }
    client.post(f"/api/v1/scans/{scan_id}/callback", json=report, headers={"X-Callback-Token": token})

    # 6. Final Terminal State Detection (Polling)
    jenkins_service.set_mock_status(scan_id, building=False, result="SUCCESS")
    monitor_scans(scans_db)

    # 7. Verification
    scan = scans_db[scan_id]
    assert scan.state == "COMPLETED"
    assert len(scan.stage_results) == 2
    assert scan.stage_results[1]["findings"]["high"] == 2
    assert "report.html" in scan.stage_results[1]["artifacts"]

def test_manual_scan_gating_validation():
    """
    Validates manual scan gating and skipping.
    """
    project_data = {
        "name": "Integration Manual Valid",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key",
        "target_ip": "1.1.1.1" # Required for Nmap
    }
    pid = client.post("/api/v1/projects", json=project_data).json()["project_id"]

    # Select only 1, 6, 10
    selected = ["Git Checkout", "Trivy FS Scan", "Nmap Scan"]
    resp = client.post("/api/v1/scans", json={"project_id": pid, "mode": "MANUAL", "selected_stages": selected})
    assert resp.status_code == 200
    sid = resp.json()["scan_id"]

    client.post(f"/api/v1/scans/{sid}/queue")
    gating = scans_db[sid].stage_gating

    assert gating["1"] == "ENABLED"
    assert gating["6"] == "ENABLED"
    assert gating["10"] == "ENABLED"
    assert gating["2"] == "DISABLED" # Sonar Scanner
    assert gating["11"] == "DISABLED" # ZAP

def test_failure_simulations():
    """
    Validates system behavior under failure conditions.
    """
    project_data = {"name": "Integration Failure", "git_url": "x", "branch": "x", "credentials_id": "x", "sonar_key": "x"}
    pid = client.post("/api/v1/projects", json=project_data).json()["project_id"]

    # Case A: Tool FAIL status
    sid_a = client.post("/api/v1/scans", json={"project_id": pid, "mode": "AUTOMATED"}).json()["scan_id"]
    client.post(f"/api/v1/scans/{sid_a}/queue")
    token_a = scans_db[sid_a].callback_token

    # QUEUED -> RUNNING
    jenkins_service.set_mock_status(sid_a, building=True)
    monitor_scans(scans_db)

    # Report a FAIL in one stage
    report_a = {
        "status": "FAILURE",
        "stages": [{"stage": "Git Checkout", "status": "FAIL", "summary": "Repo not found"}]
    }
    client.post(f"/api/v1/scans/{sid_a}/callback", json=report_a, headers={"X-Callback-Token": token_a})

    # Monitor detects Jenkins Failure (RUNNING -> FAILED)
    jenkins_service.set_mock_status(sid_a, building=False, result="FAILURE")
    monitor_scans(scans_db)

    assert scans_db[sid_a].state == "FAILED"
    assert scans_db[sid_a].stage_results[0]["status"] == "FAIL"

    # Case C: Jenkins Aborted Mid-Pipeline
    sid_c = client.post("/api/v1/scans", json={"project_id": pid, "mode": "AUTOMATED"}).json()["scan_id"]
    client.post(f"/api/v1/scans/{sid_c}/queue")

    # QUEUED -> RUNNING
    jenkins_service.set_mock_status(sid_c, building=True)
    monitor_scans(scans_db)

    # Polling detects ABORTED
    jenkins_service.set_mock_status(sid_c, building=False, result="ABORTED")
    monitor_scans(scans_db)

    assert scans_db[sid_c].state == "FAILED"

def test_result_semantics_validation():
    """
    Validates that WARN and SKIPPED do not fail the scan.
    """
    project_data = {"name": "Integration Semantics", "git_url": "x", "branch": "x", "credentials_id": "x", "sonar_key": "x"}
    pid = client.post("/api/v1/projects", json=project_data).json()["project_id"]
    sid = client.post("/api/v1/scans", json={"project_id": pid, "mode": "AUTOMATED"}).json()["scan_id"]
    client.post(f"/api/v1/scans/{sid}/queue")
    token = scans_db[sid].callback_token

    # QUEUED -> RUNNING
    jenkins_service.set_mock_status(sid, building=True)
    monitor_scans(scans_db)

    report = {
        "status": "SUCCESS",
        "stages": [
            {"stage": "Sonar Scanner", "status": "WARN", "summary": "Quality gate warnings"},
            {"stage": "Nmap Scan", "status": "SKIPPED", "summary": "No IP"}
        ]
    }
    client.post(f"/api/v1/scans/{sid}/callback", json=report, headers={"X-Callback-Token": token})

    jenkins_service.set_mock_status(sid, building=False, result="SUCCESS")
    monitor_scans(scans_db)

    assert scans_db[sid].state == "COMPLETED"
    assert scans_db[sid].stage_results[0]["status"] == "WARN"
    assert scans_db[sid].stage_results[1]["status"] == "SKIPPED"
