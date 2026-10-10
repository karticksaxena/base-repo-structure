# Global Coding Rules

The backend follows a NestJS-style feature structure that the linters enforce (`backend/CLAUDE.md` → NestJS-style structure). Backend rules live in `backend/CLAUDE.md`, frontend rules in `frontend/CLAUDE.md`; each loads only for sessions working in that folder. Tooling setup for both: `SETUP.md`.

## Core Rules

1. **BE CRITICAL** — challenge bad ideas, point out flaws
2. **PERFORMANCE FIRST** — analyze complexity before coding; avoid O(n²), use dict/set lookups, batch ops
3. **MODULAR** — functions ≤100 lines, files ≤500 lines, enforced as errors by the linters (`SETUP.md`). Split the code; never raise a limit, disable a rule or loosen a structure check to make a failure go away
4. **READ CONTEXT FIRST** — use tools before editing
5. **ASK WHEN UNCLEAR** — never guess
6. **EXPLAIN APPROACH** — describe plan before implementing
7. **DRY** — Don't Repeat Yourself. If the same logic exists in 2+ places, extract it. One change, one place.
8. **YAGNI** — You Aren't Gonna Need It. Don't build for hypothetical futures. Add complexity when actually needed.
9. **KISS** — Keep It Simple, Stupid. Choose the simplest solution that works. More abstraction ≠ better code.

## Grounded research

Use the **`grounded-research`** skill before deciding on best practices, setup steps, versions, libraries, config options or anything new or fast-moving — never from memory alone. If the skill isn't installed, follow the same method: check the installed packages, then Context7, DeepWiki and the web; cross-check 2+ sources, verify by running, cite sources, and flag anything unverified.

## Subagents

Start subagents on the **Sonnet** model only (`model: "sonnet"` on every Agent call) — never Opus or larger — to keep usage costs down.
