# Dev Tooling Setup Guide

Production-ready linting, formatting, type-checking, size limits, structure checks and tests for a monorepo: a **FastAPI** backend (Python, `uv`, NestJS-style feature modules, dishka DI, loguru) and a **Next.js** frontend (oxlint, Prettier, Vitest). Use this checklist when bootstrapping a new project from this repo.

**Path:** `SETUP.md` (repo root). Point agents here for editor + CLI tooling setup. The TypeScript-backend twin of this repo is `base-repo-ts` (NestJS + Next.js); the frontend section below is shared with it.

---

## For AI agents — read this first

1. **Three-layer rule** — rules live in config files (`backend/pyproject.toml`, `backend/tach.toml`, `frontend/.oxlintrc.json`, `frontend/.prettierrc`, `frontend/tsconfig.json`); editor wiring **and format-on-save** live in the committed `.vscode/settings.json`; the only user setting is `files.autoSave`.
2. **One package manager per side** — `uv` for Python (never pip, poetry or a bare `python -m venv`); `pnpm` for the frontend (never npm or yarn). Commit `uv.lock`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`.
3. **Latest stable versions, never pinned in docs** — `uv add <pkg>` / `pnpm add <pkg>@latest` without a version; never a prerelease. If the newest major of one tool breaks another, use the newest major that passes [Verify CLI](#verify-cli) **and** [Verify editor](#verify-editor-smoke-test--delete-after), and record why in [Troubleshooting](#troubleshooting) (current case: TypeScript stays on 6).
4. **Bare defaults** — backend = `main.py` + `core/` + one sample feature; frontend = `create-next-app` default. Add a library only when a feature needs it ([Libraries by use case](#libraries-by-use-case)).
5. **Size limits are lint rules, not advice** — files ≤ **500** lines, functions ≤ **100** lines, as **errors**, in backend and frontend. When one fires, split the file or function — never raise the limit, never add a disable comment.
6. **Structure is a lint rule** — every backend feature has the same files (`tests/test_structure.py`) and imports only in the router → service → repository direction (tach, `backend/tach.toml`). A new kind of module gets its own tach entry; never loosen `root_module = "forbid"`.
7. **Check the editor, not just the CLI** — the smoke tests must show the same problems in the VS Code Problems panel as the CLI. A setting that was never seen working in the editor is a guess.
8. **Install the VS Code extensions yourself** ([Required extensions](#required-vs-code-extensions)) and uninstall Pylance; then ask the user to reload the window — batch every reload/open request into one message.
9. **Do not use** settings that don't exist or are deprecated: `ruff.cwd`, `ruff.lint.run`, `ruff.lint.select` / `ruff.lineLength` / `ruff.configuration` (they override `pyproject.toml`), `python.analysis.*` (Pylance only), `cursorpyright.*`, `typescript.tsdk` / `typescript.enablePromptUseWorkspaceTsdk` (use `js/ts.tsdk.path` / `js/ts.tsdk.promptToUseWorkspaceVersion`).
10. **Never put `options` (e.g. `typeAware`) in `frontend/.oxlintrc.json`** — VS Code opens the repo root, so that config is _nested_, and oxlint rejects root-only options there; the editor then silently drops the whole config. Type-aware linting comes from `--type-aware` in the `lint` script (CLI) and `oxc.typeAware` + `oxc.path.tsgolint` in `.vscode/settings.json` (editor).
11. **Ask before adding application-specific setup** — the items in [Application-specific setup](#application-specific-setup--ask-the-user-first) depend on what is being built. List the relevant ones, explain each in a line, and add only what the user approves. Tooling (linters, formatters, type strictness, the structure checks) is not on that list — set it up as this guide says.

### What runs where (verified)

| Check                                | Tool                                                      | Rules in                           | Problems panel while editing                             | Whole-workspace scan                     |
| ------------------------------------ | --------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------- | ---------------------------------------- |
| Python lint                          | Ruff                                                      | `pyproject.toml`                   | open files                                               | task `backend: ruff`                     |
| Python format + import order         | Ruff (format on save)                                     | `pyproject.toml`                   | on save                                                  | task `backend: format`                   |
| Python types                         | BasedPyright (`recommended`)                              | `pyproject.toml`                   | **every file**, open or not                              | task `backend: basedpyright`             |
| Function ≤ 100 lines (py)            | flake8 + `flake8-max-function-length`                     | `pyproject.toml` (`[tool.flake8]`) | open files                                               | task `backend: function length (flake8)` |
| File ≤ 500 lines (py)                | pylint, only `too-many-lines`                             | `pyproject.toml`                   | open files                                               | task `backend: file length (pylint)`     |
| Layers router → service → repository | tach                                                      | `backend/tach.toml`                | open files (Tach extension)                              | task `backend: structure (tach)`         |
| Feature has all files                | pytest `tests/test_structure.py`                          | the test                           | —                                                        | task `backend: test`                     |
| No import cycles                     | BasedPyright `reportImportCycles` (part of `recommended`) | `pyproject.toml`                   | **every file**, open or not                              | task `backend: basedpyright`             |
| TS/TSX lint, size limits             | oxlint (type-aware)                                       | `frontend/.oxlintrc.json`          | open files                                               | task `frontend: lint`                    |
| TS types                             | `tsc` / VS Code TypeScript                                | `frontend/tsconfig.json`           | every file of a project once one of its files was opened | task `frontend: typecheck`               |
| Format JS/TS/JSON/CSS/MD/YAML        | Prettier (format on save)                                 | `frontend/.prettierrc`             | on save                                                  | task `frontend: format`                  |
| Format TOML                          | Even Better TOML                                          | defaults                           | on save                                                  | —                                        |

VS Code has **no global "lint the whole workspace" setting** — each extension decides. Only BasedPyright (`basedpyright.analysis.diagnosticMode: "workspace"`) and TypeScript (`js/ts.tsserver.experimental.enableProjectDiagnostics`) scan files you haven't opened. For everything else, **Tasks → `check: all`** runs every CLI check and puts every file's problems in the Problems panel. **Empty Problems panel = clean code** when the CLI passes.

---

## Architecture: three layers

| Layer              | Location                                                                                                                   | Purpose                                                                    | Commit? |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------- |
| **Rules**          | `backend/pyproject.toml`, `backend/tach.toml`, `frontend/.oxlintrc.json`, `frontend/.prettierrc`, `frontend/tsconfig.json` | What to enforce — shared by CLI and editor                                 | Yes     |
| **Project wiring** | `.vscode/settings.json`, `extensions.json`, `tasks.json`                                                                   | Interpreter/tool paths, workspace diagnostics, formatters + format-on-save | Yes     |
| **Personal prefs** | VS Code user `settings.json`                                                                                               | `files.autoSave` only                                                      | No      |

**Golden rule:** lint, type and format **rules** live in config files, never in VS Code settings.

---

## Application-specific setup — ask the user first

This template stays bare on purpose. The items below are what production FastAPI / Next.js apps commonly add (seen in Polar, Onyx, Sentry, the FastAPI full-stack template, cal.com, Dub, Supabase, create-t3-app), but whether and how depends on the application. **When setting up a new project, ask the user about each relevant item before adding it.**

| Side     | Item                                             | What it is                                                                                                                          | Typical trigger                                    |
| -------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| backend  | `/health` (+ `/health/ready`)                    | liveness/readiness endpoint for load balancers and orchestrators                                                                    | the app gets deployed                              |
| backend  | Request-ID middleware                            | an `X-Request-ID` per request, bound into every log line (`logger.contextualize`)                                                   | more than one service, or log search in production |
| backend  | Error contract                                   | one `AppError` base class + one handler in `main.py` → one JSON error shape                                                         | the first domain error                             |
| backend  | Production settings                              | `env` setting (dev/test/prod), OpenAPI docs off in prod, `SecretStr` secrets, `env_prefix`                                          | the first deployment                               |
| backend  | CORS                                             | `CORSMiddleware` with a `cors_origins` setting (never `*`)                                                                          | the browser calls the backend directly             |
| backend  | Security headers, body-size limit, rate limiting | HSTS / body limits (often done by the proxy); Redis-backed rate limits                                                              | public endpoints, auth                             |
| backend  | Database                                         | SQLAlchemy async + asyncpg + Alembic, test DB with rollback per test (see [Libraries by use case](#7-libraries-by-use-case))        | the first persisted data                           |
| backend  | Observability                                    | Sentry (only when a DSN is set), OpenTelemetry / Logfire, or structlog instead of loguru                                            | production monitoring                              |
| backend  | Docker                                           | multi-stage image with uv (`uv sync --locked --no-dev`), non-root `USER`, `fastapi run`                                             | container deployment                               |
| backend  | Test extras                                      | `pytest-cov` with a threshold, `pytest-xdist`                                                                                       | the suite grows or slows                           |
| backend  | Supply-chain cooldown                            | `[tool.uv] exclude-newer = "1 week"` — skip brand-new releases                                                                      | team policy                                        |
| frontend | Security headers / CSP                           | `headers()` in `next.config.ts`: `X-Content-Type-Options`, `Referrer-Policy`, frame protection, `poweredByHeader: false`; CSP later | the app gets deployed                              |
| frontend | Env validation                                   | `@t3-oss/env-nextjs` + Zod: build fails on a missing/invalid env var                                                                | the first env var                                  |
| frontend | `typedRoutes`                                    | `next.config.ts` `typedRoutes: true`: `<Link href>` checked against real routes                                                     | more than a few routes                             |
| frontend | Observability                                    | Sentry / `instrumentation.ts` `onRequestError`                                                                                      | production monitoring                              |
| frontend | E2E tests                                        | Playwright                                                                                                                          | real user flows exist                              |
| frontend | Extras                                           | `server-only` package (data layer), bundle analyzer, knip (unused code), React Compiler                                             | when the need shows up                             |
| both     | `.editorconfig`                                  | shared indent / line-ending defaults for editors without per-language formatters                                                    | contributors use other editors                     |

---

## Required VS Code extensions

| Extension        | ID                         | Role                                                       |
| ---------------- | -------------------------- | ---------------------------------------------------------- |
| Python           | `ms-python.python`         | Interpreter selection (required by Flake8/Pylint)          |
| BasedPyright     | `detachhead.basedpyright`  | Python types (LSP), whole workspace                        |
| Ruff             | `charliermarsh.ruff`       | Python lint + format + import sorting                      |
| Flake8           | `ms-python.flake8`         | Function length (`MFL000`)                                 |
| Pylint           | `ms-python.pylint`         | File length (`C0302`)                                      |
| Tach             | `gauge.tach`               | Layer violations (tach language server)                    |
| Oxc              | `oxc.oxc-vscode`           | oxlint diagnostics + fix-on-save                           |
| Prettier         | `esbenp.prettier-vscode`   | Formatting (uses the project's `prettier` + `.prettierrc`) |
| Even Better TOML | `tamasfe.even-better-toml` | TOML formatting (`pyproject.toml`)                         |

Not wanted: **Pylance** (`ms-python.vscode-pylance` — clashes with BasedPyright; the Python extension installs it as part of its pack, so uninstall it after installing Python) and **ESLint** (this repo uses oxlint). The Tach extension's last release is old (Feb 2025) but it only launches `python -m tach server -c backend/tach.toml` from `backend/.venv`, so it runs the current tach (verified). `httpx2`, `pytest-asyncio` and `flake8-pyproject` are libraries/plugins, not editor tools.

Install from a terminal (macOS; the `code` command may not be on `PATH`):

```bash
CODE="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
for ext in ms-python.python detachhead.basedpyright charliermarsh.ruff ms-python.flake8 \
           ms-python.pylint gauge.tach oxc.oxc-vscode esbenp.prettier-vscode tamasfe.even-better-toml; do
  "$CODE" --install-extension "$ext"
