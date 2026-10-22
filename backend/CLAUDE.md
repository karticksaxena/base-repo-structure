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
  main.py                 # app factory: logger, routers, dishka (Nest main.ts)
  app_module.py           # root module (Nest AppModule): dishka container with every feature's Provider
  core/                   # app-wide setup: config, logger (+ database, redis) — never imports a feature
  common/                 # shared by 2+ features: schemas.py (BaseSchema, Page[T]), base repositories, domain errors (NestJS common/)
  features/<name>/        # one NestJS module per domain
    __init__.py
    routers/              # HTTP only (Nest controllers); __init__.py combines them into one `router`
    services/             # business logic (Nest services)
    repositories/         # data access — the only layer that touches the database or Redis
    schemas/              # Pydantic request/response models (Nest DTOs)
    constants/            # fixed values used only by this feature (limits, mappings, enums)
    utils/                # small helpers used only by this feature (formatting, transforming) — no business logic
    models/               # SQLAlchemy models (Nest entities) — once a database exists
    dependencies.py       # dishka Provider (Nest module providers)
    tach.domain.toml      # this feature's layer rules — identical in every feature
```

Every layer folder is a package (`__init__.py`) holding one module per use-case area (`services/items.py`, `services/item_exports.py`).

| Rule                                                                                                                                                                                                                          | Enforced by                                               | Shows up                                                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Every feature has `__init__.py`, `routers/`, `services/`, `repositories/`, `schemas/`, `constants/`, `utils/`, `dependencies.py`, `tach.domain.toml` — and nothing else                                                       | `tests/test_structure.py`                                 | task `backend: test`, pre-commit hook                                                 |
| Nothing in `src/` outside this layout; every `core/` file has a module in `tach.toml`                                                                                                                                         | `tests/test_structure.py`                                 | same                                                                                  |
| Every feature's `tach.domain.toml` is identical to `features/items/tach.domain.toml`                                                                                                                                          | `tests/test_structure.py`                                 | same                                                                                  |
| Every feature has `tests/features/<name>/test_*.py`                                                                                                                                                                           | `tests/test_structure.py`                                 | same                                                                                  |
| Imports go routers → services → repositories only — no skipping, nothing upward (also inside functions and under `if TYPE_CHECKING:`)                                                                                         | tach (`tach.domain.toml`)                                 | live in open files (source `tach`), task `backend: structure (tach)`, pre-commit hook |
| Another feature is used only through its `services` (or `schemas`); only `*Service` classes leave `services/`                                                                                                                 | tach (`tach.domain.toml`, `[[interfaces]]`)               | same                                                                                  |
| `constants/` imports nothing in the feature and every layer may read it; `utils/` uses only `schemas/` and `constants/` (+ `models/` once a database exists); neither is visible to other features                            | tach (`tach.domain.toml`)                                 | same                                                                                  |
| FastAPI/Starlette only in routers, `dependencies.py`, `main.py`, `app_module.py`, `core/`, `common/`                                                                                                                          | `tach check-external` (`cannot_depend_on_external`)       | task `backend: structure (tach)`, pre-commit hook                                     |
| Only `app_module.py` imports feature providers (`dependencies.py`) and nothing but `main.py` imports it; `main.py` imports only `app_module.py`, the logger and feature routers; `core/` and `common/` never import a feature | tach (`tach.toml`)                                        | live, task, pre-commit hook                                                           |
| No import cycles between files                                                                                                                                                                                                | BasedPyright `reportImportCycles`                         | live, whole workspace                                                                 |
| Features never import each other in a loop, even through different files (`items` → `orders` → `items`)                                                                                                                       | import-linter (`[tool.importlinter]` in `pyproject.toml`) | task `backend: feature cycles (import-linter)`, pre-commit hook                       |
| `*Service(...)` / `*Repository(...)` are built only in a feature's `dependencies.py` (tests may build them)                                                                                                                   | pylint plugin `tests/pylint_construction.py` (`E9001`)    | live (Pylint), task `backend: pylint (file length, construction)`, pre-commit hook    |
| No `sqlalchemy` / `redis` imports outside repositories, models, `dependencies.py` and `core/` (once added)                                                                                                                    | Ruff `TID251`                                             | live, task, pre-commit hook                                                           |
| No way around the checks: no `# tach-ignore`, `# noqa: TID…`, `reportImportCycles` ignores, `# pylint: disable` / `skip-file`, `__import__` / `importlib.import_module`, blanket `# noqa` / `# type: ignore`                  | `tests/test_structure.py`, Ruff `TID251` + `PGH`          | live (Ruff), task, pre-commit hook                                                    |

