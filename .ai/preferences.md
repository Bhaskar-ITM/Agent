# Preferences

Extracted from the **actual code** in this project. These are the conventions already in use - **document them, don't invent new ones**.

## Naming Conventions

### Python (Backend)
```python
# Variables and functions: snake_case
def calculate_scan_timeout(selected_stages: list) -> int:
    ...

# Classes: PascalCase
class ScanState(Enum):
    ...

# Constants: SCREAMING_SNAKE_CASE
STAGE_TIMEOUTS = {...}
TERMINAL_STATES = {...}

# Database models: PascalCase with DB suffix
class ProjectDB(Base):
    ...
class ScanDB(Base):
    ...

# Pydantic schemas: PascalCase with descriptive suffix
class ScanCreate(BaseModel):
    ...
class ScanResponse(BaseModel):
    ...

# Files: snake_case
backend/app/api/scans.py
backend/app/core/config.py
```

### TypeScript (Frontend)
```typescript
// Variables and functions: camelCase
const scanData = useQuery({...});
function handleReset() {...}

// Components: PascalCase (file and export)
// Pages: default export
export default function ScanStatusPage() {...}
// Reusable components: named export
export function ScanProgressBar({ stages }: Props) {...}

// Hooks: camelCase with use prefix
export function useScanStatus() {...}
export function useScanWebSocket() {...}

// Types: PascalCase
export type Project = {...};
export interface Scan {...}

// Files:
// Pages: PascalCase.tsx (ScanStatusPage.tsx)
// Components: PascalCase.tsx (ScanProgressBar.tsx)
// Hooks: camelCase.ts (useScanStatus.ts)
// Services: camelCase.ts (api.ts)
// Types: types.ts
```

## File Organization

### Backend Structure
```
backend/app/
├── api/           # REST endpoints (one file per resource)
│   ├── scans/     # Scans module (feature-based, being split)
│   │   ├── constants.py    # Stage configs, mappings
│   │   ├── helpers.py      # Utility functions
│   │   ├── triggers.py     # Trigger endpoints
│   │   ├── callbacks.py    # Jenkins callback (TODO)
│   │   ├── results.py      # Results/overview endpoints (TODO)
│   │   ├── management.py   # Reset/cancel/unlock (TODO)
│   │   └── history.py      # Project scan history (TODO)
│   ├── auth.py             # Auth endpoints (~100 lines)
│   └── projects.py         # Project endpoints (~200 lines)
├── core/          # Core infrastructure
│   ├── config.py           # Settings, env vars
│   ├── db.py               # Database connection
│   ├── auth.py             # JWT auth logic
│   ├── celery_app.py       # Celery configuration
│   └── rate_limit.py       # Rate limiting setup
├── models/        # SQLAlchemy database models
├── schemas/       # Pydantic request/response schemas
├── services/      # Business logic (Jenkins, validation, orchestration)
├── state/         # Scan state management (ScanState enum)
├── tasks/         # Celery async tasks
└── websockets/    # WebSocket managers
```

### Frontend Structure
```
src/
├── components/    # Reusable UI components (< 300 lines each)
├── pages/         # Page-level components (may need splitting)
├── services/      # API client, notification service
├── hooks/         # Custom React hooks (one concern per file)
├── utils/         # Utility functions (apiError handling)
├── types.ts       # TypeScript type definitions
├── App.tsx        # Router configuration
└── main.tsx       # React app entry point
```

## Import Patterns

### TypeScript
```typescript
// 1. External libraries
import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';

// 2. Internal modules (relative imports)
import { api } from '../services/api';
import { useScanReset } from '../hooks/useScanReset';

// 3. Types (use import type)
import type { Project, Scan } from '../types';
```

### Python
```python
# 1. Standard library
from datetime import datetime, timezone
from typing import List, Optional
import logging
import uuid

# 2. Third-party
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

# 3. Local (absolute imports from app.)
from app.core.config import settings
from app.core.db import get_db
from app.models.db_models import ScanDB, ProjectDB
from app.api.scans.helpers import calculate_scan_timeout
```

## Code Style

### TypeScript
- **Semicolons:** No (per project defaults)
- **Quotes:** Single quotes
- **Trailing commas:** Where valid
- **Arrow functions:** Preferred over function declarations
- **Default exports:** Pages only; named exports for components

### Python
- **Line length:** Follow PEP 8 (79 chars, but practical limit ~100)
- **Type hints:** Required on all function signatures
- **Docstrings:** On public functions and classes
- **Error handling:** HTTPException with descriptive detail and correct status codes

## Testing Patterns

### Frontend (Vitest)
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock the API client
vi.mock('../services/api', () => ({
  api: { scans: { get: vi.fn() } }
}));

describe('ComponentName', () => {
  it('should render correctly', () => {...});
});
```

### Backend (pytest)
```python
from fastapi.testclient import TestClient
from unittest.mock import patch

def test_endpoint(client: TestClient):
    with patch("app.services.jenkins_service.trigger_scan"):
        response = client.post("/api/v1/scans", json={...})
    assert response.status_code == 201
```

## Git Commit Style
- **Format:** `type: description` (e.g., `feat:`, `fix:`, `chore:`, `docs:`)
- **Keep it concise:** One line when possible
- **Focus on "why" not "what":** "fix: prevent nginx 403 on staging" not "changed compose file"
