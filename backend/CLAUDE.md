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
  core/                   # app-wide setup: config, logger, container (+ database, redis) — never imports a feature
  common/                 # shared by 2+ features: schemas.py (BaseSchema, Page[T]), base repositories, domain errors (NestJS common/)
  features/<name>/        # one NestJS module per domain
    __init__.py
    routers/              # HTTP only (Nest controllers); __init__.py combines them into one `router`
    services/             # business logic (Nest services)
    repositories/         # data access — the only layer that touches the database or Redis
    schemas/              # Pydantic request/response models (Nest DTOs)
    models/               # SQLAlchemy models (Nest entities) — once a database exists
    dependencies.py       # dishka Provider (Nest module providers)
    tach.domain.toml      # this feature's layer rules (copied with the folder)
```

Every layer folder is a package (`__init__.py`) holding one module per use-case area (`services/items.py`, `services/item_exports.py`).

| Rule                                                                                                                         | Enforced by                       | Shows up                                                                              |
| ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------- |
| Every feature has `__init__.py`, `routers/`, `services/`, `repositories/`, `schemas/`, `dependencies.py`, `tach.domain.toml` | `tests/test_structure.py`         | `uv run pytest`, task `backend: test`, pre-commit hook                                |
| Imports go routers → services → repositories only — no skipping, nothing upward                                              | tach (`tach.domain.toml`)         | live in open files (source `tach`), task `backend: structure (tach)`, pre-commit hook |
| Another feature is used only through its `services` (or `schemas`) — never its repositories, routers or dependencies         | tach (`tach.domain.toml`)         | same                                                                                  |
| `core/` never imports a feature (only `container.py` imports feature providers)                                              | tach                              | same                                                                                  |
| `common/` is shared by everyone and never imports a feature (or `core/container.py`)                                         | tach (`tach.toml`)                | same                                                                                  |
| Every file belongs to one of the folders above (`root_module = "forbid"`)                                                    | tach                              | same                                                                                  |
| No import cycles                                                                                                             | BasedPyright `reportImportCycles` | live, whole workspace                                                                 |
| No `sqlalchemy` / `redis` imports outside repositories, models, `dependencies.py` and `core/` (once added)                   | Ruff `TID251`                     | live, task, pre-commit hook                                                           |

- Shared code moves to `common/` only when a second feature needs it — never a feature importing another feature's internals
- Add a feature by copying `features/items/` (its `tach.domain.toml` comes along), renaming the modules inside the layer folders, then registering its `router` in `main.py` and its provider in `core/container.py`
- When a check fails, change the code to fit the structure — never loosen `tach.toml`, a `tach.domain.toml`, the structure test or a lint rule to make it pass. A genuinely new kind of folder gets its own tach module entry — ask first
- After editing files, trust `uv run tach check` over the editor: the Tach extension doesn't see disk changes until the file is reopened or **Tach: Restart Server** runs
- Not caught by any tool, so keep it by hand: routers hold no business logic

## Rules

1. **NESTJS-STYLE STRUCTURE** — see the section above
2. **REPOSITORY PATTERN** — all DB/Redis access goes through `repositories/`; no queries in services. Once a database exists (`../SETUP.md` → Database pattern): models in `models/`, inheriting `Base` (UUIDv7 `id`, UTC timestamps, soft delete — never redeclare them); every database repository inherits `RepositoryBase` (`common/repository.py`) and adds only its own queries, starting from `base_statement()` (hides soft-deleted rows); delete with `soft_delete()`; repositories flush, never commit — the session provider in `core/database.py` commits on success and rolls back on error; no unbounded queries (`paginate` + `count`); services return Pydantic schemas, never ORM objects. Once Redis exists (`../SETUP.md` → Redis pattern): one app-wide client from `core/redis.py`; cached reads go through a `Cached<X>Repository` (inherits `CachedRepositoryBase`, `common/cached_repository.py`) — cache-aside, and the service **invalidates after every write**; other Redis use inherits `RedisRepositoryBase` (`common/redis_repository.py`); keys always via `self.key(...)` with a TTL
3. **DI THROUGH DISHKA** — register each feature's `Provider` in `core/container.py`; routers use `route_class=DishkaRoute` and take `FromDishka[Service]`; request-scoped objects (DB session, current user) come from providers, never built in a route. FastAPI `Depends` only to group request parameters (headers, query) — never to build services or repositories; pagination uses `Limit` / `Offset` from `common/schemas.py`
4. **ABSOLUTE IMPORTS** — `from src.app.X import Y`; relative imports only in `__init__.py`
5. **RETURN TYPES, NOT `response_model=`** — every route declares its return type (a schema, `Page[T]` or `None`): FastAPI validates the result and Pydantic serializes it to JSON in Rust (2x+ faster). For a JSON body return the schema — never wrap it in `JSONResponse`, `jsonable_encoder` or `response_class=` (each skips that path); `ORJSONResponse` / `UJSONResponse` are deprecated; `Response` subclasses only for non-JSON (files, redirects, streams); `response_model=` duplicates the annotation (Ruff `FAST001`). JSON requests need `Content-Type: application/json` (FastAPI's default `strict_content_type` — keep it on)
6. **SCHEMAS (Pydantic v2 API only)** — every schema inherits `BaseSchema` (`common/schemas.py`: unknown fields rejected); config via `model_config: ClassVar[ConfigDict]`; `model_validate()` / `model_dump()`, and `model_validate(obj, from_attributes=True)` for ORM objects — never `class Config`, `.dict()`, `.parse_obj()`, `orm_mode` or `pydantic.v1` (FastAPI dropped Pydantic v1; BasedPyright and pytest fail on the deprecated API); every `Field()` has `description=` (OpenAPI docs); every list endpoint takes `limit: Limit = 20, offset: Offset = 0` and returns `Page[T]`
7. **LOGGING** — `from src.app.core.logger import logger` (Ruff bans importing `loguru` elsewhere); `{}` placeholders, never f-strings; `logger.exception()` inside `except`. Log external calls, DB writes, exceptions and state changes — never loops or plain reads
8. **ERRORS** — services raise domain exceptions, never `HTTPException`; when the first domain exception is added, register one exception handler in `main.py` that maps them to HTTP status codes
9. **SECRETS** — only through `Settings` (`SecretStr`); never hard-coded, logged or committed (`.env` is git-ignored)
10. **UTC** — store and compare datetimes in UTC; convert to the user's timezone only for display
11. **NO `api/` FOLDER** — feature routers are registered directly in `main.py`

## Tests

- `tests/` mirrors `src/app/features/`
- `@pytest.mark.unit` (no DB) or `@pytest.mark.integration` (real DB/Redis, rolled back after each test) — never mock the DB in integration tests
- Never call external APIs or LLMs in tests — mock them