### Where code goes

- HTTP (paths, status codes, request parsing) → `routers/`; business rules → `services/`; database, Redis or other data sources → `repositories/`
- Request/response shapes → `schemas/`; fixed values and enums → `constants/`; small pure helpers → `utils/`
- Used by one feature → stays in that feature; needed by a second feature → move it to `common/`; app-wide setup → `core/` — never import another feature's internals

### Adding a feature (`orders`)

1. `cp -R src/app/features/items src/app/features/orders` — every folder, `__init__.py` and `tach.domain.toml` comes along; never edit the copied `tach.domain.toml`
2. Rename the modules in each layer folder (`routers/items.py` → `routers/orders.py`, …), the classes (`ItemService` → `OrderService`, …) and **every import** (tach rejects any import still pointing at `items`); keep every folder, even an empty `constants/` or `utils/`
3. Point `routers/__init__.py` at the new router module; register the router in `main.py` and the provider in `app_module.py`
4. Add `tests/features/orders/test_*.py`
5. Run every check (`../SETUP.md` → Verify CLI) — done only when all pass

### Changing the layer rules (ask first)

Edit `features/items/tach.domain.toml`, then copy it to every feature: `find src/app/features -mindepth 1 -maxdepth 1 -type d ! -name items ! -name __pycache__ -exec cp src/app/features/items/tach.domain.toml {}/ \;`. A new kind of folder (e.g. `tasks/`, `listeners/`, `grpc/`) also goes into `REQUIRED_PACKAGES` in `tests/test_structure.py` and into every feature.

### When a check fails

- Change the code to fit the structure — never loosen `tach.toml`, a `tach.domain.toml`, the structure test or a lint rule, never add `# tach-ignore` / `# noqa: TID…`, and **never run `tach sync`** (tach suggests it; it rewrites the rules to allow whatever the code imports)
- `lint-imports` names only the two features (`.orders -> .items (1 import)`); find the import with `grep -rn 'features\.items' src/app/features/orders` and break the loop: move what both need to `common/`, or let only one feature call the other. Never add `ignore_imports` to `[tool.importlinter]`
- `E9001 … built outside dependencies.py`: take the object as an `__init__` parameter and build it in the feature's `dependencies.py` Provider. pylint loads the plugin from `tests/`, so it runs from `backend/` (the editor and every check already do)
- Trust `uv run tach check` over the editor after editing files: the Tach extension doesn't see disk changes until the file is reopened or **Tach: Restart Server** runs
- Not caught by any tool, so keep it by hand:
  - routers hold no business logic
  - services and repositories are built only in `dependencies.py`, however the call is written — the pylint plugin matches `*Service(` / `*Repository(` by name, so an alias (`Repo = ItemRepository; Repo()`), `type(x)()`, `cls()` in a factory classmethod or `getattr(module, "ItemRepository")()` slips past it but still breaks the rule

## Rules

