# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Browser                         │
│              http://localhost:5173                      │
└────────────┬────────────────────────────┬────────────────┘
             │ HTTP/REST                  │ WebSocket
             │                            │
┌────────────▼────────────┐   ┌───────────▼──────────────┐
│    Frontend (React)     │   │  Backend (FastAPI)       │
│  src/                   │   │  backend/app/            │
│  - Pages (7)            │   │  - API routes            │
│  - Components (20+)     │   │  - WebSocket manager     │
│  - Hooks (6)            │   │  - Celery tasks          │
│  - Services (2)         │   │  - State management      │
└─────────────────────────┘   └───────────┬──────────────┘
                                          │
                            ┌─────────────▼──────────────┐
                            │   Infrastructure           │
                            │  ┌─────────┐  ┌─────────┐ │
                            │  │PostgreSQL│  │  Redis  │ │
                            │  │  (DB)    │  │(Cache)  │ │
                            │  └─────────┘  └─────────┘ │
                            └─────────────┬──────────────┘
                                          │
                            ┌─────────────▼──────────────┐
                            │   Jenkins Server           │
                            │  http://localhost:8080     │
                            │  - Security Pipeline       │
                            │  - SonarQube, Trivy, ZAP   │
                            │  - Callback to backend     │
                            └────────────────────────────┘
```

## Data Flow

### Scan Lifecycle
```
1. User triggers scan (Frontend → POST /api/v1/scans)
2. Backend creates ScanDB in CREATED state
3. Backend enqueues Celery task
4. Celery task triggers Jenkins pipeline via API
5. Jenkins runs scan stages sequentially
6. Jenkins POSTs results to /api/v1/scans/{id}/callback
7. Backend updates ScanDB state and results
8. WebSocket manager broadcasts update to connected clients
9. Frontend receives real-time update via WebSocket
10. User sees scan progress/results
```

### Authentication Flow
```
1. User logs in (POST /api/v1/auth/login)
2. Backend validates credentials, returns JWT token
3. Frontend stores token, includes in subsequent requests
4. Protected endpoints validate JWT via get_current_user dependency
5. API key auth available for service-to-service (API_KEY env var)
```

## Key Architectural Patterns

### Backend: Layered Architecture
```
API Layer (routes)
  ↓
Service Layer (business logic)
  ↓
Infrastructure Layer (external integrations)
  ↓
Data Layer (models, database)
```

- **API Layer:** FastAPI routers (`backend/app/api/`)
  - Route definitions, request validation, HTTP response
  - Delegates to services for business logic

- **Service Layer:** (`backend/app/services/`)
  - Jenkins service (API communication)
  - Validation service (scan request validation)
  - Scan orchestration logic

- **Infrastructure Layer:** (`backend/app/infrastructure/`)
  - HTTP client, Jenkins client

- **Data Layer:** (`backend/app/models/`, `backend/app/schemas/`)
  - SQLAlchemy models (ProjectDB, ScanDB)
  - Pydantic schemas (ScanCreate, ScanResponse)

### Frontend: Component-Based Architecture
```
Pages (route-level)
  ↓
Components (reusable UI)
  ↓
Services (API, notifications)
  ↓
Hooks (shared logic)
```

- **Pages:** Route-level components, handle data fetching
- **Components:** Reusable UI elements (buttons, modals, progress bars)
- **Services:** API client, notification service
- **Hooks:** Custom React hooks for scan state, WebSocket, auth

### State Management
- **Server State:** @tanstack/react-query (frontend), PostgreSQL (backend)
- **Client State:** React useState/useReducer
- **Real-time Updates:** WebSocket broadcasts
- **Background Tasks:** Celery with Redis broker

## Database Schema

### ProjectDB
```python
project_id: str (PK)
name: str
git_url: str
branch: str
credentials_id: str
sonar_key: str
target_ip: str
target_url: str
status: str
last_scan_state: str
created_at: datetime
```

### ScanDB
```python
scan_id: str (PK)
project_id: str (FK → ProjectDB)
scan_mode: str (AUTOMATED | MANUAL)
selected_stages: list[str]
state: ScanState (Enum)
created_at: datetime
started_at: datetime | null
finished_at: datetime | null
jenkins_build_number: str | null
jenkins_queue_id: str | null
stage_results: list[dict]
error_message: str | null
error_type: str | null
jenkins_console_url: str | null
callback_digests: list[str]
retry_count: int
```

## WebSocket Architecture

### Connection Management
- **Manager:** `backend/app/websockets/manager.py`
- **Endpoints:** 
  - `/api/v1/ws/scans?scan_id={id}` - Subscribe to specific scan
  - `/api/v1/ws/dashboard` - Subscribe to all scan updates
- **Features:**
  - Auto-reconnect on connection loss
  - Ping/pong keepalive
  - Broadcast to scan-specific and dashboard subscribers

### Frontend Hook
- `useScanWebSocket(scanId, onMessage)` - Manages connection lifecycle
- Handles reconnection, message parsing, state updates
- Integrated with TanStack Query cache

## Security Integration

### Jenkins Pipeline Stages
| Stage | Tool | Purpose |
|-------|------|---------|
| Sonar Scanner | SonarQube | Static code analysis |
| Sonar Quality Gate | SonarQube | Quality threshold validation |
| NPM / PIP Install | Package managers | Dependency installation |
| Dependency Check | OWASP DC | Third-party vulnerability scanning |
| Trivy FS Scan | Trivy | Filesystem vulnerability scan |
| Docker Build | Docker | Container image build |
| Docker Push | Registry | Image push to registry |
| Trivy Image Scan | Trivy | Container vulnerability scan |
| Nmap Scan | Nmap | Network port scanning |
| ZAP Scan | OWASP ZAP | Web application security test |

### Authentication Methods
1. **JWT Token** - User authentication (login flow)
2. **API Key** - Service-to-service (X-API-Key header)
3. **Callback Token** - Jenkins webhook validation (X-Callback-Token header)

## Recent Architectural Decisions

### 2026-04-13: File Structure Cleanup
- Removed duplicate directories from `Agent/`
- Kept source code at root level (git-tracked)
- Updated `.gitignore` to prevent build artifact pollution
- Fixed nginx 403 error by removing conflicting volume mount

### 2026-04-13: Backend Module Splitting
- Started splitting `scans.py` (732 lines) into `scans/` module
- Created: `constants.py`, `helpers.py`, `triggers.py`, `__init__.py`
- Remaining: `callbacks.py`, `results.py`, `management.py`, `history.py`

### 2026-04-13: Frontend Hook Extraction
- Extracted `useScanStatus.ts` from `ScanStatusPage.tsx`
- Contains scan state management, WebSocket integration, modal handling
- Reduces page complexity from 651 lines → view + logic separation

## Known Technical Debt

| Issue | Impact | Priority |
|-------|--------|----------|
| `scans.py` still exists alongside `scans/` module | Import confusion | High |
| `ScanStatusPage.tsx` still 651 lines | Complex component | Medium |
| `ProjectControlPage.tsx` 449 lines | Mixes concerns | Medium |
| No toast notification system | Poor UX for actions | Medium |
| Notification permission on mount | Bad timing | Low |
| No mobile responsiveness | UX issue | Low |
| Hardcoded ETA calculation | Inaccurate | Low |
