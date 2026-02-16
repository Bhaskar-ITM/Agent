from fastapi.testclient import TestClient

from app.main import app
from app.api.projects import projects_db
from app.api.scans import scans_db


client = TestClient(app)


def setup_function():
    projects_db.clear()
    scans_db.clear()


def test_callback_syncs_project_last_scan_state_on_success():
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "State Sync Project",
            "git_url": "https://github.com/acme/repo.git",
            "branch": "main",
            "credentials_id": "cred-1",
            "sonar_key": "sonar-1",
        },
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["project_id"]

    scan_response = client.post(
        "/api/v1/scans",
        json={
            "project_id": project_id,
            "scan_mode": "AUTOMATED",
            "selected_stages": ["SAST"],
        },
    )
    assert scan_response.status_code == 201
    scan_id = scan_response.json()["scan_id"]

    callback_response = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json={"status": "SUCCESS", "stages": []},
    )

    assert callback_response.status_code == 200
    assert scans_db[scan_id].state == "COMPLETED"
    assert projects_db[project_id]["last_scan_state"] == "COMPLETED"


def test_callback_syncs_project_last_scan_state_on_failure():
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "State Sync Project",
            "git_url": "https://github.com/acme/repo.git",
            "branch": "main",
            "credentials_id": "cred-1",
            "sonar_key": "sonar-1",
        },
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["project_id"]

    scan_response = client.post(
        "/api/v1/scans",
        json={
            "project_id": project_id,
            "scan_mode": "AUTOMATED",
            "selected_stages": ["SAST"],
        },
    )
    assert scan_response.status_code == 201
    scan_id = scan_response.json()["scan_id"]

    callback_response = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json={"status": "FAILURE", "stages": []},
    )

    assert callback_response.status_code == 200
    assert scans_db[scan_id].state == "FAILED"
    assert projects_db[project_id]["last_scan_state"] == "FAILED"
