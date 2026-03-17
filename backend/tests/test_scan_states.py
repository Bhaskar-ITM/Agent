"""
Tests for scan state transitions (C5 fix).

Tests verify that:
1. New scans start in CREATED state, not RUNNING
2. Scans transition to RUNNING when Jenkins confirms via callback
3. Admin force-unlock endpoint works for stuck projects
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.state.scan_state import ScanState
from app.models.db_models import ScanDB, ProjectDB


class TestScanInitialState:
    """Test that new scans start in CREATED state."""
    
    def test_scan_created_not_running_initially(self, client, db_session):
        """Test that new scans start in CREATED state, not RUNNING"""
        # Create a project first
        project = ProjectDB(
            project_id="test-project-123",
            name="Test Project",
            git_url="https://github.com/test/repo.git",
            branch="main",
            credentials_id="test-creds",
            sonar_key="test-sonar",
            status="CREATED"
        )
        db_session.add(project)
        db_session.commit()
        
        # Trigger a scan
        scan_request = {
            "project_id": "test-project-123",
            "scan_mode": "automated",
            "selected_stages": None
        }
        
        response = client.post("/api/v1/scans", json=scan_request)
        
        assert response.status_code == 201
        data = response.json()
        assert data['state'] == 'CREATED', f"Expected CREATED state, got {data['state']}"
        
        # Verify in database
        scan_db = db_session.query(ScanDB).filter(ScanDB.scan_id == data['scan_id']).first()
        assert scan_db.state == ScanState.CREATED


class TestScanStateTransitions:
    """Test scan state transitions via callback."""
    
    def test_scan_transitions_to_running_on_callback(self, client, db_session):
        """Test scan transitions to RUNNING when Jenkins confirms build started"""
        # Create a project
        project = ProjectDB(
            project_id="test-project-456",
            name="Test Project 2",
            git_url="https://github.com/test/repo2.git",
            branch="main",
            credentials_id="test-creds",
            sonar_key="test-sonar",
            status="CREATED"
        )
        db_session.add(project)
        db_session.commit()
        
        # Trigger a scan (should be in CREATED state)
        scan_request = {
            "project_id": "test-project-456",
            "scan_mode": "automated",
            "selected_stages": None
        }
        
        response = client.post("/api/v1/scans", json=scan_request)
        assert response.status_code == 201
        scan_data = response.json()
        scan_id = scan_data['scan_id']
        assert scan_data['state'] == 'CREATED'
        
        # Verify project last_scan_state is CREATED
        db_session.refresh(project)
        assert project.last_scan_state == ScanState.CREATED.value
        
        # Send callback indicating Jenkins build started (RUNNING state)
        # Note: Callback currently only handles COMPLETED/FAILED
        # We need to add support for RUNNING transition
        callback_data = {
            "status": "RUNNING",
            "build_number": 123,
            "queue_id": 456,
            "stages": []
        }
        
        callback_response = client.post(
            f"/api/v1/scans/{scan_id}/callback",
            json=callback_data,
            headers={"X-Callback-Token": "test-callback-token"}
        )
        
        # Should accept RUNNING status in callback
        assert callback_response.status_code == 200
        
        # Verify scan is now in RUNNING state
        scan_db = db_session.query(ScanDB).filter(ScanDB.scan_id == scan_id).first()
        assert scan_db.state == ScanState.RUNNING
        
        # Verify project last_scan_state is updated
        db_session.refresh(project)
        assert project.last_scan_state == ScanState.RUNNING.value
    
    def test_scan_transitions_to_completed_on_success_callback(self, client, db_session):
        """Test scan transitions to COMPLETED on successful callback"""
        # Create a project
        project = ProjectDB(
            project_id="test-project-789",
            name="Test Project 3",
            git_url="https://github.com/test/repo3.git",
            branch="main",
            credentials_id="test-creds",
            sonar_key="test-sonar",
            status="CREATED"
        )
        db_session.add(project)
        db_session.commit()
        
        # Trigger a scan
        scan_request = {
            "project_id": "test-project-789",
            "scan_mode": "automated",
            "selected_stages": None
        }
        
        response = client.post("/api/v1/scans", json=scan_request)
        assert response.status_code == 201
        scan_id = response.json()['scan_id']
        
        # Send success callback
        callback_data = {
            "status": "SUCCESS",
            "build_number": 124,
            "queue_id": 457,
            "stages": [
                {
                    "name": "Sonar Scanner",
                    "status": "PASSED",
                    "summary": "Code analysis completed"
                }
            ]
        }
        
        callback_response = client.post(
            f"/api/v1/scans/{scan_id}/callback",
            json=callback_data,
            headers={"X-Callback-Token": "test-callback-token"}
        )
        
        assert callback_response.status_code == 200
        
        # Verify scan is COMPLETED
        scan_db = db_session.query(ScanDB).filter(ScanDB.scan_id == scan_id).first()
        assert scan_db.state == ScanState.COMPLETED


class TestAdminForceUnlock:
    """Test admin force-unlock endpoint for stuck projects."""
    
    def test_admin_force_unlock_stuck_scan(self, client, db_session):
        """Test that admin can force-unlock a stuck scan"""
        # Create a project
        project = ProjectDB(
            project_id="test-project-stuck",
            name="Stuck Project",
            git_url="https://github.com/test/stuck.git",
            branch="main",
            credentials_id="test-creds",
            sonar_key="test-sonar",
            status="CREATED",
            last_scan_state=ScanState.RUNNING.value  # Simulate stuck state
        )
        db_session.add(project)
        
        # Create a stuck scan in RUNNING state
        scan = ScanDB(
            scan_id="stuck-scan-123",
            project_id="test-project-stuck",
            scan_mode="automated",
            selected_stages=["sonar_scanner"],
            state=ScanState.RUNNING,
            created_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc),
            stage_results=[],
            callback_digests=[]
        )
        db_session.add(scan)
        db_session.commit()
        
        # Admin force-unlock the scan
        response = client.post(f"/api/v1/scans/{scan.scan_id}/force-unlock")
        
        # Should succeed (in test mode, auth is bypassed)
        assert response.status_code == 200
        data = response.json()
        assert "unlocked" in data['message'].lower()
        
        # Verify scan state is now FAILED
        db_session.refresh(scan)
        assert scan.state == ScanState.FAILED
        
        # Verify project last_scan_state is updated
        db_session.refresh(project)
        assert project.last_scan_state == ScanState.FAILED.value
    
    def test_admin_force_unlock_nonexistent_scan(self, client):
        """Test that force-unlock returns 404 for nonexistent scan"""
        response = client.post("/api/v1/scans/nonexistent-scan/force-unlock")
        assert response.status_code == 404
    
    def test_force_unlock_sets_error_details(self, client, db_session):
        """Test that force-unlock sets appropriate error details"""
        # Create a project
        project = ProjectDB(
            project_id="test-project-error",
            name="Error Project",
            git_url="https://github.com/test/error.git",
            branch="main",
            credentials_id="test-creds",
            sonar_key="test-sonar",
            status="CREATED"
        )
        db_session.add(project)
        
        # Create a stuck scan
        scan = ScanDB(
            scan_id="stuck-scan-456",
            project_id="test-project-error",
            scan_mode="automated",
            selected_stages=["sonar_scanner"],
            state=ScanState.RUNNING,
            created_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc),
            stage_results=[],
            callback_digests=[]
        )
        db_session.add(scan)
        db_session.commit()
        
        # Force-unlock
        response = client.post(f"/api/v1/scans/{scan.scan_id}/force-unlock")
        assert response.status_code == 200
        
        # Verify error details are set
        db_session.refresh(scan)
        assert scan.state == ScanState.FAILED
        assert scan.error_message is not None
        assert "admin" in scan.error_message.lower() or "unlocked" in scan.error_message.lower()
        assert scan.error_type == "ADMIN_RECOVERY"
