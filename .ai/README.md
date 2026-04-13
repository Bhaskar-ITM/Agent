# .ai/ Control Center

This directory is the **AI Control Center** for autonomous development.

## How to Use This

When an AI (or human developer) picks up this project, they should:

1. **Read this file first** - It explains where to find project context
2. **Check `tasks/current.md`** - See what's being worked on
3. **Review `constraints.md`** - Understand what rules to follow
4. **Check `memory/gotchas.md`** - Know the landmines before touching code

## Directory Structure

```
.ai/
├── README.md           ← You are here
├── context.md          ← Tech stack, entry points, domain knowledge
├── constraints.md      ← Rules that must never be broken
├── preferences.md      ← Naming conventions, code style (extracted from actual code)
├── architecture.md     ← Current system architecture documentation
├── workflows/
│   └── add-feature.md  ← Standard workflow for adding new features
├── tasks/
│   ├── current.md      ← What's being worked on NOW
│   ├── backlog.md      ← Future work items
│   └── completed.md    ← What's been done
└── memory/
    └── gotchas.md      ← Weird hacks, edge cases, "don't touch this" notes
```

## AI Handoff Protocol

When starting a new development session:
1. Read `.ai/context.md` to refresh project knowledge
2. Check `.ai/tasks/current.md` for active work
3. Review `.ai/memory/gotchas.md` before making changes
4. Update `.ai/tasks/completed.md` when done
5. Commit changes with clear, descriptive messages

## Key Principles

- **Document-First, Move-Second:** Always analyze before changing
- **Never Delete Code:** Unless it's a duplicate or provably dead
- **Preserve Git History:** Atomic commits, no force pushes
- **Ask > Assume:** If unsure, stop and ask the user