done
"$CODE" --uninstall-extension ms-python.vscode-pylance
```

Then **Cmd+Shift+P → Developer: Reload Window** and **Python: Select Interpreter → `backend/.venv/bin/python`**. VS Code auto-selects a global Python if the folder was opened before `backend/.venv` existed, and `python.defaultInterpreterPath` does not override that choice.

---

## Backend (FastAPI + uv)

### 1. Python and uv

```bash
brew install uv || brew upgrade uv     # an old uv doesn't know the newest Python release
uv python install 3.15                 # the newest stable CPython; check python.org first
cd backend
echo 3.15 > .python-version
```

Keep `.python-version`, `requires-python`, `pythonVersion` (BasedPyright) and `target-version` (Ruff) on the same version.

### 2. Dependencies

```bash
uv add fastapi uvicorn pydantic-settings loguru dishka
uv add --dev ruff basedpyright pytest pytest-asyncio httpx2 \
  flake8 flake8-max-function-length flake8-pyproject pylint tach pip-audit
```

- `httpx2` — Starlette's `TestClient` now imports `httpx2` (Pydantic's successor to `httpx`) and warns `Using httpx with starlette.testclient is deprecated; install httpx2 instead` when only `httpx` is installed.
- `flake8-pyproject` — flake8 can't read `pyproject.toml` on its own (verified: settings in `[tool.flake8]` are ignored without it). The plugin reads `pyproject.toml` from the **current directory**, which is why `flake8.cwd` points at `backend/`.
- `pip-audit` (PyPA) checks the installed packages against known vulnerabilities — the backend twin of `pnpm audit`. uv 0.13 also has `uv audit`, but it is marked experimental (`uv audit is experimental and may change without warning`), so it isn't used.
- No `[build-system]`: the backend is an app, not a package, so `uv` installs only its dependencies; imports resolve from `backend/` (`from src.app…`).

### 3. `backend/pyproject.toml` — all rules

Copy this block below `[dependency-groups]`:

```toml
# --- Type checking (BasedPyright) ---
[tool.basedpyright]
pythonVersion = "3.15"           # match .python-version
typeCheckingMode = "recommended"
failOnWarnings = true
include = ["src", "tests"]
venvPath = "."                   # editor and CLI resolve imports from the same venv
venv = ".venv"

# --- Lint + format (Ruff) ---
[tool.ruff]
target-version = "py315" # match pythonVersion
line-length = 100

[tool.ruff.lint]
select = [
  "E",
  "W",     # pycodestyle
  "F",     # pyflakes
  "I",     # isort
  "UP",    # pyupgrade
  "B",     # flake8-bugbear
  "C4",    # flake8-comprehensions
  "G",     # flake8-logging-format
  "SIM",   # flake8-simplify
  "TID",   # tidy imports: no relative imports, banned APIs
  "S",     # security (bandit)
  "ANN",   # annotations
  "FAST",  # FastAPI
  "ASYNC", # async pitfalls
  "T20",   # no print()
  "PT",    # pytest style
  "RUF",   # Ruff-specific (incl. RUF100: unused noqa)
  "PIE",   # misc. lints
  "PERF",  # performance anti-patterns
  "FURB",  # refurb: modern idioms
  "DTZ",   # timezone-naive datetimes
  "LOG",   # logging misuse
  "PLE",   # pylint errors
  "PLW",   # pylint warnings
  "ARG",   # unused arguments
  "C90",   # cyclomatic complexity (max-complexity below)
]
unfixable = ["F841"] # never auto-delete unused variables

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]                 # assert is how pytest checks
"**/__init__.py" = ["TID252"]         # relative imports allowed only in __init__.py
"src/app/core/logger.py" = ["TID251"]

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"loguru".msg = "Import `logger` from `src.app.core.logger`."

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.isort]
known-first-party = ["src"]

# --- Function length <= 100 code lines (flake8, read via flake8-pyproject) ---
[tool.flake8]
select = ["MFL"]                   # only flake8-max-function-length; Ruff does the rest
max-function-length = 100
exclude = [".venv", "__pycache__"]

# --- File length <= 500 lines (pylint, this one check only) ---
[tool.pylint."messages control"]
disable = ["all"]
enable = ["too-many-lines"]

[tool.pylint.format]
max-module-lines = 500

# --- Tests (pytest) ---
[tool.pytest]
addopts = [
  "--strict-markers",
  "--import-mode=importlib",
  "-p",
  "no:tach",
] # tach's pytest plugin is not used
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto" # pytest-asyncio: run async def tests without a marker
markers = [
  "unit: isolated tests, no DB/Redis dependency",
  "integration: tests that hit a real DB/Redis instance",
]
```

`backend/tach.toml` — the app-level layer rules (`main`, `core/`). They live in tach's own file, not `[tool.tach]` in `pyproject.toml`: the VS Code extension starts `tach server -c backend/tach.toml` from the repo root, and `-c` reads the whole file as tach config (`pyproject.toml` fails with `unknown field dependency-groups`). The CLI (`uv run tach check` in `backend/`) finds `tach.toml` on its own.

```toml
# NestJS-style layers: router -> service -> repository.
# Its own file (not [tool.tach] in pyproject.toml): the VS Code extension starts
# `tach server -c backend/tach.toml` from the repo root, and `-c` reads a whole file
# as tach config.
#
# Feature layers (router -> service -> repository, and another feature only through its
# service) live next to each feature: src/app/features/<name>/tach.domain.toml.
source_roots = ["."]
exclude = ["tests", "**/__pycache__", ".venv"]
root_module = "forbid"                         # every source file must belong to a module below

