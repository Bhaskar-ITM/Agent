import logging
import os
import threading
import time
from pathlib import Path

from fastapi import Depends, FastAPI

from app.api import projects, scans
from app.core.auth import require_api_key
from app.core.config import settings
from app.state.persistence import persist_state, restore_state
from app.state.store import projects_db, scans_db, scans_db_lock

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DevSecOps Control Plane API",
    dependencies=[Depends(require_api_key)],
)


def _expiry_worker():
    logger.info("Scan expiry worker started")
    while True:
        time.sleep(60)
        try:
            with scans_db_lock:
                # Performance Optimization (Bolt ⚡): Pre-calculating values and batching persistence.
                # Prevents O(N) disk writes and redundant calculations in the background worker.
                now = datetime.utcnow()
                timeout_seconds = settings.SCAN_TIMEOUT
                mutated = False
                for scan_obj in list(scans_db.values()):
                    if scans._expire_scan_if_timed_out(scan_obj, now=now, timeout_seconds=timeout_seconds):
                        mutated = True
                if mutated:
                    persist_state(scans_db, projects_db)
        except Exception:
            logger.exception("Expiry worker encountered an error")


@app.on_event("startup")
def validate_configuration():
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required")
    if not settings.JENKINS_BASE_URL:
        raise RuntimeError("JENKINS_BASE_URL is required")
    if not settings.STORAGE_PATH:
        raise RuntimeError("STORAGE_PATH is required")

    worker_count = int(os.environ.get("WEB_CONCURRENCY", "1"))
    if worker_count > 1:
        raise RuntimeError(f"WEB_CONCURRENCY={worker_count} is forbidden. This application requires exactly 1 worker.")

    Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    restored_scans, restored_projects = restore_state()
    with scans_db_lock:
        scans_db.clear()
        scans_db.update(restored_scans)
        projects_db.clear()
        projects_db.update(restored_projects)

    threading.Thread(target=_expiry_worker, daemon=True, name="expiry-worker").start()


app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
app.include_router(scans.router, prefix="/api/v1", tags=["scans"])


@app.get("/")
def read_root():
    return {"message": "DevSecOps Control Plane is live"}
