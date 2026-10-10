# base-repo-structure

Starter template: **FastAPI** backend (Python, `uv`, NestJS-style feature modules, dishka DI, loguru) and a **Next.js** frontend (oxlint, Prettier, Vitest). Linting, types, size limits (files ≤ 500 lines, functions ≤ 100) and the router → service → repository structure are enforced in the CLI and in VS Code's Problems panel. The TypeScript-backend twin is `base-repo-ts` (NestJS).

Both apps start bare — add folders and libraries as features need them.

## Quick start

```bash
cd backend && uv sync
uv run uvicorn src.app.main:app --reload     # http://localhost:8000/docs

cd ../frontend && nvm install && nvm use && pnpm install
pnpm run dev                                 # http://localhost:3000
```

## Checks

```bash
# backend/
uv run ruff check src tests          # lint
uv run ruff format --check src tests # format
uv run basedpyright                  # types
uv run flake8 src tests              # functions <= 100 lines
uv run pylint src tests              # files <= 500 lines
uv run tach check                    # router -> service -> repository
uv run pytest                        # tests + feature structure

# frontend/
pnpm run lint          # oxlint (type-aware, size limits)
pnpm run typecheck     # tsc --noEmit
pnpm run format:check  # Prettier
pnpm run test          # Vitest
pnpm run build         # Turbopack
pnpm run audit         # dependency vulnerabilities
```

In VS Code: **Tasks: Run Task → `check: all`** runs everything and lists every file's problems in the Problems panel.

## Layout

```
backend/src/app/
  main.py               # app factory: logger, routers, dishka
  core/                 # config, logger, container
  features/<name>/      # router · service · repository · schemas · dependencies
frontend/src/app/       # Next.js App Router
```

## Docs

- [`SETUP.md`](SETUP.md) — tooling setup and verification (read this first)
- [`CLAUDE.md`](CLAUDE.md) — shared coding rules for AI agents
- [`backend/CLAUDE.md`](backend/CLAUDE.md) — backend rules
- [`frontend/CLAUDE.md`](frontend/CLAUDE.md) — frontend rules
