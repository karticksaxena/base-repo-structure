# Backend Coding Rules

## Dev tooling

Follow **`../SETUP.md`**. Lint, type, size and test rules live in `pyproject.toml`; layer rules in `tach.toml` (app level) and each feature's `tach.domain.toml` — never in `.vscode/settings.json`, and never in a separate `pyrightconfig.json`, `.flake8` or `.pylintrc`.

## Stack

FastAPI · Pydantic + pydantic-settings · **dishka** (DI) · **loguru** (logging) · pytest · `uv` (package manager, never pip) · Python from `.python-version`

Added only when a feature needs them (`../SETUP.md` → Libraries by use case): **SQLAlchemy** (async ORM) + asyncpg · Alembic (migrations) · redis · httpx2 (outgoing HTTP)

Always the latest stable, mutually compatible versions — never prereleases, never versions hardcoded in docs.

## NestJS-style structure (enforced — the linters fail on violations)

```
src/app/
  main.py                 # app factory: logger, routers, dishka (Nest AppModule + main.ts)
  core/                   # config, logger, container — never imports a feature
  features/<name>/
    __init__.py
    router.py             # HTTP only                 (Nest controller)
    service.py            # business logic            (Nest service)
    repository.py         # data access               (DB/Redis)
    schemas.py            # Pydantic request/response (Nest DTOs)
    dependencies.py       # dishka Provider           (Nest module providers)
    tach.domain.toml      # this feature's layer rules (copied with the folder)
```

| Rule                                                                                                         | Enforced by                       | Shows up                                                                              |
| ------------------------------------------------------------------------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------------- |
| Every feature folder has all seven files (incl. `__init__.py`, `tach.domain.toml`)                           | `tests/test_structure.py`         | `uv run pytest`, task `backend: test`, pre-commit hook                                |
| Imports go router → service → repository only — no skipping, nothing upward                                  | tach (`tach.domain.toml`)         | live in open files (source `tach`), task `backend: structure (tach)`, pre-commit hook |
| Another feature is used only through its service (or schemas) — never its repository, router or dependencies | tach (`tach.domain.toml`)         | same                                                                                  |
| `core/` never imports a feature (only `container.py` imports feature providers)                              | tach                              | same                                                                                  |
| Every file is one of the files above (`root_module = "forbid"`)                                              | tach                              | same                                                                                  |
| No import cycles                                                                                             | BasedPyright `reportImportCycles` | live, whole workspace                                                                 |

- Add a feature by copying `features/items/` (its `tach.domain.toml` comes along), then register its router in `main.py` and its provider in `core/container.py`
- When a check fails, change the code to fit the structure — never loosen `tach.toml`, a `tach.domain.toml`, the structure test or a lint rule to make it pass. A genuinely new kind of file (e.g. `models.py` once a DB lands) gets its own `tach.toml` module entry — ask first
- After editing files, trust `uv run tach check` over the editor: the Tach extension doesn't see disk changes until the file is reopened or **Tach: Restart Server** runs
- Not caught by any tool, so keep it by hand: routers hold no business logic

## Rules

1. **NESTJS-STYLE STRUCTURE** — see the section above
2. **REPOSITORY PATTERN** — all DB/Redis access goes through repositories; no queries in services
3. **DI THROUGH DISHKA** — register each feature's `Provider` in `core/container.py`; routers use `route_class=DishkaRoute` and take `FromDishka[Service]`; request-scoped objects (DB session, current user) come from providers, never built in a route. FastAPI `Depends` only for request decomposition (query/header params such as pagination) — never to build services or repositories
4. **ABSOLUTE IMPORTS** — `from src.app.X import Y`; relative imports only in `__init__.py`
5. **RETURN TYPES, NOT `response_model=`** — FastAPI uses the route's return annotation as the response model (Ruff `FAST001` flags the duplicate)
6. **FIELD DESCRIPTIONS** — every Pydantic `Field()` has `description=` (OpenAPI docs)
7. **LOGGING** — `from src.app.core.logger import logger` (Ruff bans importing `loguru` elsewhere); `{}` placeholders, never f-strings; `logger.exception()` inside `except`. Log external calls, DB writes, exceptions and state changes — never loops or plain reads
8. **ERRORS** — services raise domain exceptions, never `HTTPException`; when the first domain exception is added, register one exception handler in `main.py` that maps them to HTTP status codes
9. **SECRETS** — only through `Settings` (`SecretStr`); never hard-coded, logged or committed (`.env` is git-ignored)
10. **UTC** — store and compare datetimes in UTC; convert to the user's timezone only for display
11. **NO `api/` FOLDER** — feature routers are registered directly in `main.py`

## Tests

- `tests/` mirrors `src/app/features/`
- `@pytest.mark.unit` (no DB) or `@pytest.mark.integration` (real DB/Redis, rolled back after each test) — never mock the DB in integration tests
- Never call external APIs or LLMs in tests — mock them
