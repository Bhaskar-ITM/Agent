"""
Tests for project API endpoints (B1 fix).

Tests verify that:
1. Projects with no scans return null for last_scan_state (not "NONE")
2. Projects with scans return the actual state
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.db_models import ProjectDB, ScanDB
from app.state.scan_state import ScanState


class TestProjectLastScanState:
    """Test that last_scan_state returns null for projects without scans."""

    def test_project_without_scans_returns_null_state(self, client, db_session):
        """Test that projects with no scans return null for last_scan_state"""
        # Create a project without any scans
        project = ProjectDB(
            project_id="test-project-no-scans",
            name="Project Without Scans",
            git_url="https://github.com/test/no-scans.git",
            branch="main",
            credentials_id="test-creds",
            sonar_key="test-sonar",
            status="CREATED",
            last_scan_state=None
        )
        db_session.add(project)
        db_session.commit()

        # Get the projects list
        response = client.get("/api/v1/projects")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1

        project_data = data[0]
        assert project_data['project_id'] == "test-project-no-scans"
        assert project_data['last_scan_state'] is None, \
            f"Expected null for last_scan_state, got {project_data['last_scan_state']}"
        assert project_data['last_scan_id'] is None

    def test_project_with_scans_returns_actual_state(self, client, db_session):
        """Test that projects with scans return the actual last_scan_state"""
        # Create a project
        project = ProjectDB(
            project_id="test-project-with-scans",
            name="Project With Scans",
            git_url="https://github.com/test/with-scans.git",
            branch="main",
            credentials_id="test-creds",
            sonar_key="test-sonar",
            status="CREATED",
            last_scan_state=ScanState.COMPLETED.value
        )
        db_session.add(project)

        # Create a completed scan
        scan = ScanDB(
            scan_id="completed-scan-123",
            project_id="test-project-with-scans",
            scan_mode="automated",
            selected_stages=["sonar_scanner"],
            state=ScanState.COMPLETED,
            created_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            stage_results=[],
            callback_digests=[]
        )
        db_session.add(scan)
        db_session.commit()

        # Get the projects list
        response = client.get("/api/v1/projects")
        assert response.status_code == 200

        data = response.json()
        project_data = next(p for p in data if p['project_id'] == "test-project-with-scans")

        assert project_data['last_scan_state'] == ScanState.COMPLETED.value
        assert project_data['last_scan_id'] == "completed-scan-123"

    def test_get_single_project_returns_null_state(self, client, db_session):
        """Test that getting a single project without scans returns null state"""
        # Create a project without scans
        project = ProjectDB(
            project_id="test-project-single",
            name="Single Project",
            git_url="https://github.com/test/single.git",
            branch="main",
            credentials_id="test-creds",
            sonar_key="test-sonar",
            status="CREATED",
            last_scan_state=None
        )
        db_session.add(project)
        db_session.commit()

        # Get the project
        response = client.get(f"/api/v1/projects/{project.project_id}")
        assert response.status_code == 200

        data = response.json()
        assert data['last_scan_state'] is None, \
            f"Expected null for last_scan_state, got {data['last_scan_state']}"
        assert data['last_scan_id'] is None
