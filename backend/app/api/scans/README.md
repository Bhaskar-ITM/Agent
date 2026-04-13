# Scans API Module

Scan management endpoints, organized by responsibility.

## Overview
Handles all scan-related operations: triggering scans, receiving Jenkins callbacks, retrieving results, managing scan lifecycle (reset/cancel), and project scan history.

## Public API

### From `triggers.py`
- **POST `/api/v1/scans`** - Trigger a new scan (returns 201)
- **GET `/api/v1/scans`** - List all scans with timeout checking

### TODO: Migrate from `scans.py` (732 lines)
- **GET `/api/v1/scans/{scan_id}`** - Get scan details
- **GET `/api/v1/scans/{scan_id}/results`** - Get scan stage results
- **GET `/api/v1/scans/{scan_id}/overview`** - Get scan summary
- **POST `/api/v1/scans/{scan_id}/callback`** - Jenkins callback endpoint
- **POST `/api/v1/scans/{scan_id}/reset`** - Reset a failed scan
- **POST `/api/v1/scans/{scan_id}/cancel`** - Cancel a running scan
- **POST `/api/v1/scans/{scan_id}/force-unlock`** - Unlock stuck scan
- **GET `/api/v1/projects/{project_id}/scans`** - Project scan history

## Module Files
| File | Purpose |
|------|---------|
| `constants.py` | Stage timeouts, status mappings, terminal/active states |
| `helpers.py` | Timeout calculation, response formatting, payload parsing |
| `triggers.py` | Scan trigger endpoint (POST /scans) |
| `callbacks.py` | Jenkins callback handler (TODO) |
| `results.py` | Results and overview endpoints (TODO) |
| `management.py` | Reset, cancel, unlock endpoints (TODO) |
| `history.py` | Project scan history endpoint (TODO) |

## Connection to Other Modules
- **`app.services.jenkins_service`** - Triggers Jenkins pipeline
- **`app.tasks.jenkins_tasks`** - Celery async task for scan triggering
- **`app.state.scan_state`** - Scan state enum (CREATED, RUNNING, etc.)
- **`app.websockets.manager`** - Broadcasts scan updates
- **`app.models.db_models`** - ScanDB, ProjectDB models
- **`app.schemas.scan`** - Request/response Pydantic models
