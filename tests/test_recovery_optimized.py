import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.db_models import ScanDB, ProjectDB
from app.state.scan_state import ScanState
from app.services.scan_recovery import recover_stuck_scans, poll_jenkins_for_active_scans
from app.core.db import SessionLocal, engine, Base
from app.core.config import settings

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    db = SessionLocal()
    # Clean up before tests
    db.query(ScanDB).delete()
    db.query(ProjectDB).delete()
    db.commit()
    yield db
    # Clean up after tests
    db.query(ScanDB).delete()
    db.query(ProjectDB).delete()
    db.commit()
    db.close()

def test_recover_stuck_scans_optimized(db: Session):
    # Setup: Multiple projects and stuck scans
    p1 = ProjectDB(project_id="p1", name="Project 1", last_scan_state=ScanState.RUNNING.value)
    p2 = ProjectDB(project_id="p2", name="Project 2", last_scan_state=ScanState.RUNNING.value)
    db.add_all([p1, p2])
    db.commit()

    stuck_time = datetime.now(timezone.utc) - timedelta(seconds=settings.SCAN_TIMEOUT + 10)
    s1 = ScanDB(scan_id="s1", project_id="p1", scan_mode="QUICK", state=ScanState.RUNNING, created_at=stuck_time)
    s2 = ScanDB(scan_id="s2", project_id="p2", scan_mode="QUICK", state=ScanState.RUNNING, created_at=stuck_time)
    db.add_all([s1, s2])
    db.commit()

    # Execution
    recovered = recover_stuck_scans()

    # Verification
    assert recovered == 2
    db.refresh(s1)
    db.refresh(s2)
    db.refresh(p1)
    db.refresh(p2)
    assert s1.state == ScanState.FAILED
    assert s2.state == ScanState.FAILED
    assert p1.last_scan_state == ScanState.FAILED.value
    assert p2.last_scan_state == ScanState.FAILED.value

def test_poll_jenkins_no_changes_optimized(db: Session):
    # Setup: Active scans but no Jenkins changes (mocked)
    p1 = ProjectDB(project_id="p1", name="Project 1", last_scan_state=ScanState.RUNNING.value)
    db.add(p1)
    db.commit()

    s1 = ScanDB(scan_id="s1", project_id="p1", scan_mode="QUICK", state=ScanState.RUNNING, created_at=datetime.now(timezone.utc))
    db.add(s1)
    db.commit()

    # Execution
    updated = poll_jenkins_for_active_scans()

    # Verification (should be 0 since mock JenkinsClient won't return terminal states by default or without build_number)
    assert updated == 0
    db.refresh(s1)
    assert s1.state == ScanState.RUNNING
