# Constraints

Rules that must **NEVER** be violated when working on this codebase.

## Hard Constraints (Never Break)

### Code Integrity
- **DO NOT DELETE CODE** unless it's provably dead, a duplicate, or strictly empty
- **DO NOT BREAK IMPORTS** - If you move a file, update ALL imports. If unsure, DON'T move it
- **DO NOT USE `git push --force`** - Ever
- **DO NOT COMMIT SECRETS** - Never commit `.env.*` files, API keys, or credentials
- **PRESERVE GIT HISTORY** - Make atomic, logical commits. No rebasing that rewrites history

### Security
- **Never log secrets** - API keys, tokens, passwords must never appear in logs
- **Validate all inputs** - Use Pydantic schemas for backend, TypeScript types for frontend
- **Authentication required** - All API endpoints except auth/login and public docs must require auth
- **Rate limit public endpoints** - Use the existing slowapi configuration
- **Callback token validation** - Jenkins callback must validate CALLBACK_TOKEN

### Architecture
- **Keep files under 300 lines** - Split by responsibility if they grow larger
- **One hook/component per file** - No mega-files with multiple unrelated exports
- **Use existing patterns** - Don't introduce new patterns without discussion
- **Feature-based organization preferred** - But respect existing layered backend structure

## Soft Constraints (Follow Unless There's a Good Reason)

### TypeScript
- **No `any` types** - Use proper type definitions from `src/types.ts`
- **Use `type` for shapes, `interface` for extensible contracts**
- **Export types from `src/types.ts`** - Keep type definitions centralized
- **Use `import type` for type-only imports**

### Python
- **Type hints required** - All function signatures must have type annotations
- **snake_case for vars/functions, PascalCase for classes, SCREAMING_SNAKE_CASE for constants**
- **Use absolute imports from `app.`** - No relative imports between packages
- **HTTPException with descriptive detail** - Include appropriate HTTP status codes

### React
- **Default export pages, named export reusable components**
- **Use `memo()` for components that re-render frequently**
- **Use arrow functions** - Set `displayName` for memoized components
- **Custom hooks for logic extraction** - One concern per hook
- **@tanstack/react-query for data fetching** - No manual fetch + useState patterns

### Testing
- **Co-locate tests with source** or use dedicated `tests/` directory
- **Vitest for frontend, pytest for backend**
- **Mock external services** - Jenkins, database, etc. should be mocked in tests
- **Tests must pass before committing** - Run tests before claiming work is done

## Environment-Specific Constraints

### Docker
- **Don't mount local directories over built files** - Was causing nginx 403 errors
- **Use environment-specific compose files** - dev, test, staging overlays
- **Wait for health checks** - Services need 2-3 minutes to be fully healthy

### Jenkins
- **Pipeline timeout** - Default 7200 seconds (2 hours), configurable per scan
- **Callback URL** - Must be reachable from Jenkins server
- **Stage order matters** - Dependencies enforced in pipeline and backend

## Known Limitations
- Manual scan stage selection doesn't show dependency visualization
- ETA calculation uses hardcoded durations (not historical data)
- Browser notifications request permission on mount (should be opt-in)
- No undo/toast system for destructive actions yet
- Mobile responsiveness needs work (sidebar always w-64)
