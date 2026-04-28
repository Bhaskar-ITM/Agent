# Knowledge Graph Report

## Graph Statistics

| Metric | Value |
|--------|-------|
| Nodes | 482 |
| Edges | 877 |
| Communities | 44 |
| God Nodes | 10 |

---

## Top God Nodes (Most Connected)

| Node | Connections | Description |
|------|-------------|-------------|
| ScanState | 81 edges | Central state management for scans |
| ProjectDB | 64 edges | Database model for projects |
| ScanDB | 64 edges | Database model for scan results |
| JenkinsClient | 14 edges | Jenkins API client wrapper |
| main() | 11 edges | FastAPI application entry |

---

## Key Communities

| Community | Nodes | Domain |
|-----------|-------|--------|
| 0 | 105 | Database models & state handling |
| 1 | 77 | Frontend React components |
| 2 | 32 | API endpoints & routes |
| 3 | 30 | Jenkins integration services |
| 4 | 28 | Validation & utilities |
| 5 | 24 | WebSocket handlers |
| 6 | 23 | Test suites |

---

## Architecture Insights

### Central Abstractions
1. **ScanState** - Most connected, manages scan lifecycle
2. **ProjectDB/ScanDB** - Equal importance, data persistence
3. **JenkinsClient** - External service integration

### Structural Observations
- Frontend and backend are well-separated in communities
- API routes cluster together appropriately
- Tests form their own community

### Surprising Connections
- ScanState connects to both ProjectDB and JenkinsClient (indirect)
- WebSocket manager bridges API and frontend communities

---

## Recommendations

### 1. File Organization
- Keep files under 300 lines (AI reads faster)
- Use descriptive filenames (e.g., `useScanStatus.ts` not `hooks.ts`)

### 2. Feature-Based Structure
- Current layered structure works but feature-based is more AI-friendly
- Consider grouping by feature: `/scans/triggers.py`, `/scans/results.py`

### 3. Split Priority Files
- `backend/app/api/scans.py` (732 lines) - Already started splitting
- `src/pages/ScanStatusPage.tsx` (651 lines) - Already extracted hook

---

## Generated Files

| File | Description |
|------|-------------|
| `graph.html` | Interactive visualization (open in browser) |
| `graph.json` | Raw graph data for programmatic access |
| `analysis.json` | Community and god node analysis |
| `extraction.json` | AST extraction results |

---

*Generated: 2026-04-13*