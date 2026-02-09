from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_integration_naming():
    # 1. Create project with camelCase field
    project_data = {
        "name": "Integration Project",
        "gitUrl": "https://github.com/test/repo.git",
        "branch": "main",
            "credentials": "git-cred",
        "sonarKey": "sonar-key"
    }
    response = client.post("/api/projects", json=project_data)
    assert response.status_code == 200
    data = response.json()

    # Assert output is camelCase
    assert "gitUrl" in data
    assert data["gitUrl"] == "https://github.com/test/repo.git"
    assert "sonarKey" in data

    project_id = data["id"]

    # 2. Trigger scan
    scan_data = {
        "projectId": project_id,
        "mode": "AUTOMATED"
    }
    response = client.post("/api/scans", json=scan_data)
    assert response.status_code == 200
    data = response.json()

    # Assert output is camelCase
    assert "scanId" in data
    assert "projectId" in data
    assert data["projectId"] == project_id
    assert "createdAt" in data

if __name__ == "__main__":
    pytest.main([__file__])
