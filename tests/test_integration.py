from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_integration_feature_2():
    # 1. Create project
    project_data = {
        "name": "Feature 2 Project",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key"
    }
    response = client.post("/api/v1/projects", json=project_data)
    assert response.status_code == 200
    project_id = response.json()["project_id"]

    # 2. Trigger scan (CREATED state)
    scan_data = {
        "project_id": project_id,
        "mode": "AUTOMATED"
    }
    response = client.post("/api/v1/scans", json=scan_data)
    assert response.status_code == 200
    scan_id = response.json()["scan_id"]
    assert response.json()["state"] == "CREATED"

    # 3. Queue scan (CREATED -> QUEUED)
    response = client.post(f"/api/v1/scans/{scan_id}/queue")
    assert response.status_code == 200
    assert response.json()["state"] == "QUEUED"

    # Verify idempotency
    response = client.post(f"/api/v1/scans/{scan_id}/queue")
    assert response.status_code == 200
    assert response.json()["state"] == "QUEUED"

    # Peek into DB for verification
    from app.api.scans import scans_db
    scan_obj = scans_db[scan_id]
    assert scan_obj.payload_checksum is not None
    callback_token = scan_obj.callback_token

    # 4. Simulate Handshake (QUEUED -> RUNNING via polling)
    from app.services.jenkins_service import jenkins_service
    from app.services.scan_monitor import monitor_scans

    jenkins_service.set_mock_status(scan_id, building=True)
    monitor_scans(scans_db)

    # Check state
    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.json()["state"] == "RUNNING"

    # 5. Manual Mode Validation
    manual_scan_data = {
        "project_id": project_id,
        "mode": "MANUAL",
        "selected_stages": ["Git Checkout", "Sonar Scanner"]
    }
    response = client.post("/api/v1/scans", json=manual_scan_data)
    m_scan_id = response.json()["scan_id"]

    response = client.post(f"/api/v1/scans/{m_scan_id}/queue")
    assert response.status_code == 200

    # Verify manual payload structure (simulation check)
    from app.core.handshake import build_jenkins_payload
    from app.api.projects import projects_db
    m_payload = build_jenkins_payload(scans_db[m_scan_id], projects_db[project_id])
    assert m_payload["requested_stages"] == [1, 2]
    assert m_payload["scan_mode"] == "MANUAL"

if __name__ == "__main__":
    pytest.main([__file__])