[[modules]]
path = "src.app.main"
depends_on = [
  "src.app.core.container",
  "src.app.core.logger",
  "src.app.features.*.router",
]

[[modules]]
path = "src.app.core.config"
depends_on = []
utility = true               # any module may read settings

[[modules]]
path = "src.app.core.logger"
depends_on = ["src.app.core.config"]
utility = true                       # any module may log

[[modules]]
path = "src.app.core.container"
depends_on = ["src.app.features.*.dependencies"]
```

`src/app/features/<name>/tach.domain.toml` — each feature's own layer rules, copied with the folder. A tach _domain_ file: paths are relative to the feature, `//` paths are absolute. Because each feature has its own file, "same feature" is expressible: a service may use **its own** repository but only **another feature's service or schemas** — exactly what a Nest module exports. `test_structure.py` requires the file in every feature.

```toml
# Layer rules for this feature — copied with the folder when adding a feature.
# Paths are relative to this feature; "//" paths are absolute.
# NestJS-style: router -> service -> repository; another feature only through its
# service (and its schemas for DTO types).

[[modules]]
path = "router"
depends_on = [
  "service",
  "schemas",
  "//src.app.features.*.service",
  "//src.app.features.*.schemas",
]

[[modules]]
path = "service"
depends_on = [
  "repository",
  "schemas",
  "//src.app.features.*.service",
  "//src.app.features.*.schemas",
]

[[modules]]
path = "repository"
depends_on = ["schemas"]

[[modules]]
path = "schemas"
depends_on = []

[[modules]]
path = "dependencies"
depends_on = ["repository", "service"]
```

Notes (each verified by running the tool):

