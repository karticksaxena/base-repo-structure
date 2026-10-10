# Backend Coding Rules

## Dev tooling

Follow **`../SETUP.md`**. Every lint, type, size and structure rule lives in `pyproject.toml` — never in `.vscode/settings.json`, and never in a separate `pyrightconfig.json`, `.flake8`, `.pylintrc` or `tach.toml`.

## Stack

FastAPI · Pydantic + pydantic-settings · **dishka** (DI) · **loguru** (logging) · pytest · `uv` (package manager, never pip) · Python from `.python-version`

Added only when a feature needs them (`../SETUP.md` → Libraries by use case): **SQLAlchemy** (async ORM) + asyncpg · Alembic (migrations) · redis · httpx2 (outgoing HTTP)

Always the latest stable, mutually compatible versions — never prereleases, never versions hardcoded in docs.

## Rules

1. **NESTJS-STYLE FEATURES** — one folder per domain in `src/app/features/<name>/` with `router.py` (HTTP only, Nest controller), `service.py` (logic), `repository.py` (data access), `schemas.py` (Pydantic DTOs), `dependencies.py` (dishka `Provider`, Nest module providers). `tests/test_structure.py` fails when a file is missing
2. **LAYERS** — router → service → repository, never skipped or reversed; another feature is used only through its service. Enforced by tach (`[tool.tach]`); a new kind of module gets a tach entry, never a looser rule
3. **REPOSITORY PATTERN** — all DB/Redis access goes through repositories; no queries in services
4. **DI THROUGH DISHKA** — register each feature's `Provider` in `core/container.py`; routers use `route_class=DishkaRoute` and take `FromDishka[Service]`; request-scoped objects (DB session, current user) come from providers, never built in a route
5. **ABSOLUTE IMPORTS** — `from src.app.X import Y`; relative imports only in `__init__.py`
6. **RETURN TYPES, NOT `response_model=`** — FastAPI uses the route's return annotation as the response model (Ruff `FAST001` flags the duplicate)
7. **FIELD DESCRIPTIONS** — every Pydantic `Field()` has `description=` (OpenAPI docs)
8. **LOGGING** — `from src.app.core.logger import logger` (Ruff bans importing `loguru` elsewhere); `{}` placeholders, never f-strings; `logger.exception()` inside `except`. Log external calls, DB writes, exceptions and state changes — never loops or plain reads
9. **ERRORS** — services raise domain exceptions, never `HTTPException`; one handler in `main.py` maps them to HTTP status codes
10. **SECRETS** — only through `Settings` (`SecretStr`); never hard-coded, logged or committed (`.env` is git-ignored)
11. **UTC** — store and compare datetimes in UTC; convert to the user's timezone only for display
12. **NO `api/` FOLDER** — feature routers are registered directly in `main.py`

## Tests

- `tests/` mirrors `src/app/features/`
- `@pytest.mark.unit` (no DB) or `@pytest.mark.integration` (real DB/Redis, rolled back after each test) — never mock the DB in integration tests
- Never call external APIs or LLMs in tests — mock them
