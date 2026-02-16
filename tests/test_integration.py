from fastapi.testclient import TestClient
from app.main import app
import pytest
from unittest.mock import patch
from app.api.projects import projects_db
from app.api.scans import scans_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_in_memory_stores():
    projects_db.clear()
    scans_db.clear()
    yield
    projects_db.clear()
    scans_db.clear()


@patch("app.infrastructure.jenkins.jenkins_client.JenkinsClient.trigger_pipeline")
def test_integration_v1(mock_trigger):
    mock_trigger.return_value = {"status": "queued"}
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
        "scan_mode": "AUTOMATED"
    }
    response = client.post("/api/v1/scans", json=scan_data)
    assert response.status_code == 201
    data = response.json()

    # Assert output matches spec
    assert "scan_id" in data
    assert data["state"] == "CREATED"

    scan_id = data["scan_id"]

    # 3. Get Status
    response = client.get(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 200
    assert response.json()["state"] == "CREATED"

    # 4. Get Results
    response = client.get(f"/api/v1/scans/{scan_id}/results")
    assert response.status_code == 200
    assert "results" in response.json()


@pytest.mark.parametrize(
    "callback_status,expected_terminal_state",
    [
        ("SUCCESS", "COMPLETED"),
        ("FAILURE", "FAILED"),
        ("ABORTED", "FAILED"),
        ("UNSTABLE", "FAILED"),
    ],
)
def test_scan_callback_updates_project_and_scan_terminal_states(
    callback_status, expected_terminal_state
):
    # 1. Create a project
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": f"Project {callback_status}",
            "git_url": "https://github.com/test/repo.git",
            "branch": "main",
            "credentials_id": "git-cred",
            "sonar_key": "sonar-key",
        },
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["project_id"]

    # 2. Trigger a scan for the project
    scan_response = client.post(
        "/api/v1/scans",
        json={"project_id": project_id, "scan_mode": "AUTOMATED"},
    )
    assert scan_response.status_code == 201
    scan_id = scan_response.json()["scan_id"]

    # 3. Post callback with terminal Jenkins status
    callback_response = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json={
            "status": callback_status,
            "stages": [
                {
                    "stage": "SAST",
                    "status": "PASSED" if callback_status == "SUCCESS" else "FAILED",
                    "summary": "deterministic test callback",
                }
            ],
            "finishedAt": "2025-01-01T00:00:00Z",
        },
    )
    assert callback_response.status_code == 200

    # 4. Verify project listing reflects terminal state for this project
    projects_response = client.get("/api/v1/projects")
    assert projects_response.status_code == 200
    projects = projects_response.json()
    matching_project = next(p for p in projects if p["project_id"] == project_id)
    assert matching_project["last_scan_state"] == expected_terminal_state

    # 5. Verify scan details endpoint reflects terminal state
    scan_state_response = client.get(f"/api/v1/scans/{scan_id}")
    assert scan_state_response.status_code == 200
    assert scan_state_response.json()["state"] == expected_terminal_state


if __name__ == "__main__":
    pytest.main([__file__])