- **BasedPyright `recommended`** reports `reportUnannotatedClassAttribute`: annotate attributes (`self._repository: ItemRepository = repository`) and Pydantic config (`model_config: ClassVar[ConfigDict] = ConfigDict(...)`). Annotate `@asynccontextmanager` functions `-> AsyncGenerator[None]`, not `AsyncIterator` (typeshed marks the latter deprecated). dishka types `provide` with `Any`, so its import carries `# pyright: ignore[reportUnknownVariableType]`.
- **`FAST001`** flags `response_model=` that repeats the return annotation — annotate the route's return type only.
- **`banned-api`** makes `from loguru import logger` an error everywhere except `core/logger.py`.
- **flake8** runs only `MFL`. `flake8-max-function-length` counts code lines only (it skips the `def` line, docstrings, blank lines and comments — the same as oxlint's `skipBlankLines` / `skipComments`).
- **pylint** runs only `too-many-lines` (`C0302`). It counts **every** line, blank and comment lines included, so the Python file limit is slightly stricter than the frontend's. Ruff has no line-count rule (checked in Ruff 0.17: only `PLR0915` statement counts and `C901` complexity).
- **tach** (rules in `tach.toml`, next section) checks imports between modules: a router importing a repository fails (`Module 'src.app.features.items.router' cannot depend on 'src.app.features.items.repository'`), a repository importing a service fails, and with `root_module = "forbid"` a file that matches no module (e.g. `features/items/utils.py`) fails as `Module '<root>' cannot depend on …`. Another feature's repository, router or dependencies are rejected too (`Module 'src.app.features.items.service' cannot depend on 'src.app.features.orders.repository'`), through the per-feature domain files. Verified against NestJS's rules with 28 import directions (own/other feature, every layer, `core/`, `main`, stray files): 28/28 behave like Nest, from the CLI and from the tach language server; the cross-feature error also shows live in VS Code's Problems tab (verified).
- **pytest 9** reads the native `[tool.pytest]` table (header shows `configfile: pyproject.toml`, `asyncio: mode=Mode.AUTO`).

### 4. Structure (NestJS-style feature modules)

```
backend/
├── pyproject.toml          ← every rule except layers
├── tach.toml               ← app-level layer rules (main, core); features have their own
├── .python-version
├── .env.example            ← settings to copy into .env (LOG_LEVEL, LOG_FORMAT)
├── uv.lock
├── src/app/
│   ├── main.py             ← create_app(): logger, routers, dishka (Nest AppModule + main.ts)
│   ├── core/
│   │   ├── config.py       ← Settings (pydantic-settings, reads .env)
│   │   ├── logger.py       ← loguru setup; the only place loguru is imported
│   │   └── container.py    ← dishka container: every feature's Provider
│   └── features/
│       └── items/          ← sample feature — copy it for a new one
│           ├── __init__.py
│           ├── router.py       HTTP only            (Nest controller)
│           ├── service.py      business logic       (Nest service)
│           ├── repository.py   data access          (in-memory until a DB is added)
│           ├── schemas.py      Pydantic DTOs        (Nest DTOs)
│           ├── dependencies.py dishka Provider      (Nest module providers)
│           └── tach.domain.toml layer rules         (copied with the folder)
└── tests/
    ├── conftest.py         ← TestClient fixture (fresh app + container per test)
    ├── test_structure.py   ← fails when a feature folder misses a required file
    └── features/items/     ← mirrors src/app/features/
```

Adding a feature `orders`:

1. Copy `src/app/features/items/` to `src/app/features/orders/` (its `tach.domain.toml` comes along), rename the classes.
2. Register the router in `main.py` (`app.include_router(orders_router)`) and the provider in `core/container.py`.
3. Add `tests/features/orders/`.
4. Run [Verify CLI](#verify-cli). Tach already covers the new folder through the `features.*` globs.

### 5. Dependency injection — dishka

`features/<name>/dependencies.py` (one `Provider` per feature):

```python
from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType] -- dishka types it with Any
)

from src.app.features.items.repository import ItemRepository
from src.app.features.items.service import ItemService


class ItemsProvider(Provider):
    """The feature's providers, like a Nest module's `providers` list."""

    @provide(scope=Scope.APP)  # in-memory store: one per app
    def repository(self) -> ItemRepository:
        return ItemRepository()

    @provide(scope=Scope.REQUEST)
    def service(self, repository: ItemRepository) -> ItemService:
        return ItemService(repository)
```

`core/container.py`:

```python
from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider

from src.app.features.items.dependencies import ItemsProvider


def create_container() -> AsyncContainer:
    return make_async_container(FastapiProvider(), ItemsProvider())
```

`router.py` — `DishkaRoute` injects `FromDishka[...]` parameters without an `@inject` decorator per route:

```python
router = APIRouter(prefix="/items", tags=["items"], route_class=DishkaRoute)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_item(data: ItemCreate, service: FromDishka[ItemService]) -> ItemResponse:
    return await service.create(data)
```

`main.py` — the lifespan closes the container (and every resource it opened) on shutdown:

```python
def create_app() -> FastAPI:
    setup_logger()
    container = create_container()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        yield
        await container.close()

    app = FastAPI(title="Backend", lifespan=lifespan)
    app.include_router(items_router)
    setup_dishka(container, app)
    return app
```

**dishka and FastAPI `Depends` together** (verified in one route): use `Depends` only for _request decomposition_ — query/path/header parameters such as pagination, which then appear in the OpenAPI docs — and dishka (`FromDishka[...]`) for everything you'd construct: services, repositories, DB sessions, clients. dishka parameters stay out of the OpenAPI schema.

```python
@router.get("")
async def list_items(
    page: Annotated[Pagination, Depends(pagination)],  # FastAPI: parsed from ?limit=&offset=
    service: FromDishka[ItemService],  # dishka: built per request
) -> list[ItemResponse]: ...
```

Request-scoped values built from the request (current user, tenant) — `FastapiProvider()` makes `Request` injectable, so the service arrives already bound to the caller (verified):

```python
class AuthProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def current_user(self, request: Request) -> CurrentUser:
        return decode_token(request.headers["authorization"])
```

### 6. Logging — loguru

`core/logger.py` is the only module that imports loguru (Ruff `TID251` enforces it). Dev gets colored lines, prod gets JSON:

```python
_PRETTY_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level:<8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def setup_logger() -> None:
    settings = get_settings()
    logger.remove()
    if settings.log_format == "json":
        _ = logger.add(sys.stderr, level=settings.log_level, serialize=True)
    else:
        _ = logger.add(sys.stderr, level=settings.log_level, format=_PRETTY_FORMAT)
```

`core/config.py` holds the two settings (`log_level`, `log_format: Literal["pretty", "json"]`); set them per environment in `backend/.env`:

```bash
# Dev (default)            # Prod
LOG_LEVEL=DEBUG            # LOG_LEVEL=WARNING
LOG_FORMAT=pretty          # LOG_FORMAT=json
```

Use it as `from src.app.core.logger import logger` → `logger.info("Created item {}", item.id)`.

### 7. Libraries by use case

Installed by default: `fastapi`, `uvicorn`, `pydantic-settings` (config), `dishka` (DI), `loguru` (logging); dev: the tools above. Add the rest **only when a feature needs them**, with `uv add <pkg>` (latest stable):

| Need                      | Library                          | Install                                                      |
| ------------------------- | -------------------------------- | ------------------------------------------------------------ |
| Database ORM (PostgreSQL) | **SQLAlchemy** (async) + asyncpg | `uv add "sqlalchemy[asyncio]" asyncpg`                       |
| Migrations                | **Alembic**                      | `uv add alembic` → `uv run alembic init -t async migrations` |
| Cache, locks, rate limits | **redis** (`redis.asyncio`)      | `uv add redis`                                               |
| Outgoing HTTP calls       | **httpx2**                       | `uv add httpx2` (already a dev dependency for tests)         |

**SQLAlchemy wiring** (verified with dishka on Python 3.15) — `core/database.py` holds a `DatabaseProvider`: engine per app, session per request:

```python
class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def engine(self, settings: Settings) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(settings.database_url.get_secret_value())
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session
```

Then:

- `database_url: SecretStr` in `Settings` (`postgresql+asyncpg://…` in `.env`); add `DatabaseProvider()` to `create_container()`
- ORM models in `features/<name>/models.py`; repositories take an `AsyncSession` in `__init__`
- tach: add modules `src.app.core.database` (`depends_on = ["src.app.core.config"]`) and `src.app.features.*.models` (`depends_on = []`), add `"src.app.core.database"` to `core.container`'s `depends_on`, and `"src.app.features.*.models"` to the repository's
- Alembic: never edit an existing migration; review autogenerate output; run `alembic upgrade head` in CI/CD, never at app startup
- Ruff: add `"sqlalchemy".msg = "Database access goes through repositories."` to `banned-api`, and `TID251` to `per-file-ignores` for `src/app/features/*/repository.py`, `src/app/features/*/models.py` and `src/app/core/database.py` — a query in a service is then an error
- Integration tests use a real test database and roll back after each test

### 8. Verify CLI (backend)

```bash
cd backend
uv run ruff check src tests
uv run ruff format --check src tests
uv run basedpyright
uv run flake8 src tests
uv run pylint src tests
uv run tach check
uv run pytest
uv run pip-audit
```

All must pass. Then boot once: `uv run uvicorn src.app.main:app` → `curl -X POST localhost:8000/items -H 'content-type: application/json' -d '{"name":"Pen"}'` returns `{"id":1,"name":"Pen"}`.

---

## Frontend (Next.js + oxlint)

`create-next-app` ships **ESLint** — swap it for oxlint:

```bash
pnpm dlx create-next-app@latest frontend --ts --app --src-dir --tailwind --use-pnpm --disable-git --import-alias '@/*' --yes
cd frontend
rm eslint.config.mjs README.md .gitignore            # root .gitignore covers frontend/
rm -r public                                         # starter SVGs; recreate public/ for real assets
pnpm remove eslint eslint-config-next
pnpm add -D oxlint oxlint-tsgolint prettier prettier-plugin-organize-imports
pnpm add -D 'typescript@^6' '@types/node@^<Node LTS major>'   # see Troubleshooting: TypeScript 7
echo 'lts/*' > .nvmrc
```

- Replace the starter `src/app/page.tsx` with a bare page (one `<h1>`), and set `metadata` in `layout.tsx`.
- Add `src/app/error.tsx`, `src/app/global-error.tsx` and `src/app/not-found.tsx` (the production checklist recommends them). In Next.js 16.4 error boundaries receive `{ error, retry }` (`retry()` re-fetches the segment; `reset` is the older, rarer option) — copy the shape from `node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/error.md`, without its `console.error` (oxlint bans `console`); `global-error.tsx` renders its own `<html>` and `<body>`.
- `tsconfig.json`: add `"noUncheckedIndexedAccess": true` (an index read is `T | undefined`) and `"verbatimModuleSyntax": true` (type-only imports must say `import type`) next to `"strict": true`. `next build` keeps both (verified).
- Turbopack is the default bundler for `next dev` and `next build`; SWC is built in. React Compiler stays off (`next.config.ts` has no `reactCompiler: true`).
- Keep `AGENTS.md` and the generated `CLAUDE.md` (`@AGENTS.md`) — `next dev` re-writes that block. Project rules go below the import (`frontend/CLAUDE.md`).
- In `frontend/pnpm-workspace.yaml`, delete `allowBuilds` entries for removed packages (e.g. `unrs-resolver`); keep `sharp: false`.
- `@types/node` follows the Node **LTS** major (`.nvmrc` = `lts/*`), not the newest Node.

`frontend/.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["typescript", "unicorn", "oxc", "import", "react", "jsx-a11y", "nextjs", "vitest"],
  "categories": {
    "correctness": "error",
    "suspicious": "warn"
  },
  "env": {
    "browser": true
  },
  "rules": {
    "typescript/no-explicit-any": "error",
    "typescript/no-floating-promises": "error",
    "typescript/no-misused-promises": "error",
    "typescript/await-thenable": "error",
    "typescript/no-unsafe-argument": "error",
    "typescript/no-unsafe-assignment": "error",
    "typescript/no-unsafe-call": "error",
    "typescript/no-unsafe-member-access": "error",
    "typescript/no-unsafe-return": "error",
    "typescript/explicit-function-return-type": [
      "error",
      {
        "allowExpressions": true,
        "allowTypedFunctionExpressions": true
      }
    ],
    "eslint/no-eval": "error",
    "typescript/no-implied-eval": "error",
    "eslint/no-new-func": "error",
    "eslint/no-script-url": "error",
    "eslint/no-proto": "error",
    "eslint/no-caller": "error",
    "eslint/no-console": "error",
    "react/react-in-jsx-scope": "off",
    "import/no-unassigned-import": [
      "warn",
      {
        "allow": ["**/*.css"]
      }
    ],
    "react/no-danger": "error",
    "react/jsx-no-script-url": "error",
    "react/jsx-no-target-blank": "error",
    "eslint/max-lines": [
      "error",
      {
        "max": 500,
        "skipBlankLines": true,
        "skipComments": true
      }
    ],
    "eslint/max-lines-per-function": [
      "error",
      {
        "max": 100,
        "skipBlankLines": true,
        "skipComments": true
      }
    ],
    "import/no-cycle": "error"
  },
  "ignorePatterns": ["node_modules/", ".next/", "dist/", "coverage/", "next-env.d.ts"],
  "overrides": [
    {
      "files": ["src/components/ui/**"],
      "rules": {
        "typescript/explicit-function-return-type": "off",
        "eslint/max-lines": "off",
        "eslint/max-lines-per-function": "off"
      }
    },
    {
      "files": ["**/*.test.ts", "**/*.test.tsx"],
      "rules": {
        "eslint/max-lines-per-function": "off"
      }
    }
  ]
}
```

- `plugins` **replaces** the defaults (`typescript`, `unicorn`, `oxc`) — always list them. `nextjs` = the `eslint-config-next` rules.
- Type-aware rules (`no-floating-promises`, `no-unsafe-*`) need `oxlint-tsgolint` and the `--type-aware` flag in the scripts — not `options.typeAware` (agent rule 10).
- Size limits: `max-lines` (500) and `max-lines-per-function` (100), code lines only. Test files are exempt from the function limit (a suite is one `describe` callback); shadcn's generated `src/components/ui/**` is exempt from return types and both limits (`shadcn add --overwrite` would undo hand edits). React components count as functions — split a component over 100 lines.
- `import/no-cycle` — circular imports between modules are errors.
- `no-unassigned-import` allows `import './globals.css'`. `explicit-function-return-type` applies to components: `layout.tsx` / `page.tsx` return `React.JSX.Element`.

`frontend/.prettierrc` (`printWidth` matches Ruff's `line-length`; the plugin sorts and removes imports on format, and `format:check` fails on unsorted ones):

```json
{
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "plugins": ["prettier-plugin-organize-imports"]
}
```

`.prettierignore`:

```bash
printf 'pnpm-lock.yaml\npnpm-workspace.yaml\n.next\nnext-env.d.ts\ndist\ncoverage\n' > .prettierignore
```

Tests — Vitest + React Testing Library (Next's bundled guide: `node_modules/next/dist/docs/01-app/02-guides/testing/vitest.md`):

```bash
pnpm add -D vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom
```

`vitest.config.mts` — Vite resolves the `@/` alias from `tsconfig.json` itself (`resolve.tsconfigPaths`); the `vite-tsconfig-paths` plugin is no longer needed (Vitest warns when it's installed):

```ts
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  resolve: { tsconfigPaths: true },
  test: { environment: 'jsdom' },
});
```

`src/app/page.test.tsx` (tests sit next to the code):

```tsx
import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import Page from './page';

test('renders the main heading', () => {
  render(<Page />);
  expect(screen.getByRole('heading', { level: 1 })).toBeDefined();
});
```

Scripts (`frontend/package.json`):

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "oxlint --type-aware --deny-warnings",
  "lint:fix": "oxlint --type-aware --fix",
  "typecheck": "next typegen && tsc --noEmit",
  "format": "prettier --write .",
  "format:check": "prettier --check .",
  "test": "vitest run",
  "test:watch": "vitest",
  "audit": "pnpm audit --audit-level=high"
}
```

`next typegen` generates Next's route types (`LayoutProps`, `PageProps`) — without it `tsc` fails on a clean checkout. Format once after scaffolding (`create-next-app` uses double quotes): `pnpm run format`.

### What enforces the frontend structure

| Rule                                                                                                                                                                          | Enforced by                       | Where it shows                                                                                                                                                                   |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Routes come only from `page.tsx` / `route.ts` / `layout.tsx` … in `src/app/`; a `page.tsx` and `route.ts` in the same folder fail (`Conflicting route and page`)              | Next.js itself                    | `next build`, `next dev`                                                                                                                                                         |
| Hooks such as `useState` only in Client Components; `'use client'` used correctly (`You're importing a module that depends on useState into a React Server Component module`) | Next.js itself                    | `next build`; live in the editor through the Next.js TypeScript plugin (needs **Use Workspace Version**): `ts(71001) "useState" is not allowed in Server Components.` (verified) |
| Internal links via `next/link`, images via `next/image`, no `<head>` misuse                                                                                                   | oxlint `nextjs` plugin            | live (oxc) + `pnpm run lint`                                                                                                                                                     |
| No import cycles                                                                                                                                                              | oxlint `import/no-cycle`          | live (oxc) + `pnpm run lint`                                                                                                                                                     |
| Fetch on the server, no secrets in `NEXT_PUBLIC_*`, feature folders don't import each other                                                                                   | convention (`frontend/CLAUDE.md`) | review — no tool checks these                                                                                                                                                    |

A Route Handler (`src/app/api/**/route.ts`) is optional in the App Router: Server Components and Server Actions can call the backend directly, and that is the preferred path (`frontend/CLAUDE.md` rule 2). Use a Route Handler only for something the browser itself must call (webhooks, a CopilotKit runtime, a public endpoint).

### Frontend libraries by use case

Add only when a feature needs them (rules in `frontend/CLAUDE.md`):

| Need                                  | Library                                            | Setup                                                                                                                                                            |
| ------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Any UI component                      | **shadcn/ui**                                      | `pnpm dlx shadcn@latest init` once, then `pnpm dlx shadcn@latest add <component>` → `src/components/ui/`; run `pnpm run format` after each                       |
| Validation (forms, backend responses) | **Zod**                                            | `pnpm add zod`                                                                                                                                                   |
| Agent chat / agent UI                 | **CopilotKit** over AG-UI (+ A2UI for rich blocks) | `pnpm add @copilotkit/react-core @copilotkit/runtime @ag-ui/client`; use the newest entry point its docs recommend; runtime in `src/app/api/copilotkit/route.ts` |

### Verify CLI (frontend)

```bash
cd frontend
pnpm run lint && pnpm run typecheck && pnpm run format:check
pnpm run test && pnpm run build && pnpm run audit
```

---

## Root `.gitignore`

One file at the repo root covers both packages (no `frontend/.gitignore`). Key entries: `__pycache__/`, `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `node_modules/`, `.next/`, `next-env.d.ts`, `*.tsbuildinfo`, `coverage/`, `.env` / `.env.*` with `!.env.example`, and `.vscode/*` with `!.vscode/extensions.json`, `!.vscode/settings.json`, `!.vscode/tasks.json`. Without `node_modules/` ignored, oxlint lints `node_modules` and appears to hang.

---

## Workspace settings (commit `.vscode/`)

### `.vscode/extensions.json`

Recommends the nine extensions above; `unwantedRecommendations`: `ms-python.vscode-pylance`, `dbaeumer.vscode-eslint`.

### `.vscode/settings.json`

```json
{
  "npm.autoDetect": "off",
  "editor.formatOnSave": true,

  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.languageServer": "None",
  "basedpyright.analysis.configFilePath": "${workspaceFolder}/backend",
  "basedpyright.analysis.diagnosticMode": "workspace",
  "ruff.interpreter": ["${workspaceFolder}/backend/.venv/bin/python"],
  "flake8.interpreter": ["${workspaceFolder}/backend/.venv/bin/python"],
  "flake8.importStrategy": "fromEnvironment",
  "flake8.cwd": "${workspaceFolder}/backend",
  "pylint.interpreter": ["${workspaceFolder}/backend/.venv/bin/python"],
  "pylint.importStrategy": "fromEnvironment",
  "pylint.cwd": "${workspaceFolder}/backend",
  "pylint.lintOnChange": true,
  "tach.importStrategy": "fromEnvironment",
  "tach.configuration": "backend/tach.toml",
  "pylint.severity": {
    "convention": "Error",
    "error": "Error",
    "fatal": "Error",
    "refactor": "Hint",
    "warning": "Warning",
    "info": "Information"
  },

  "js/ts.tsdk.path": "frontend/node_modules/typescript/lib",
  "js/ts.tsdk.promptToUseWorkspaceVersion": true,
  "js/ts.tsserver.experimental.enableProjectDiagnostics": true,
  "oxc.requireConfig": true,
  "oxc.typeAware": true,
  "oxc.path.tsgolint": "frontend/node_modules/.bin/tsgolint",

  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll": "always",
      "source.organizeImports": "always"
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.codeActionsOnSave": {
      "source.fixAll.oxc": "always",
      "source.organizeImports": "always"
    }
  },
  "[json]": { "editor.defaultFormatter": "esbenp.prettier-vscode" },
  "[toml]": { "editor.defaultFormatter": "tamasfe.even-better-toml" }
}
```

The committed file repeats the `[typescript]` block for `[typescriptreact]`, `[javascript]`, `[javascriptreact]`, and the `[json]` line for `[jsonc]`, `[css]`, `[markdown]`, `[yaml]`.

Why each line (setting names checked in each extension's `package.json`):

- `npm.autoDetect: "off"` — hides VS Code's auto-generated npm script tasks so the task list only shows this repo's tasks.
- `python.languageServer: "None"` — turns off Pylance's language server; BasedPyright provides types instead.
- `pylint.lintOnChange: true` — Pylint re-checks while you type (default: on save only).
- `oxc.requireConfig: true` — oxlint runs only where a `.oxlintrc.json` exists (`frontend/`), so other files get no default-rule noise.
- `editor.formatOnSave` + per-language `defaultFormatter` — every file type with a formatter is formatted on save: Python by Ruff, TS/JS/JSON/CSS/Markdown/YAML by Prettier, TOML by Even Better TOML. Files without a formatter (`.gitignore`, `.nvmrc`) are left alone.
- `basedpyright.analysis.diagnosticMode: "workspace"` — type errors for **every** file, opened or not (verified: an unopened file's error appears in Problems). `configFilePath` points BasedPyright at `backend/pyproject.toml`.
- `*.interpreter` + `importStrategy: "fromEnvironment"` — Ruff, Flake8 and Pylint run the versions in `backend/.venv` (the same ones as the CLI, with the `flake8-max-function-length` / `flake8-pyproject` plugins); the bundled copies don't have the plugins.
- `flake8.cwd` / `pylint.cwd` — both read `backend/pyproject.toml` from their working directory. Ruff needs no `cwd`: it finds the nearest `pyproject.toml` per file (`ruff.cwd` doesn't exist).
- `tach.*` — the Tach extension runs `python -m tach server -c <configuration>` with the repo root as working directory, using the interpreter selected in VS Code (`backend/.venv`). Don't set `tach.interpreter`: at startup the extension passes it unexpanded to the Python extension, `${workspaceFolder}/…` resolves to nothing (`Python version undefined.undefined is not supported`) and the server never starts. `configuration` is passed as-is, so it is relative to the repo root.
- `pylint.severity.convention: "Error"` — `C0302` is a _convention_ message, which the extension shows as Information by default.
- `js/ts.tsserver.experimental.enableProjectDiagnostics` — TypeScript errors for every file of a project once one of its files was opened (experimental; `pnpm run typecheck` is always accurate).
- `oxc.path.tsgolint` — the Oxc language server runs from the repo root, which has no `node_modules`, so it can't find the type-aware engine on its own.

### `.vscode/tasks.json` — manual only

| Task                                 | Command (cwd)                                                                               | Problem matcher                                                                                   |
| ------------------------------------ | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `backend: dev`                       | `uv run uvicorn src.app.main:app --reload` (backend)                                        | —                                                                                                 |
| `backend: ruff`                      | `uv run ruff check --output-format concise src tests`                                       | `ruff`                                                                                            |
| `backend: basedpyright`              | `uv run basedpyright`                                                                       | `basedpyright` (absolute paths)                                                                   |
| `backend: function length (flake8)`  | `uv run flake8 --color never src tests`                                                     | `flake8`                                                                                          |
| `backend: file length (pylint)`      | `uv run pylint src tests --score=n --msg-template='{path}:{line}:{column}: {msg_id} {msg}'` | `pylint`                                                                                          |
| `backend: structure (tach)`          | `uv run tach check`                                                                         | `tach` (`[FAIL] file:line:` when piped, `❌ file:line:` in a terminal — the pattern accepts both) |
| `backend: format`                    | `uv run ruff format --check src tests`                                                      | —                                                                                                 |
| `backend: test`                      | `uv run pytest --tb=line`                                                                   | `pytest` (failing assertion line)                                                                 |
| `frontend: dev`                      | `pnpm run dev` (frontend)                                                                   | —                                                                                                 |
| `frontend: lint`                     | `pnpm run --silent lint --format unix`                                                      | `oxlint`                                                                                          |
| `frontend: typecheck`                | `pnpm run typecheck`                                                                        | `$tsc`, `fileLocation` = `frontend/`                                                              |
| `frontend: format` / `test`          | `pnpm run format:check` / `pnpm run test`                                                   | —                                                                                                 |
| `backend: audit` / `frontend: audit` | `uv run pip-audit --progress-spinner off` / `pnpm run audit`                                | — (not part of `check: all`: they report vulnerable packages, not file problems)                  |
| **`check: all`**                     | every task above except `dev`, in parallel                                                  | each task's own                                                                                   |

Run **Tasks: Run Task → `check: all`** for a full-workspace scan: every file's problems land in the Problems panel (verified: entries from all eight tools appeared), one owner per tool, so a rerun of one task replaces only its own entries. Task problems stay until that task runs again.

- Task entries carry the source `<tool> (task)` (e.g. `tach (task)`); live editor entries carry the plain tool name (`tach`). A task entry is a snapshot of its last run: it stays — even for a file that was fixed or deleted — until that task runs again, so rerun `check: all` after big changes. The Tach extension re-checks a file only when it is opened or saved: its server ignores edits (`Received unknown notification: textDocument/didChange` in Output → **Tach**), so after an agent or `git` changes a file on disk its old errors stay. Clear them with **Tach: Restart Server** (or close and reopen the file).
- Every non-composite task sets `NO_COLOR=1` (and the BasedPyright task also `FORCE_COLOR=0`, which BasedPyright needs; Ruff reads any `FORCE_COLOR` as "on", so it isn't global), and flake8 gets `--color never`. VS Code runs tasks in a terminal, where these tools print colour codes otherwise, and the problem patterns would then match nothing (verified by running each task command in a pseudo-terminal against real violations).
- `check: all` runs its tasks **in parallel** (one terminal each). Keep it that way: with `"dependsOrder": "sequence"` VS Code stops at the first task that fails, and the remaining tools never report.
- Agents: the Claude Code `getDiagnostics` tool returns extension diagnostics only, not task problem-matcher results. Ask the user which sources appear in Problems after running `check: all`.
- Never add `"runOn": "folderOpen"` (it opens terminals on every reload) unless the user asks.

---

## User settings (once per machine)

`~/Library/Application Support/Code/User/settings.json` (Cursor: `.../Cursor/User/settings.json`):

```json
{
  "files.autoSave": "onFocusChange"
}
```

- Auto-save fires the workspace's format-on-save and fix-on-save when you click away from a file. It saves only files with **unsaved edits**: a file changed on disk by an agent isn't dirty, so nothing runs until you type in it or press Cmd+S.
- Never put rule settings (`ruff.lint.select`, `ruff.lineLength`, `ruff.configuration`) in user settings — Ruff's default `configurationPreference: "editorFirst"` lets them override `pyproject.toml`.
- Language blocks (`[python]`, `[typescript]`, …) in user settings are fine but redundant here: the workspace file sets them.

---

## Verify CLI

```bash
cd backend && uv run ruff check src tests && uv run ruff format --check src tests && uv run basedpyright \
  && uv run flake8 src tests && uv run pylint src tests && uv run tach check && uv run pytest && uv run pip-audit
cd ../frontend && pnpm run lint && pnpm run typecheck && pnpm run format:check \
  && pnpm run test && pnpm run build && pnpm run audit
```

All must pass.

## Verify editor (smoke test — delete after)

An agent can't see VS Code by itself. Two channels exist:

- **Claude Code's IDE connection.** The user runs `/ide` and picks VS Code. The agent then calls `getDiagnostics` (per file or all files) and gets exactly what the editor shows: Ruff, BasedPyright, Flake8, Pylint, tach, oxc, ts. It does **not** return task (problem-matcher) results, the `<tool> (task)` entries.
- **The user.** Some steps need a human in the editor. Ask for all of them in **one** message (the user may not be around for several round trips), and ask for a screenshot of the Problems tab where the agent can't read it.

### Step 0 — editor ready (user)

One message to the user covering: install the extensions ([Required extensions](#required-vs-code-extensions)) → **Developer: Reload Window** → **Python: Select Interpreter → `backend/.venv/bin/python`** → **TypeScript: Select TypeScript Version → Use Workspace Version** (turns on the Next.js TypeScript plugin; VS Code needs this approval once and settings can't give it) → `/ide` in Claude Code. The Python extensions start only when a `.py` file is open: their activation looks for `pyproject.toml` / `*.py` at the **workspace root**, and this repo keeps them in `backend/`. So a Python file must be open once per session; BasedPyright then scans the whole workspace.

### Step 1 — create every smoke file (agent)

**Backend** — create `backend/src/app/features/items/smoke.py` (a function over 100 lines and a file over 500 lines):

```bash
cd backend && python3 -c "
body = ''.join(f'    n += {i}\n' for i in range(101))
open('src/app/features/items/smoke.py', 'w').write(
    '# SMOKE TEST: delete after verifying\nimport os\n\nfrom src.app.features.items.repository import ItemRepository\n\n\n'
    'def wrong_type() -> int:\n    return \"not-an-int\"\n\n\n'
    'def too_long() -> int:\n    n = 0\n' + body + '    return n\n' + ''.join(f'X{i} = {i}\n' for i in range(400)))"
printf '# SMOKE TEST: delete after verifying\n\n\ndef closed_file_error() -> int:\n    return "not-an-int"\n' > src/app/features/items/smoke_closed.py
```

Open `smoke.py` only. Expect in Problems (verified):

| Source                                                | Problem                                                                       |
| ----------------------------------------------------- | ----------------------------------------------------------------------------- |
| Ruff                                                  | `` `os` imported but unused `` (F401)                                         |
| basedpyright                                          | `Type "Literal['not-an-int']" is not assignable to return type "int"` (error) |
| Flake8                                                | `MFL000 Function too long (103 > 100)` (error)                                |
| Pylint                                                | `Too many lines in module (514/500)` (error)                                  |
| basedpyright, in **`smoke_closed.py` (never opened)** | the same type error — proves whole-workspace mode                             |

Also expect, source **tach** (verified), on `smoke.py` line 4: `Module '<root>' cannot depend on 'src.app.features.items.repository'` (a file outside the feature module types). Type a character in `smoke.py` and click away: auto-save runs Ruff — the unused imports disappear.

**Frontend** — create three files in `frontend/src/app/`:

```ts
// smoke.ts — SMOKE TEST: delete after verifying
import { readFile } from 'node:fs';

async function save(): Promise<void> {}

export function run(value: any) {
  console.log(value);
  save();
}

export const wrongType: number = 'not-a-number';
```

```bash
node -e "require('fs').writeFileSync('frontend/src/app/smoke-size.ts', '// SMOKE TEST: delete after verifying\nexport function big(): number {\n  let n = 0;\n' + '  n++;\n'.repeat(100) + '  return n;\n}\n')"
```

```tsx
// smoke-jsx.tsx — SMOKE TEST: delete after verifying
export function Smoke(): React.JSX.Element {
  return (
    <a href="/about">
      <img src="/logo.svg" alt="logo" />
    </a>
  );
}
```

Open all three. (`smoke-jsx.tsx` must not share a base name with `smoke.ts`: TypeScript keeps only one of `x.ts` / `x.tsx` in a project, so the other is checked as a loose file and reports false errors like `Cannot find namespace 'React'`.) Expect, source **oxc**, all errors: `no-unused-vars`, `explicit-function-return-type`, `no-explicit-any`, `no-console`, `no-floating-promises` (proves type-aware linting), `max-lines-per-function` (`big`, 104 lines), `next(no-html-link-for-pages)`, `next(no-img-element)`; source **ts**: `Type 'string' is not assignable to type 'number'`. Compare with `cd frontend && pnpm run lint` — the lists must match. Type a character in `smoke.ts` and click away: double quotes become single, semicolons are added, the unused import is removed.

**Structure** — break the NestJS layering on purpose:

```bash
cd backend
# router skips the service (tach)
printf '\nfrom src.app.features.items.repository import ItemRepository  # SMOKE TEST\n\n_SMOKE = ItemRepository\n' >> src/app/features/items/router.py
# feature folder missing its files (pytest)
mkdir -p src/app/features/orders && touch src/app/features/orders/__init__.py
printf 'from fastapi import APIRouter\n\nrouter = APIRouter(prefix="/orders")\n' > src/app/features/orders/router.py
uv run tach check   # expect [FAIL] … Module 'src.app.features.items.router' cannot depend on 'src.app.features.items.repository'
uv run pytest -q    # expect … src/app/features/orders/ is missing: service.py, repository.py, schemas.py, dependencies.py, tach.domain.toml
```

**Pre-commit hook** — must refuse a commit while any smoke file exists:

```bash
git add -A && git commit -m "smoke: must be blocked"; echo "exit=$?"   # expect exit=1 and no new commit (git log)
git reset -q                                                          # unstage again
```

### Step 2 — one batched request to the user

> Please, in VS Code: (1) open `backend/src/app/features/items/smoke.py`, `backend/src/app/features/items/router.py`, and the three `frontend/src/app/smoke*` files — but **not** `smoke_closed.py`; (2) in `smoke.py` and `frontend/src/app/smoke.ts` type one space and press Cmd+S; (3) **Tasks: Run Task → `check: all`**, wait for every terminal to finish; (4) send a screenshot of the Problems tab, then reply "done".

### Step 3 — verify (agent)

- **Editor checks** — `getDiagnostics` on each smoke file must show every row of the backend and frontend tables above, plus on `router.py` source **tach**: `Module 'src.app.features.items.router' cannot depend on 'src.app.features.items.repository'`.
- **Whole-workspace mode** — `smoke_closed.py` (never opened) must show the basedpyright type error.
- **Fix/format on save** — read the files from disk: `smoke.py` no longer has `import os`; `smoke.ts` has single quotes, semicolons and no `readFile` import.
- **Tasks** — in the screenshot, entries with sources `ruff (task)`, `basedpyright (task)`, `flake8 (task)`, `pylint (task)`, `tach (task)`, `pytest (task)` (orders missing files), `oxlint (task)` and `tsc (task)`.
- If a task source is missing, run that task's command inside a pseudo-terminal and match its pattern by hand — tools print differently in a terminal than in a pipe: `script -q /dev/null sh -c '<command>' < /dev/null` with the task's `env`, then test the `regexp` from `tasks.json` against each line.

### Step 4 — clean up (agent, then user)

```bash
git checkout -- backend/src/app/features/items/router.py
rm -r backend/src/app/features/orders
rm backend/src/app/features/items/smoke.py backend/src/app/features/items/smoke_closed.py
rm frontend/src/app/smoke.ts frontend/src/app/smoke-size.ts frontend/src/app/smoke-jsx.tsx
git status --short   # must be empty
```

Then ask the user to close the deleted files' tabs, run **TypeScript: Restart TS Server** (with a `.ts`/`.tsx` file active) and **Tach: Restart Server**, and one more **`check: all`** — tach keeps errors for files changed on disk and task entries stay until their task reruns, so without this the Problems tab keeps showing the deleted smoke files. A final `getDiagnostics` (all files) must return no errors.

---

## Git pre-commit hook

`.githooks/pre-commit` runs the fast checks (every backend check, frontend lint/typecheck/format/test) and blocks the commit when one fails. Git doesn't enable committed hooks by itself — once per clone:

```bash
git config core.hooksPath .githooks
```

There is no CI workflow in this template.

---

## Troubleshooting

| Symptom                                                                                             | Fix                                                                                                                                                                                                                                                                                                                                                                                |
| --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No Python problems at all after opening the folder                                                  | The Python extensions activate on an open `.py` file (their root-level triggers don't see `backend/`). Open any Python file; Output → **BasedPyright** / **Flake8** / **Pylint** shows they started                                                                                                                                                                                |
| `Package … is not installed in the selected environment` on `pyproject.toml`                        | VS Code selected a global Python. **Python: Select Interpreter → `backend/.venv/bin/python`**                                                                                                                                                                                                                                                                                      |
| Problems empty, CLI finds type errors                                                               | BasedPyright extension missing/disabled, or Pylance still installed; `python.languageServer: "None"`; Reload Window                                                                                                                                                                                                                                                                |
| Flake8/Pylint silent or using defaults                                                              | `importStrategy: "fromEnvironment"`, `*.interpreter` → `backend/.venv`, `*.cwd` → `backend/`; `uv sync` so the plugins are installed                                                                                                                                                                                                                                               |
| flake8 ignores `[tool.flake8]`                                                                      | `flake8-pyproject` missing, or flake8 runs from a directory without `pyproject.toml`                                                                                                                                                                                                                                                                                               |
| File-length problem shows as blue Information                                                       | `pylint.severity` needs `"convention": "Error"`                                                                                                                                                                                                                                                                                                                                    |
| `tach`: `Module '<root>' cannot depend on …`                                                        | The file matches no module in `tach.toml` — move the code into a feature file or add a module entry for the new kind of file                                                                                                                                                                                                                                                       |
| Tach problems missing in the editor                                                                 | Tach extension installed; `tach.configuration` = `backend/tach.toml`; **no** `tach.interpreter`; interpreter selected = `backend/.venv`. Output → **Tach** must show `Project root: …/backend`. `Configuration file not found` = `tach.configuration` missing; `Python version undefined.undefined` = remove `tach.interpreter`. The task `backend: structure (tach)` always works |
| Next.js editor warnings (hooks in Server Components, `'use client'` misuse) never appear            | Open a `.ts`/`.tsx` file first (the command only exists while one is active), then **TypeScript: Select TypeScript Version → Use Workspace Version** — VS Code loads the `next` plugin from `tsconfig.json` only for the workspace TypeScript                                                                                                                                      |
| An old `tach` error stays on a line that is now fine                                                | The tach server ignores edits and disk changes — **Tach: Restart Server**, or close and reopen the file. Old `<tool> (task)` entries clear when that task runs again                                                                                                                                                                                                               |
| `File '…' not found. The file is in the program because…` (source `ts`) for a file that was deleted | The TypeScript server still holds the deleted file (usually because its tab was open). Close the tab, then **TypeScript: Restart TS Server** with a `.ts`/`.tsx` file active                                                                                                                                                                                                       |
| `tach`: `Module '…router' cannot depend on '…repository'`                                           | Go through the service — routers never touch repositories                                                                                                                                                                                                                                                                                                                          |
| `test_feature_has_required_files` fails                                                             | The feature folder is missing one of `router.py`, `service.py`, `repository.py`, `schemas.py`, `dependencies.py`, `__init__.py`                                                                                                                                                                                                                                                    |
| `MFL000` / `C0302` / `max-lines*` error                                                             | Split the function or file. Never raise `max` or add a disable comment                                                                                                                                                                                                                                                                                                             |
| BasedPyright `reportUnannotatedClassAttribute`                                                      | Annotate the attribute (`self._x: T = x`, `model_config: ClassVar[ConfigDict] = …`)                                                                                                                                                                                                                                                                                                |
| BasedPyright: `asynccontextmanager` is deprecated                                                   | Annotate the lifespan `-> AsyncGenerator[None]`, not `AsyncIterator[None]`                                                                                                                                                                                                                                                                                                         |
| BasedPyright `reportUnknownVariableType` on `from dishka import provide`                            | dishka types `provide` with `Any` — keep the `# pyright: ignore[reportUnknownVariableType]` on that import                                                                                                                                                                                                                                                                         |
| `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`                  | `uv add --dev httpx2`                                                                                                                                                                                                                                                                                                                                                              |
| `uv python install` can't find the newest Python                                                    | Upgrade uv (`brew upgrade uv`) — its download list is built in                                                                                                                                                                                                                                                                                                                     |
| Ruff flags differ between editor and CLI                                                            | Remove `ruff.lint.select` / `ruff.lineLength` / `ruff.configuration` from user settings                                                                                                                                                                                                                                                                                            |
| `pnpm run lint` hangs for minutes                                                                   | oxlint is linting `node_modules` — missing `.gitignore` / `ignorePatterns`                                                                                                                                                                                                                                                                                                         |
| Editor shows only a few oxc **warnings** while `pnpm run lint` shows errors                         | `frontend/.oxlintrc.json` contains `options.typeAware` — not allowed in nested configs; remove it, then **Oxc: Restart Server**                                                                                                                                                                                                                                                    |
| Editor misses `no-floating-promises` / `no-unsafe-*`                                                | Set `"oxc.path.tsgolint": "frontend/node_modules/.bin/tsgolint"`, then Reload Window                                                                                                                                                                                                                                                                                               |
| **TypeScript 7** (`typescript@latest`)                                                              | Kept on **TypeScript 6**: TypeScript 7 passes `tsc`, oxlint and `next build`, but ships no `lib/tsserver.js`, so `js/ts.tsdk.path` and the project-wide diagnostics this repo relies on don't work with it (VS Code needs the separate `TypeScriptTeam.native-preview` extension for now). Move to 7 once VS Code's built-in TypeScript supports it with project diagnostics       |
| TS errors only in the editor, e.g. `Cannot find namespace 'React'` in a `.tsx`                      | Another file has the same base name (`x.ts` next to `x.tsx`) — TypeScript drops one from the project; rename one. `pnpm exec tsc --noEmit --listFilesOnly` shows which files are in                                                                                                                                                                                                |
| Vitest: `The plugin "vite-tsconfig-paths" is detected`                                              | `pnpm remove vite-tsconfig-paths`; use `resolve: { tsconfigPaths: true }` in `vitest.config.mts`                                                                                                                                                                                                                                                                                   |
| `Cannot find name 'LayoutProps'`                                                                    | `typecheck` must run `next typegen` before `tsc`                                                                                                                                                                                                                                                                                                                                   |
| `format:check` fails after scaffolding or `shadcn add`                                              | Run `pnpm run format`                                                                                                                                                                                                                                                                                                                                                              |
| Format/fix on save didn't run after an agent edited a file                                          | Auto-save only saves unsaved edits — type in the file or press Cmd+S                                                                                                                                                                                                                                                                                                               |
| `AGENTS.md` keeps reappearing in the diff                                                           | `next dev` maintains it — commit it                                                                                                                                                                                                                                                                                                                                                |

---

## New project checklist

- [ ] **1.** Copy this repo (or follow Backend 1–8 + Frontend)
- [ ] **2.** `cd backend && uv sync`; `cd frontend && pnpm install`; `nvm install && nvm use` in `frontend/`
- [ ] **3.** Install the VS Code extensions, uninstall Pylance → Reload Window → **Select Interpreter** → `backend/.venv`
- [ ] **4.** User settings: `files.autoSave: "onFocusChange"`
- [ ] **4b.** `git config core.hooksPath .githooks` (pre-commit hook)
- [ ] **5.** `cp backend/.env.example backend/.env`; create `frontend/.env.local` for frontend secrets (never commit either)
- [ ] **6.** Run [Verify CLI](#verify-cli) — all green
- [ ] **7.** Run the [editor smoke test](#verify-editor-smoke-test--delete-after) → delete the smoke files
- [ ] **7b.** Ask the user about [application-specific setup](#application-specific-setup--ask-the-user-first); add only what they approve
- [ ] **8.** Commit config files — never rely on personal settings alone

---

## Reference: this repo's layout

```
<project>/
├── SETUP.md                    ← this file
├── README.md
├── CLAUDE.md                   ← shared coding rules for AI agents
├── .gitignore                  ← one file for backend + frontend
├── .prettierrc                 ← format style for root files (docs, .vscode/*.json) — frontend's style without the organize-imports plugin
├── .vscode/                    ← extensions, settings (wiring + format on save), tasks
├── .githooks/pre-commit        ← runs the fast checks before each commit
├── backend/
│   ├── CLAUDE.md               ← backend rules
│   ├── pyproject.toml          ← backend rules (Ruff, BasedPyright, flake8, pylint, pytest)
│   ├── tach.toml               ← app-level layer rules (features: src/app/features/*/tach.domain.toml)
│   ├── .python-version, uv.lock, .env.example
│   ├── src/app/                ← main.py, core/, features/<name>/
│   └── tests/                  ← test_structure.py + features/ mirror
└── frontend/                   ← Next.js (App Router, src/, Tailwind, Turbopack)
    ├── CLAUDE.md, AGENTS.md    ← frontend rules + Next's agent rules
    ├── .oxlintrc.json, .prettierrc, tsconfig.json, vitest.config.mts, .nvmrc
    └── src/app/                ← layout, page (+ test), globals.css
```

---

## Agent completion criteria

Before marking tooling setup done, confirm:

1. Backend: `ruff check`, `ruff format --check`, `basedpyright`, `flake8`, `pylint`, `tach check`, `pytest`, `pip-audit` all pass; the server boots and `POST /items` works
2. Frontend: `lint`, `typecheck`, `format:check`, `test`, `build`, `audit` all pass
3. Editor smoke test (Steps 0–4 above): every row of the backend and frontend tables appears in Problems — as errors where listed — including the never-opened `smoke_closed.py`, the tach error on `router.py`, and all eight `(task)` sources in the user's screenshot; fix/format on save confirmed on disk; the pre-commit hook refused the smoke commit; all smoke files removed and `getDiagnostics` clean
4. Size limits are errors in both: `max-function-length = 100` + `max-module-lines = 500` (backend), `max-lines-per-function` 100 + `max-lines` 500 (frontend)
5. `backend/tach.toml` has `root_module = "forbid"` and the router → service → repository rules; `tests/test_structure.py` exists
6. No stray config files: no `pyrightconfig.json`, `.flake8`, `.pylintrc`, `[tool.tach]` in `pyproject.toml`, `eslint.config.mjs`, `frontend/.gitignore`
7. Extensions installed as listed; Pylance and ESLint not installed; the interpreter is `backend/.venv`
8. Versions are the newest stable ones that pass every check; any held-back major is recorded in Troubleshooting
