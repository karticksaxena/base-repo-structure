# base-repo-structure

Starter template: **FastAPI** backend (Python, `uv`, NestJS-style feature modules, dishka DI, loguru) and a **Next.js** frontend (oxlint, Prettier, Vitest). Linting, types, size limits (files ≤ 500 lines, functions ≤ 100) and the router → service → repository structure are enforced in the CLI and in VS Code's Problems panel. The TypeScript-backend twin is `base-repo-ts` (NestJS).

Both apps start bare — add folders and libraries as features need them.

## Quick start

```bash
cd backend && uv sync && cp .env.example .env
uv run granian --interface asgi --reload src.app.main:app   # http://localhost:8000/docs

cd ../frontend && nvm install && nvm use && pnpm install
pnpm run dev                                 # http://localhost:3000
```

Once per clone:

```bash
git config core.hooksPath .githooks   # pre-commit hook: runs the checks below (except build and audits), blocks failing commits
```

In VS Code: install the recommended extensions (Pylance and ESLint not wanted), then **Python: Select Interpreter → `backend/.venv`** and, with a `.tsx` file open, **TypeScript: Select TypeScript Version → Use Workspace Version** (Next.js plugin). Problems then show Ruff, BasedPyright, Flake8 (function length), Pylint (file length), tach (structure), oxc, TypeScript and Next.js rules — details in [`SETUP.md`](SETUP.md).

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
uv run pip-audit                     # dependency vulnerabilities

# frontend/
pnpm run lint          # oxlint (type-aware, size limits)
pnpm run typecheck     # tsc --noEmit
pnpm run format:check  # Prettier
pnpm run test          # Vitest
pnpm run build         # Turbopack
pnpm run audit         # dependency vulnerabilities
```

In VS Code: **Tasks: Run Task → `check: all`** runs every check except the audits and lists every file's problems in the Problems panel.

## Layout

```
backend/src/app/
  main.py               # app factory: logger, routers, dishka
  core/                 # config, logger, container
  common/               # shared by 2+ features (errors, utils) — never imports a feature
  features/<name>/      # __init__ · router · service · repository · schemas · dependencies · tach.domain.toml
frontend/src/app/       # Next.js App Router
```

The backend follows a NestJS-style structure enforced by tach and a structure test — the rules are in [`backend/CLAUDE.md`](backend/CLAUDE.md#nestjs-style-structure-enforced--the-linters-fail-on-violations).

## Docs

- [`SETUP.md`](SETUP.md) — tooling setup and verification (read this first)
- [`CLAUDE.md`](CLAUDE.md) — shared coding rules for AI agents
- [`backend/CLAUDE.md`](backend/CLAUDE.md) — backend rules
- [`frontend/CLAUDE.md`](frontend/CLAUDE.md) — frontend rules