1. **NESTJS-STYLE STRUCTURE** — see the section above
2. **REPOSITORY PATTERN** — all DB/Redis access goes through `repositories/`; no queries in services. Once a database exists (`../SETUP.md` → Database pattern): models in `models/`, inheriting `Base` (UUIDv7 `id`, UTC timestamps, soft delete — never redeclare them); every database repository inherits `RepositoryBase` (`common/repository.py`) and adds only its own queries, starting from `base_statement()` (hides soft-deleted rows); delete with `soft_delete()`; repositories flush, never commit — the session provider in `core/database.py` commits on success and rolls back on error; no unbounded queries (`paginate` + `count`); services return Pydantic schemas, never ORM objects. Once Redis exists (`../SETUP.md` → Redis pattern): one app-wide client from `core/redis.py`; cached reads go through a `Cached<X>Repository` (inherits `CachedRepositoryBase`, `common/cached_repository.py`) — cache-aside, and the service **invalidates after every write**; other Redis use inherits `RedisRepositoryBase` (`common/redis_repository.py`); keys always via `self.key(...)` with a TTL
3. **DI THROUGH DISHKA** — register each feature's `Provider` in `app_module.py` (the root module, like Nest's `AppModule`); routers use `route_class=DishkaRoute` and take `FromDishka[Service]`; request-scoped objects (DB session, current user) come from providers, never built in a route. FastAPI `Depends` only to group request parameters (headers, query) — never to build services or repositories; pagination uses `Limit` / `Offset` from `common/schemas.py`
4. **ABSOLUTE IMPORTS** — `from src.app.X import Y`; relative imports only in `__init__.py`
5. **RETURN TYPES, NOT `response_model=`** — every route declares its return type (a schema, `Page[T]` or `None`): FastAPI validates the result and Pydantic serializes it to JSON in Rust (2x+ faster). For a JSON body return the schema — never wrap it in `JSONResponse`, `jsonable_encoder` or `response_class=` (each skips that path); `ORJSONResponse` / `UJSONResponse` are deprecated; `Response` subclasses only for non-JSON (files, redirects, streams); `response_model=` duplicates the annotation (Ruff `FAST001`). JSON requests need `Content-Type: application/json` (FastAPI's default `strict_content_type` — keep it on)
6. **SCHEMAS (Pydantic v2 API only)** — every schema inherits `BaseSchema` (`common/schemas.py`: unknown fields rejected); config via `model_config: ClassVar[ConfigDict]`; `model_validate()` / `model_dump()`, and `model_validate(obj, from_attributes=True)` for ORM objects — never `class Config`, `.dict()`, `.parse_obj()`, `orm_mode` or `pydantic.v1` (FastAPI dropped Pydantic v1; BasedPyright and pytest fail on the deprecated API); every `Field()` has `description=` (OpenAPI docs); every list endpoint takes `limit: Limit = 20, offset: Offset = 0` and returns `Page[T]`
7. **LOGGING** — `from src.app.core.logger import logger` (Ruff bans importing `loguru` elsewhere); `{}` placeholders, never f-strings; `logger.exception()` inside `except`. Log external calls, DB writes, exceptions and state changes — never loops or plain reads
8. **ERRORS** — services raise domain exceptions, never `HTTPException`; when the first domain exception is added, register one exception handler in `main.py` that maps them to HTTP status codes
9. **SECRETS** — only through `Settings` (`SecretStr`); never hard-coded, logged or committed (`.env` is git-ignored)
10. **UTC** — store and compare datetimes in UTC; convert to the user's timezone only for display
11. **NO `api/` FOLDER** — feature routers are registered directly in `main.py`
12. **PERFORMANCE — RESEARCH FIRST** — before choosing a library, pattern or setting, use the **`grounded-research`** skill to find the fastest production-proven option for the installed versions (never from memory); measure before and after optimizing. Defaults:
    - `async def` routes await only async I/O — a blocking library goes in a `def` route (FastAPI runs it in a threadpool) or is replaced by an async one; CPU-heavy work goes to a background job or more workers, never into the request
    - Raw JSON → `Model.model_validate_json(raw)` (not `json.loads` + `model_validate`); a `TypeAdapter` is built once at module level; tagged (discriminated) unions over plain unions
    - Database: `lazy="raise"` on relationships + `selectinload()` (no N+1); bulk inserts as one list; select only the columns a large list needs; paginate everything
    - One client/pool per external service for the whole app (dishka `Scope.APP`); `Scope.REQUEST` only for per-request state; Redis `pipeline()` for batches
    - Production: `--workers` = CPU cores on Granian (default) or uvicorn (one worker per container under an orchestrator); stay on the GIL build of Python and off the experimental JIT until their support is production-ready
    - Speed comes from Pydantic's Rust core, Granian, asyncpg and query design — dishka and SQLAlchemy are chosen for structure, not speed
13. **HTTP API DESIGN** — the URL names the record; the body carries the change:
    - Path: plural nouns and ids only (`/orders/{order_id}`), no verbs
    - Query: filters, sorting, `limit` / `offset` — on `GET` only
    - Body: create/update data as a schema; none on `GET` or `DELETE`
    - Headers: auth and request metadata (`Idempotency-Key`), never business data
    - Methods: `GET` reads · `POST /orders` creates (201) · `PATCH /orders/{order_id}` updates the fields sent · `DELETE /orders/{order_id}` deletes (204); `PUT` only to replace a whole record
    - Never secrets or personal data in the path or query — servers, proxies and browsers log URLs (RFC 9110 §17.9)
    - The acting user comes from auth (a dishka provider), never from a header the client sets
    - A `POST` that must be safe to retry (payments) takes an `Idempotency-Key`; add it only when an endpoint needs it
    - Route function names are `<verb>_<noun>` (`list_items`, `create_order`) and unique across the app — once Hey API is added they become the OpenAPI operation ids and the frontend's function names (`listItems`), and `tests/test_openapi.py` fails on a duplicate

## Tests

- `tests/` mirrors `src/app/features/` — every feature has `tests/features/<name>/test_*.py` (the structure test checks it)
- `@pytest.mark.unit` (no DB) or `@pytest.mark.integration` (real DB/Redis, rolled back after each test) — never mock the DB in integration tests
- Never call external APIs or LLMs in tests — mock them
