"""
Scan Recovery Service - Auto-recovery for stuck scans

This service periodically checks for scans that have been stuck in
QUEUED or RUNNING state for too long and marks them as FAILED.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.db_models import ScanDB, ProjectDB
from app.state.scan_state import ScanState
from app.core.config import settings

logger = logging.getLogger(__name__)

TERMINAL_STATES = {ScanState.COMPLETED, ScanState.FAILED, ScanState.CANCELLED}

def recover_stuck_scans() -> int:
    """
    Find and recover stuck scans.
    
    A scan is considered stuck if:
    - It's in QUEUED or RUNNING state
    - It hasn't been updated in more than SCAN_TIMEOUT seconds
    
    Returns: Number of scans recovered
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        timeout_threshold = now - timedelta(seconds=settings.SCAN_TIMEOUT)
        
        # Find stuck scans
        stuck_scans = db.query(ScanDB).filter(
            ScanDB.state.in_([ScanState.QUEUED, ScanState.RUNNING]),
            ScanDB.created_at < timeout_threshold
        ).all()
        
        recovered_count = 0
        for scan_obj in stuck_scans:
            logger.warning(
                f"Recovering stuck scan {scan_obj.scan_id} "
                f"(stuck since {scan_obj.created_at}, timeout={settings.SCAN_TIMEOUT}s)"
            )
            
            # Mark scan as failed
            scan_obj.state = ScanState.FAILED
            scan_obj.finished_at = now
            scan_obj.error_message = f"Scan timed out after {settings.SCAN_TIMEOUT} seconds"
            scan_obj.error_type = "TIMEOUT"
            
            # Update project state
            project_obj = db.query(ProjectDB).filter(
                ProjectDB.project_id == scan_obj.project_id
            ).first()
            if project_obj:
                project_obj.last_scan_state = ScanState.FAILED.value
            
            recovered_count += 1
            logger.info(f"Successfully recovered scan {scan_obj.scan_id}")
        
        if recovered_count > 0:
            db.commit()
            logger.info(f"Recovery complete: {recovered_count} scan(s) recovered")
        
        return recovered_count
        
    except Exception as e:
        logger.error(f"Error during scan recovery: {e}", exc_info=True)
        db.rollback()
        return 0
    finally:
        db.close()


def recover_single_scan(scan_id: str) -> bool:
    """
    Recover a specific scan by ID.
    
    Use this for manual recovery via API.
    
    Returns: True if recovered, False otherwise
    """
    db = SessionLocal()
    try:
        scan_obj = db.query(ScanDB).filter(ScanDB.scan_id == scan_id).first()
        if not scan_obj:
            logger.warning(f"Scan {scan_id} not found for recovery")
            return False
        
        if scan_obj.state in TERMINAL_STATES:
            logger.info(f"Scan {scan_id} already in terminal state {scan_obj.state}")
            return False
        
        # Mark as failed
        scan_obj.state = ScanState.FAILED
        scan_obj.finished_at = datetime.utcnow()
        scan_obj.error_message = "Recovered by admin request"
        scan_obj.error_type = "ADMIN_RECOVERY"
        
        # Update project
        project_obj = db.query(ProjectDB).filter(
            ProjectDB.project_id == scan_obj.project_id
        ).first()
        if project_obj:
            project_obj.last_scan_state = ScanState.FAILED.value
        
        db.commit()
        logger.info(f"Manually recovered scan {scan_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error recovering scan {scan_id}: {e}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()


def run_recovery_task():
    """
    Background task to run recovery periodically.
    
    Call this from a background thread or scheduler.
    """
    import time
    
    while True:
        try:
            logger.info("Running scheduled scan recovery...")
            count = recover_stuck_scans()
            if count > 0:
                logger.info(f"Recovery task complete: {count} scans recovered")
            else:
                logger.debug("Recovery task complete: no stuck scans found")
        except Exception as e:
            logger.error(f"Recovery task failed: {e}", exc_info=True)
        
        # Run every 5 minutes
        time.sleep(300)
