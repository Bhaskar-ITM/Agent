from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_integration_v1():
    # 1. Create project with snake_case
    project_data = {
        "name": "Integration Project",
        "git_url": "https://github.com/test/repo.git",
        "branch": "main",
        "credentials_id": "git-cred",
        "sonar_key": "sonar-key"
    }
    response = client.post("/api/v1/projects", json=project_data)
    assert response.status_code == 200
    data = response.json()

    # Assert output matches spec
    assert "project_id" in data
    assert data["status"] == "CREATED"

    project_id = data["project_id"]

    # 2. Trigger scan
    scan_data = {
        "project_id": project_id,
        "mode": "AUTOMATED"
    }
    response = client.post("/api/v1/scans", json=scan_data)
    assert response.status_code == 200
    data = response.json()

    # Assert output matches spec
    assert "scan_id" in data
    assert data["state"] in ["QUEUED", "RUNNING"]

    scan_id = data["scan_id"]

    # Peek into DB to get callback token for simulation
    from app.api.scans import scans_db
    callback_token = scans_db[scan_id].callback_token

    # 3. Get Status - Should be QUEUED (Queue-Only pattern)
    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 200
    assert response.json()["state"] == "QUEUED"

    # 4. Simulate STARTED Handshake from Jenkins
    response = client.post(
        f"/api/v1/scans/{scan_id}/started",
        headers={"X-Callback-Token": callback_token}
    )
    assert response.status_code == 200

    # 5. Check state again - Should be RUNNING
    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.json()["state"] == "RUNNING"

    # 6. Get Results
    response = client.get(f"/api/v1/scans/{scan_id}/results")
    assert response.status_code == 200
    assert "results" in response.json()

    # 7. Callback SUCCESS
    report = {
        "status": "SUCCESS",
        "stages": [{"name": "Git Checkout", "status": "PASSED"}]
    }
    response = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json=report,
        headers={"X-Callback-Token": callback_token}
    )
    assert response.status_code == 200

    # 8. Verify final state
    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.json()["state"] == "COMPLETED"

    # 9. Verify invalid token rejection
    response = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json=report,
        headers={"X-Callback-Token": "wrong-token"}
    )
    assert response.status_code == 403

if __name__ == "__main__":
    pytest.main([__file__])
