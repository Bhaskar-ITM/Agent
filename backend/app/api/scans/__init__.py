"""Scan API module - organized by responsibility."""

from fastapi import APIRouter

from app.api.scans.triggers import router as triggers_router
from app.api.scans.results import router as results_router
from app.api.scans.callbacks import router as callbacks_router
from app.api.scans.management import router as management_router
from app.api.scans.history import router as history_router
from app.api.scans import constants

# Re-export constants for backward compatibility
from app.api.scans.constants import TERMINAL_STATES, ACTIVE_STATES, STAGE_TIMEOUTS

# Main router that includes all scan endpoints
router = APIRouter()

# Include all sub-module routers
router.include_router(triggers_router)
router.include_router(results_router)
router.include_router(callbacks_router)
router.include_router(management_router)
router.include_router(history_router)

__all__ = [
    "router",
    "constants",
    "TERMINAL_STATES",
    "ACTIVE_STATES",
    "STAGE_TIMEOUTS",
]
