# Project Context

## Tech Stack

### Frontend
- **Framework:** React 19 with TypeScript 5.9
- **Build Tool:** Vite 7
- **Styling:** TailwindCSS 4
- **Routing:** React Router 7
- **State Management:** TanStack Query 5 (@tanstack/react-query)
- **HTTP Client:** Axios
- **Icons:** Lucide React
- **Testing:** Vitest + React Testing Library

### Backend
- **Framework:** Python FastAPI
- **Database:** PostgreSQL 16 (via SQLAlchemy ORM)
- **Task Queue:** Celery with Redis 7 broker
- **Caching:** Redis 7
- **Authentication:** JWT tokens + API key auth
- **Rate Limiting:** SlowAPI
- **Testing:** pytest with FastAPI TestClient

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Reverse Proxy:** Nginx (for frontend in staging)
- **CI/CD:** Jenkins (Groovy Pipeline)
- **Security Tools:** Trivy, SonarQube, Nmap, OWASP ZAP, Dependency-Check

### Environment Profiles
| Profile | Purpose | Key Settings |
|---------|---------|--------------|
| `dev` | Local development | Mock execution, debug logging, hot reload |
| `test` | CI testing | Isolated DB, mocked execution |
| `staging` | Production-like | Real Jenkins/Kali integration, persistent services |

## Entry Points

### Application Entry Points
| Component | File | Description |
|-----------|------|-------------|
| Backend API | `backend/app/main.py` | FastAPI app initialization, route registration |
| Frontend App | `src/main.tsx` → `src/App.tsx` | React SPA root with routing |
| Celery Worker | `backend/app/core/celery_app.py` | Background task processor |
| WebSocket Manager | `backend/app/websockets/manager.py` | Real-time scan update broadcaster |

### Build/Run Commands
```bash
# Start staging environment (recommended)
cd Agent && docker compose -f docker/docker-compose.yml -f docker/docker-compose.staging.yml --env-file .env.staging up -d --build

# Frontend dev server
npm run dev

# Backend (if running locally)
cd backend && uvicorn app.main:app --reload

# Run tests
npx vitest run          # Frontend
pytest tests/           # Backend
```

### Access URLs (Staging)
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Domain Knowledge

### What This Project Does
DevSecOps security scanning pipeline with a web-based management interface. Users can:
1. Create projects with git repositories
2. Trigger automated security scans (SonarQube, Trivy, Nmap, ZAP, etc.)
3. Monitor scan progress in real-time via WebSocket
4. View detailed scan results with vulnerability reports
5. Manage scan lifecycle (reset failed scans, cancel running scans)

### Core Concepts
- **Project:** A git repository to be scanned. Contains git URL, branch, credentials, target info.
- **Scan:** A security scan execution. Has states: CREATED → QUEUED → RUNNING → COMPLETED/FAILED/CANCELLED
- **Stage:** Individual scan steps (git checkout, sonar scanner, trivy scan, etc.)
- **Jenkins Pipeline:** Groovy script that orchestrates the actual security scanning
- **Callback:** Jenkins POSTs results back to the backend when a scan completes

### Jenkins Integration
- Pipeline defined in `Agent/Jenkinsfile`
- Callback endpoint: `POST /api/v1/scans/{scan_id}/callback`
- Callback token authentication via `CALLBACK_TOKEN` env var
- Scan modes: AUTOMATED (all stages) or MANUAL (selected stages)

### Database Models
- **ProjectDB:** Projects with git info, credentials, last scan state
- **ScanDB:** Scan executions with state, results, error info, retry count

### Recent Improvements (2026-04-13)
- WebSocket real-time scan updates
- Browser notifications for scan completion
- Scan progress bar with ETA estimation
- Error recovery suggestions component
- Enhanced error reporting in Jenkins callback
- Fixed API authentication (VITE_API_KEY)
- File structure cleanup (removed duplicate directories)
- Fixed nginx 403 error (removed conflicting volume mount)
