# base-repo-structure

Starter template: **FastAPI** backend (Python, `uv`, Granian, NestJS-style feature modules, dishka DI, Pydantic v2, loguru) and a **Next.js** frontend (oxlint, Prettier, Vitest). Linting, types, size limits and the NestJS-style structure are enforced in the CLI, in VS Code's Problems panel and by a pre-commit hook. The TypeScript-backend twin is `base-repo-ts` (NestJS).

Both apps start bare — add folders and libraries as features need them.

## What's enforced

- **Size** — files ≤ 500 lines (every line counted), functions ≤ 100 code lines, lines ≤ 100 characters (backend; Prettier wraps the frontend at 100)
- **Backend structure** (tach + `tests/test_structure.py`, verified against 113 edge cases):
  - imports go routers → services → repositories — nothing skipped, nothing upward, also inside functions and under `if TYPE_CHECKING:`
  - another feature only through its services (only `*Service` classes leave `services/`) or schemas
  - `constants/` and `utils/` stay inside their feature; `utils/` can't reach services or repositories
  - FastAPI only in routers, never in services, repositories or schemas
  - every feature has the same folders, identical layer rules and its own tests; no stray files; no comments or dynamic imports that switch a check off
- **Code** — strict types (BasedPyright `recommended`, `tsc` strict); Pydantic v2 API only; schemas reject unknown fields; list endpoints return `Page[T]`; UUIDv7 ids; any warning fails the tests
- **Not caught by a tool** — business logic inside routers (keep it in services; code review)

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

In VS Code: install the recommended extensions (Pylance and ESLint not wanted), then **Python: Select Interpreter → `backend/.venv`** and, with a `.tsx` file open, **TypeScript: Select TypeScript Version → Use Workspace Version** (Next.js plugin). Problems then show Ruff, BasedPyright, Flake8 (function length), Pylint (file length), tach (structure), oxc, TypeScript and Next.js rules — details in [`SETUP.md`](SETUP.md). After files change outside the editor, run **Tach: Restart Server** (tach doesn't watch the disk).

## Checks

```bash
# backend/
uv run ruff check src tests          # lint (incl. banned imports, no blanket noqa)
uv run ruff format --check src tests # format
uv run basedpyright                  # types, import cycles
uv run flake8 src tests              # functions <= 100 code lines
uv run pylint src tests              # files <= 500 lines
uv run tach check                    # layers: routers -> services -> repositories, constants/, utils/
uv run tach check-external           # declared dependencies; FastAPI only in routers
uv run pytest                        # tests + feature layout (folders, layer rules, tests, bypasses)
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

## Building an app from this template

1. Follow [`SETUP.md`](SETUP.md) once: newest compatible versions, extensions, editor check.
2. Go through the [ask-first list](SETUP.md#application-specific-setup--ask-the-user-first) — server, health checks, error contract, database, Redis, auth, background jobs, events, gRPC, Docker, observability — and add only what the app needs. The database, Redis and cache patterns are written out and verified in `SETUP.md`.
3. New feature: copy `features/items/` (layer rules included), rename its modules and classes, register its router in `main.py` and its provider in `app_module.py`, add `tests/features/<name>/` — steps in [`backend/CLAUDE.md`](backend/CLAUDE.md). Never edit one feature's `tach.domain.toml`.
4. Choose libraries and optimizations from live research, not memory (`backend/CLAUDE.md` → Performance).

No CI is set up: the pre-commit hook is the gate (`git commit --no-verify` skips it).

## Layout

```
backend/src/app/
  main.py               # app factory: logger, routers, dishka (Nest main.ts)
  app_module.py         # root module (Nest AppModule): every feature's provider
  core/                 # config, logger (+ database, redis) — never imports a feature
  common/               # shared by 2+ features: schemas.py (BaseSchema, Page[T]) — never imports a feature
  features/<name>/      # routers/ · services/ · repositories/ · schemas/ · constants/ · utils/ · dependencies.py · tach.domain.toml
backend/tests/          # test_structure.py + features/<name>/ (required for every feature)
frontend/src/app/       # Next.js App Router
```

The structure rules and what enforces each one are in [`backend/CLAUDE.md`](backend/CLAUDE.md#nestjs-style-structure-enforced--the-linters-fail-on-violations).

## Docs

- [`SETUP.md`](SETUP.md) — tooling setup, verification and the ask-first list (read this first)
- [`CLAUDE.md`](CLAUDE.md) — shared coding rules for AI agents
- [`backend/CLAUDE.md`](backend/CLAUDE.md) — backend rules
- [`frontend/CLAUDE.md`](frontend/CLAUDE.md) — frontend rules
