# Workflows

## Add Feature

Standard workflow for adding new features to this project.

### Prerequisites
- Read `.ai/context.md` to understand the project
- Check `.ai/constraints.md` for rules
- Check `.ai/preferences.md` for code style

### Steps

#### 1. Understand the Request
- What is the feature?
- Who is the user (end user, admin, service)?
- What existing functionality does it relate to?

#### 2. Discover (Read-Only)
```bash
# Search for related code
grep -r "related_concept" backend/app/src/
grep -r "related_concept" src/

# Check existing patterns
ls backend/app/api/
ls src/components/
ls src/hooks/

# Review recent commits for style
git log --oneline -10
```

#### 3. Design
- **Backend:** Which API endpoint? New or existing resource?
- **Frontend:** New page, component, or hook?
- **Database:** New model or extend existing?
- **Integration:** Does it affect Jenkins pipeline?

#### 4. Implement (Backend First)
```bash
# 1. Add/extend schema
backend/app/schemas/

# 2. Add/extend model (if needed)
backend/app/models/

# 3. Add service logic
backend/app/services/

# 4. Add API endpoint
backend/app/api/

# 5. Add tests
pytest tests/
```

#### 5. Implement (Frontend)
```bash
# 1. Add TypeScript types
src/types.ts

# 2. Add/update API service
src/services/api.ts

# 3. Add hook (if reusable logic)
src/hooks/

# 4. Add component
src/components/  or  src/pages/

# 5. Add route (if new page)
src/App.tsx

# 6. Add tests
npx vitest run
```

#### 6. Test
```bash
# Backend tests
pytest tests/ -v

# Frontend tests
npx vitest run

# Build check
npm run build  # Frontend
# Check backend syntax
python -m py_compile backend/app/main.py
```

#### 7. Commit
```bash
git add .
git commit -m "feat: describe WHAT and WHY"
```

#### 8. Update Task Tracking
- Move task from `backlog.md` to `completed.md`
- Update `current.md` if starting next task

### Code Review Checklist
Before considering a feature done:
- [ ] All imports resolved
- [ ] Types defined (no `any`)
- [ ] Error handling in place
- [ ] Tests written
- [ ] File under 300 lines (split if needed)
- [ ] Follows existing naming conventions
- [ ] No secrets in code or commits
- [ ] Build passes
