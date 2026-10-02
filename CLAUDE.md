# Global Coding Rules

Backend-specific rules (stack, structure, DI, logging, exceptions, security, DB patterns, etc.) live in `backend/CLAUDE.md` and load only for sessions working under `backend/`.

## Core Rules
1. **BE CRITICAL** — challenge bad ideas, point out flaws
2. **PERFORMANCE FIRST** — analyze complexity before coding; avoid O(n²), use dict lookups, batch ops
3. **MODULAR** — functions <50 lines, files <500 lines, extract shared logic to `common/`
4. **READ CONTEXT FIRST** — use tools before editing
5. **ASK WHEN UNCLEAR** — never guess
6. **EXPLAIN APPROACH** — describe plan before implementing
7. **DRY** — Don't Repeat Yourself. If the same logic exists in 2+ places, extract it. One change, one place.
8. **YAGNI** — You Aren't Gonna Need It. Don't build for hypothetical futures. Add complexity when actually needed.
9. **KISS** — Keep It Simple, Stupid. Choose the simplest solution that works. More abstraction ≠ better code.
