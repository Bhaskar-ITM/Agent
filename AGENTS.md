# AGENTS.md - Development Guidelines for AI Coding Agents

## Project Overview

DevSecOps security scanning pipeline with React/TypeScript frontend and Python FastAPI backend.

## Build/Lint/Test Commands

### Frontend (React + TypeScript + Vite)

```bash
cd Agent
npm install          # Install dependencies
npm run dev          # Start Vite dev server
npm run build        # Production build (tsc -b && vite build)
npm run lint         # Run ESLint
npm run preview      # Preview production build

npx vitest run                              # Run all tests
npx vitest run src/pages/LoginPage.test.tsx # Run single test file
npx vitest watch                            # Run tests in watch mode
```

### Backend (Python FastAPI)

```bash
cd Agent
pip install -r backend/requirements.txt     # Install dependencies
pytest tests/                               # Run all tests
pytest tests/test_integration.py            # Run single test file
pytest tests/test_integration.py::test_integration_v1  # Run single test
pytest -v                                   # Verbose output
```

### Docker

```bash
cd Agent
python run.py dev       # Development environment
python run.py test      # Test environment (runs tests in Docker)
python run.py staging   # Staging environment
python run.py down      # Stop all containers
```

## Code Style Guidelines

### Frontend (TypeScript/React)

**Imports:** Group: external libs → internal modules → types. Use `import type` for types.

```typescript
import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Project, Scan } from '../types';
```

**Types:** Use `type` for shapes, `interface` for extensible contracts. Export from `src/types.ts`. Avoid `any`.

**Components:** Default export pages, named export reusable. Use `memo()`, arrow functions. Set `displayName` for memoized.

**Patterns:** @tanstack/react-query for fetching, custom hooks, useMemo, React Router.

**Testing:** Vitest + React Testing Library, co-located tests, vi.mock(), describe/it/expect.

### Backend (Python/FastAPI)

**Imports:** stdlib → third-party → local. Use absolute imports from `app.`

```python
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.core.config import settings
```

**Models:** Pydantic BaseModel for schemas, SQLAlchemy for tables. Type hints required.

**Error Handling:** HTTPException with descriptive detail and appropriate status codes.

**Naming:** snake_case vars/funcs, PascalCase classes, SCREAMING_SNAKE_CASE constants.

**Testing:** pytest with fastapi.testclient.TestClient, unittest.mock.patch.

## Project Structure

```
Agent/
├── backend/app/       # API, core, models, schemas, services, state
├── src/              # components, pages, services, hooks, types.ts
├── tests/            # Python tests
├── docker/           # Docker configs
├── package.json      # Frontend deps
├── vitest.config.ts  # Test config
└── tsconfig.json     # TS config
```

## Key Files

| File | Purpose |
|------|---------|
| `src/types.ts` | TypeScript types |
| `src/services/api.ts` | API client |
| `backend/app/main.py` | FastAPI entry |
| `backend/app/core/config.py` | Settings |
| `backend/requirements.txt` | Python deps |

## Security Notes

Never commit `.env.*` or secrets. Validate callback tokens on webhooks. Rate limit public endpoints.
