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

    # 3. Get Status
    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 200
    assert response.json()["state"] == "RUNNING" # scan_orchestrator moves to RUNNING on success

    # 4. Get Results
    response = client.get(f"/api/v1/scans/{scan_id}/results")
    assert response.status_code == 200
    assert "results" in response.json()

if __name__ == "__main__":
    pytest.main([__file__])
