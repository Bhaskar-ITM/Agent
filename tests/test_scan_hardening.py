from datetime import timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.api.projects import projects_db
from app.api.scans import scans_db
from app.state.scan_state import ScanState


client = TestClient(app)


def setup_function():
    projects_db.clear()
    scans_db.clear()


def _create_project():
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Hardening Project",
            "git_url": "https://github.com/acme/repo.git",
            "branch": "main",
            "credentials_id": "cred-1",
            "sonar_key": "sonar-1",
        },
    )
    assert response.status_code == 200
    return response.json()["project_id"]


def test_manual_dependency_validation_blocks_invalid_selection():
    project_id = _create_project()

    response = client.post(
        "/api/v1/scans",
        json={
            "project_id": project_id,
            "scan_mode": "manual",
            "selected_stages": ["trivy_image_scan"],
        },
    )

    assert response.status_code == 400
    assert "requires" in response.json()["detail"]


def test_prevent_duplicate_active_scan_for_same_project():
    project_id = _create_project()

    first = client.post(
        "/api/v1/scans",
        json={"project_id": project_id, "scan_mode": "automated"},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/scans",
        json={"project_id": project_id, "scan_mode": "automated"},
    )

    assert second.status_code == 409


def test_callback_idempotency_does_not_overwrite_terminal_state():
    project_id = _create_project()
    scan_response = client.post(
        "/api/v1/scans",
        json={"project_id": project_id, "scan_mode": "automated"},
    )
    scan_id = scan_response.json()["scan_id"]

    success_callback = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json={"status": "SUCCESS", "stages": []},
    )
    assert success_callback.status_code == 200

    replay_conflict = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json={"status": "FAILURE", "stages": []},
    )
    assert replay_conflict.status_code == 200

    scan = scans_db[scan_id]
    assert scan.state == "COMPLETED"
    assert replay_conflict.json().get("idempotent") is True


def test_callback_artifact_validation_enforces_limits():
    project_id = _create_project()
    scan_response = client.post(
        "/api/v1/scans",
        json={"project_id": project_id, "scan_mode": "automated"},
    )
    scan_id = scan_response.json()["scan_id"]

    invalid = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json={
            "status": "SUCCESS",
            "stages": [{"stage": "zap_scan", "status": "SUCCESS", "artifact_size_bytes": 999999999}],
        },
    )

    assert invalid.status_code == 400



def test_callback_rejects_invalid_stage_identifier():
    project_id = _create_project()
    scan_response = client.post(
        "/api/v1/scans",
        json={"project_id": project_id, "scan_mode": "automated"},
    )
    scan_id = scan_response.json()["scan_id"]

    invalid = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json={
            "status": "SUCCESS",
            "stages": [{"stage": "extra_stage_not_allowed", "status": "SUCCESS"}],
        },
    )

    assert invalid.status_code == 400


def test_callback_rejects_unknown_status():
    project_id = _create_project()
    scan_response = client.post(
        "/api/v1/scans",
        json={"project_id": project_id, "scan_mode": "automated"},
    )
    scan_id = scan_response.json()["scan_id"]

    invalid = client.post(
        f"/api/v1/scans/{scan_id}/callback",
        json={"status": "IN_PROGRESS", "stages": []},
    )

    assert invalid.status_code == 400


def test_running_scan_times_out_when_window_exceeded():
    project_id = _create_project()
    scan_response = client.post(
        "/api/v1/scans",
        json={"project_id": project_id, "scan_mode": "automated"},
    )
    scan_id = scan_response.json()["scan_id"]

    scan = scans_db[scan_id]
    scan.state = ScanState.RUNNING
    scan.created_at = scan.created_at - timedelta(hours=3)

    status_response = client.get(f"/api/v1/scans/{scan_id}")
    assert status_response.status_code == 200
    assert status_response.json()["state"] == "FAILED"
