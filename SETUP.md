# Dev Tooling Setup Guide

Production-ready linting, formatting, type-checking, size limits, structure checks and tests for a monorepo: a **FastAPI** backend (Python, `uv`, NestJS-style feature modules, dishka DI, loguru) and a **Next.js** frontend (oxlint, Prettier, Vitest). Use this checklist when bootstrapping a new project from this repo.

**Path:** `SETUP.md` (repo root). Point agents here for editor + CLI tooling setup. The TypeScript-backend twin of this repo is `base-repo-ts` (NestJS + Next.js); the frontend section below is shared with it.

---

## For AI agents — read this first

1. **Three-layer rule** — rules live in config files (`backend/pyproject.toml`, `backend/tach.toml`, `frontend/.oxlintrc.json`, `frontend/.prettierrc`, `frontend/tsconfig.json`); editor wiring **and format-on-save** live in the committed `.vscode/settings.json`; the only user settings are `files.autoSave` and `pylint.lintOnChange` (machine-scoped, so it can't live in the workspace).
2. **One package manager per side** — `uv` for Python (never pip, poetry or a bare `python -m venv`); `pnpm` for the frontend (never npm or yarn). Commit `uv.lock`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`.
3. **Latest stable versions that work together, never pinned in docs** — install with `uv add <pkg>` / `pnpm add <pkg>@latest` (no version), never a prerelease (`rc`, `beta`, `canary`, `next`, `dev`; check `pnpm view <pkg> dist-tags` / PyPI). When setting up or refreshing a project, follow [Keeping versions current](#keeping-versions-current): upgrade everything, run every check, and if the newest major of one tool breaks another, hold that one package at the newest major that passes and record why there (current holds: TypeScript 6, `@types/node` at the Node LTS major).
4. **Bare defaults** — backend = `main.py` + `core/` + one sample feature; frontend = `create-next-app` default. Add a library only when a feature needs it ([Libraries by use case](#7-libraries-by-use-case)).
5. **Size limits are lint rules, not advice** — files ≤ **500** lines, functions ≤ **100** lines, as **errors**, in backend and frontend. When one fires, split the file or function — never raise the limit, never add a disable comment.
6. **Structure is a lint rule** — every backend feature has the same files (`tests/test_structure.py`) and imports only in the routers → services → repositories direction (tach, `backend/tach.toml`). A new kind of module gets its own tach entry; never loosen `root_module = "forbid"`, and never run `tach sync` (tach's error output suggests it; it rewrites the rules to allow whatever the code imports).
7. **Check the editor, not just the CLI** — the smoke tests must show the same problems in the VS Code Problems panel as the CLI. A setting that was never seen working in the editor is a guess.
8. **Install the VS Code extensions yourself** ([Required extensions](#required-vs-code-extensions)) and uninstall Pylance; then ask the user to reload the window — batch every reload/open request into one message.
9. **Do not use** settings that don't exist or are deprecated: `ruff.cwd`, `ruff.lint.run`, `ruff.lint.select` / `ruff.lineLength` / `ruff.configuration` (they override `pyproject.toml`), `python.analysis.*` (Pylance only), `cursorpyright.*`, `typescript.tsdk` / `typescript.enablePromptUseWorkspaceTsdk` (use `js/ts.tsdk.path` / `js/ts.tsdk.promptToUseWorkspaceVersion`).
10. **Never put `options` (e.g. `typeAware`) in `frontend/.oxlintrc.json`** — VS Code opens the repo root, so that config is _nested_, and oxlint rejects root-only options there; the editor then silently drops the whole config. Type-aware linting comes from `--type-aware` in the `lint` script (CLI) and `oxc.typeAware` + `oxc.path.tsgolint` in `.vscode/settings.json` (editor).
11. **Ask before adding application-specific setup** — the items in [Application-specific setup](#application-specific-setup--ask-the-user-first) depend on what is being built. List the relevant ones, explain each in a line, and add only what the user approves. Tooling (linters, formatters, type strictness, the structure checks) is not on that list — set it up as this guide says; only **changing** the structure rules (a new kind of feature folder, a `tach.domain.toml` rule) is asked first.

### What runs where (verified)

| Check                                                                        | Tool                                                      | Rules in                                | Problems panel while editing                             | Whole-workspace scan                     |
| ---------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------- | ---------------------------------------- |
| Python lint                                                                  | Ruff                                                      | `pyproject.toml`                        | open files                                               | task `backend: ruff`                     |
| Python format + import order                                                 | Ruff (format on save)                                     | `pyproject.toml`                        | on save                                                  | task `backend: format`                   |
| Python types                                                                 | BasedPyright (`recommended`)                              | `pyproject.toml`                        | **every file**, open or not                              | task `backend: basedpyright`             |
| Function ≤ 100 lines (py)                                                    | flake8 + `flake8-max-function-length`                     | `pyproject.toml` (`[tool.flake8]`)      | open files                                               | task `backend: function length (flake8)` |
| File ≤ 500 lines (py)                                                        | pylint, only `too-many-lines`                             | `pyproject.toml`                        | open files                                               | task `backend: file length (pylint)`     |
| Layers routers → services → repositories                                     | tach (+ `tach check-external`: HTTP only in routers)      | `backend/tach.toml`, `tach.domain.toml` | open files (Tach extension)                              | task `backend: structure (tach)`         |
| Layout: required folders, nothing else, same layer rules, tests, no bypasses | pytest `tests/test_structure.py`                          | the test                                | —                                                        | task `backend: test`                     |
| No import cycles                                                             | BasedPyright `reportImportCycles` (part of `recommended`) | `pyproject.toml`                        | **every file**, open or not                              | task `backend: basedpyright`             |
| TS/TSX lint, size limits                                                     | oxlint (type-aware)                                       | `frontend/.oxlintrc.json`               | open files                                               | task `frontend: lint`                    |
| TS types                                                                     | `tsc` / VS Code TypeScript                                | `frontend/tsconfig.json`                | every file of a project once one of its files was opened | task `frontend: typecheck`               |
| Format JS/TS/JSON/CSS/MD/YAML                                                | Prettier (format on save)                                 | `frontend/.prettierrc`                  | on save                                                  | task `frontend: format`                  |
| Format TOML                                                                  | Even Better TOML                                          | defaults                                | on save                                                  | —                                        |

VS Code has **no global "lint the whole workspace" setting** — each extension decides. Only BasedPyright (`basedpyright.analysis.diagnosticMode: "workspace"`) and TypeScript (`js/ts.tsserver.experimental.enableProjectDiagnostics`) scan files you haven't opened. For everything else, **Tasks → `check: all`** runs every CLI check except the two audits and puts every file's problems in the Problems panel. **Empty Problems panel = clean code** when the CLI passes.

---

## Architecture: three layers

| Layer              | Location                                                                                                                   | Purpose                                                                    | Commit? |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------- |
| **Rules**          | `backend/pyproject.toml`, `backend/tach.toml`, `frontend/.oxlintrc.json`, `frontend/.prettierrc`, `frontend/tsconfig.json` | What to enforce — shared by CLI and editor                                 | Yes     |
| **Project wiring** | `.vscode/settings.json`, `extensions.json`, `tasks.json`                                                                   | Interpreter/tool paths, workspace diagnostics, formatters + format-on-save | Yes     |
| **Personal prefs** | VS Code user `settings.json`                                                                                               | `files.autoSave`, `pylint.lintOnChange`                                    | No      |

**Golden rule:** lint, type and format **rules** live in config files, never in VS Code settings.

---

## Application-specific setup — ask the user first

This template stays bare on purpose. The items below are what production FastAPI / Next.js apps commonly add (seen in Polar, Onyx, Sentry, the FastAPI full-stack template, cal.com, Dub, Supabase, create-t3-app), but whether and how depends on the application. **When setting up a new project, ask the user about each relevant item before adding it.**

| Side     | Item                                             | What it is                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Typical trigger                                                                |
| -------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| backend  | **ASGI server — always ask at setup**            | **Granian** (default; latest stable; Rust server) or `uvicorn[standard]` (second option; what FastAPI's own install uses, far larger community). On this app, 1 worker: Granian 13,416 req/s vs `uvicorn[standard]` 10,658 (+26% for Granian), plain `uvicorn` 4,660. Granian's free-threading support is experimental — see [Switching to uvicorn](#switching-to-uvicorn)                                                                                                                                                                                                                                                                                                                                                                                                                      | project setup                                                                  |
| backend  | `/health` (+ `/health/ready`)                    | liveness/readiness endpoint for load balancers and orchestrators                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | the app gets deployed                                                          |
| backend  | Request-ID middleware                            | an `X-Request-ID` per request, bound into every log line (`logger.contextualize`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | more than one service, or log search in production                             |
| backend  | Error contract                                   | one `AppError` base class + one handler in `main.py` → one JSON error shape                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | the first domain error                                                         |
| backend  | Production settings                              | `env` setting (dev/test/prod), OpenAPI docs off in prod, `SecretStr` secrets, `env_prefix`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | the first deployment                                                           |
| backend  | CORS                                             | `CORSMiddleware` with a `cors_origins` setting (never `*`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | the browser calls the backend directly                                         |
| backend  | Security headers, body-size limit, rate limiting | HSTS / body limits (often done by the proxy); Redis-backed rate limits                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | public endpoints, auth                                                         |
| backend  | Database                                         | SQLAlchemy async + asyncpg + Alembic, test DB with rollback per test (see [Libraries by use case](#7-libraries-by-use-case))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | the first persisted data                                                       |
| backend  | Redis                                            | app-wide client + `RedisRepositoryBase` (key prefix, TTL in seconds, typed values) — see [Redis pattern](#redis-pattern)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | caching, counters, locks, rate limits                                          |
| backend  | Background jobs / queues                         | **Taskiq** (async-first like BullMQ; Redis broker `taskiq-redis`, FastAPI + dishka integrations; still pre-1.0, marked Alpha) or **Celery** (mature, production standard, sync-first). Not set up in this template — research the current setup steps when chosen                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | work that must run outside the request (emails, imports, scheduled jobs)       |
| backend  | Observability                                    | Sentry (only when a DSN is set), OpenTelemetry / Logfire, or structlog instead of loguru                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | production monitoring                                                          |
| backend  | Docker                                           | multi-stage image with uv (`uv sync --locked --no-dev`), non-root `USER`, the chosen server (`granian --interface asgi --host 0.0.0.0 src.app.main:app`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | container deployment                                                           |
| backend  | Test extras                                      | `pytest-cov` with a threshold, `pytest-xdist`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | the suite grows or slows                                                       |
| backend  | Supply-chain cooldown                            | `[tool.uv] exclude-newer = "1 week"` — skip brand-new releases                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | team policy                                                                    |
| backend  | Auth: current user + guards                      | a dishka `CurrentUser` provider (REQUEST scope, built from `Request` — see the dishka section) + permission checks per route (Nest guards + `@CurrentUser`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | the first protected route                                                      |
| backend  | Database error mapping                           | part of the error contract: one handler maps `IntegrityError` (duplicate, missing foreign key) to 409/422 instead of a 500                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | the database lands                                                             |
| backend  | Transaction helper for jobs                      | outside a request there is no request-scoped session: one helper that opens a session and commits or rolls back (your team's `runInTransaction`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | jobs or scripts write to the database                                          |
| backend  | Events                                           | in-process domain events (a feature reacts to another without calling its services) and external ones (SNS/SQS, Kafka, Redis streams) — your team used EventEmitter + SNS                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | features react to each other's changes, or other services must hear about them |
| backend  | Feature `tasks/` and `listeners/` folders        | a feature's job handlers (`tasks/`) and event handlers (`listeners/`): each a module in `features/items/tach.domain.toml` that may use only its `services` and `schemas`, added to `REQUIRED_PACKAGES` in `tests/test_structure.py`, then copied to every feature (tach and the structure test reject the folder until then)                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | background jobs or events are added                                            |
| backend  | **gRPC** (service-to-service calls)              | `grpcio` (official; async API `grpc.aio`; Python 3.15 wheels) + `grpcio-tools` (code from `.proto` files), plus `grpcio-health-checking` / `grpcio-reflection`; dishka ships a `grpcio` integration. Alternatives: `betterproto2` (typed dataclass code) or Connect RPC (`connect-python`, also speaks HTTP/JSON) — both pre-1.0. Your team ran gRPC servers and clients between services. Layout: a feature's server handlers in `grpc/` (like `routers/`: they call only `services` and `schemas`; added to the layer rules and `REQUIRED_PACKAGES` like `tasks/`), outgoing clients in `repositories/` (another data source); generated code in its own folder, excluded from the linters; the gRPC server runs on its own port next to the HTTP app. Research the current setup when chosen | another service calls this one, or this one calls another service over gRPC    |
| backend  | Seed scripts                                     | an idempotent `scripts/seed.py` for dev/test data                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | dev environments need sample data                                              |
| both     | Frontend types from OpenAPI                      | export the backend's `openapi.json` and generate TypeScript types/client from it, so the frontend can't drift from the API — research the current generator when chosen                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | the frontend calls the backend                                                 |
| backend  | Structure rule changes                           | a new kind of feature folder (beyond `tasks/`, `listeners/`, `grpc/`) or any change to `features/items/tach.domain.toml`, `tach.toml` or the structure test — copied to every feature                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | the layout doesn't fit a real need                                             |
| backend  | Hard delete / purging old rows                   | real `DELETE`s or a job that purges soft-deleted rows after a retention period (the template only soft-deletes)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | privacy requests (GDPR), storage limits                                        |
| frontend | Security headers / CSP                           | `headers()` in `next.config.ts`: `X-Content-Type-Options`, `Referrer-Policy`, frame protection, `poweredByHeader: false`; CSP later                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | the app gets deployed                                                          |
| frontend | Env validation                                   | `@t3-oss/env-nextjs` + Zod: build fails on a missing/invalid env var                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | the first env var                                                              |
| frontend | `typedRoutes`                                    | `next.config.ts` `typedRoutes: true`: `<Link href>` checked against real routes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | more than a few routes                                                         |
| frontend | Observability                                    | Sentry / `instrumentation.ts` `onRequestError`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | production monitoring                                                          |
| frontend | E2E tests                                        | Playwright                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | real user flows exist                                                          |
| frontend | Extras                                           | `server-only` package (data layer), bundle analyzer, knip (unused code), React Compiler                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | when the need shows up                                                         |
| both     | `.editorconfig`                                  | shared indent / line-ending defaults for editors without per-language formatters                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | contributors use other editors                                                 |

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
uv add fastapi pydantic pydantic-settings granian loguru dishka
uv add --dev ruff basedpyright pytest pytest-asyncio httpx2 \
  flake8 flake8-max-function-length flake8-pyproject pylint tach pip-audit 'granian[reload]'
```

- `httpx2` — Starlette's `TestClient` now imports `httpx2` (Pydantic's successor to `httpx`) and warns `Using httpx with starlette.testclient is deprecated; install httpx2 instead` when only `httpx` is installed.
- `flake8-pyproject` — flake8 can't read `pyproject.toml` on its own (verified: settings in `[tool.flake8]` are ignored without it). The plugin reads `pyproject.toml` from the **current directory**, which is why `flake8.cwd` points at `backend/`.
- **Granian** is the ASGI server (Rust; FastAPI's docs list it as an alternative to Uvicorn). Run it with `--interface asgi`; the dev-only `granian[reload]` extra adds auto-reload. Ask the user at setup whether they want `uvicorn[standard]` instead ([Application-specific setup](#application-specific-setup--ask-the-user-first)).
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
  "PGH",   # no blanket `# noqa` / `# type: ignore` — name the rule
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
"importlib.import_module".msg = "Dynamic imports bypass the layer checks (tach). Import directly."

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
filterwarnings = ["error"] # a deprecation (e.g. Pydantic v1-style `class Config`) fails the tests
markers = [
  "unit: isolated tests, no DB/Redis dependency",
  "integration: tests that hit a real DB/Redis instance",
]
```

`backend/tach.toml` — the app-level layer rules (`main`, `core/`). They live in tach's own file, not `[tool.tach]` in `pyproject.toml`: the VS Code extension starts `tach server -c backend/tach.toml` from the repo root, and `-c` reads the whole file as tach config (`pyproject.toml` fails with `unknown field dependency-groups`). The CLI (`uv run tach check` in `backend/`) finds `tach.toml` on its own.

```toml
# NestJS-style layers: routers -> services -> repositories.
# Its own file (not [tool.tach] in pyproject.toml): the VS Code extension starts
# `tach server -c backend/tach.toml` from the repo root, and `-c` reads a whole file
# as tach config.
#
# Feature layers (routers -> services -> repositories, and another feature only through its
# services) live next to each feature: src/app/features/<name>/tach.domain.toml.
source_roots = ["."]
exclude = ["tests", "**/__pycache__", ".venv"]
root_module = "forbid"                         # every source file must belong to a module below
ignore_type_checking_imports = false           # `if TYPE_CHECKING:` imports follow the layers too

[external]
exclude = ["granian"] # the ASGI server is run as a command, never imported

[[modules]]
path = "src.app.main"
depends_on = [
  "src.app.app_module",
  "src.app.core.logger",
  "src.app.features.*.routers",
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
path = "src.app.common"
depends_on = []
utility = true          # shared by every feature (NestJS common/); never imports a feature

[[modules]]
path = "src.app.app_module"                     # root module (NestJS AppModule)
depends_on = ["src.app.features.*.dependencies"] # the only module that imports feature providers
```

`src/app/features/<name>/tach.domain.toml` — each feature's layer rules, copied with the folder. A tach _domain_ file: paths are relative to the feature, `//` paths are absolute. Because each feature has its own file, "same feature" is expressible: services may use **their own** repositories but only **another feature's services or schemas** — exactly what a Nest module exports. `constants/` and `utils/` are the feature's own (like your team's per-module folders): every layer may read `constants/`; `utils/` may use only `schemas/` and `constants/` (+ `models/` once a database exists), so business logic can't hide there. `cannot_depend_on_external` keeps FastAPI/Starlette in routers (`tach check-external`), and the `[[interfaces]]` block lets only `*Service` classes leave `services/`. `test_structure.py` requires the file in every feature and requires it to be **identical** to `features/items/tach.domain.toml`, so one feature's rules can't be loosened quietly.

```toml
# Layer rules for this feature — the same in every feature (tests/test_structure.py checks it).
# Paths are relative to this feature; "//" paths are absolute. Each path is a folder
# (e.g. "services" covers services/*.py).
# NestJS-style: routers -> services -> repositories; another feature only through its
# services (and its schemas for DTO types); constants/ and utils/ belong to this feature only.

[[modules]]
path = "routers"
depends_on = [
  "services",
  "schemas",
  "constants",
  "utils",
  "//src.app.features.*.services",
  "//src.app.features.*.schemas",
]

[[modules]]
path = "services"
depends_on = [
  "repositories",
  "schemas",
  "constants",
  "utils",
  "//src.app.features.*.services",
  "//src.app.features.*.schemas",
]
cannot_depend_on_external = ["fastapi", "starlette"] # HTTP stays in routers

[[modules]]
path = "repositories"
depends_on = ["schemas", "constants", "utils"]
cannot_depend_on_external = ["fastapi", "starlette"]

[[modules]]
path = "schemas"
depends_on = ["constants"]
cannot_depend_on_external = ["fastapi", "starlette"]

[[modules]]
path = "constants"
depends_on = []
cannot_depend_on_external = ["fastapi", "starlette"]

[[modules]]
path = "utils"
depends_on = ["schemas", "constants"]
cannot_depend_on_external = ["fastapi", "starlette"]

[[modules]]
path = "dependencies"
depends_on = ["repositories", "services", "constants"]

# Only service classes leave services/: a router can't reach a repository through a
# service module's imports.
[[interfaces]]
expose = [".*Service"]
from = ["services"]
```

Notes (each verified by running the tool):

- **BasedPyright `recommended`** reports `reportUnannotatedClassAttribute`: annotate attributes (`self._repository: ItemRepository = repository`) and Pydantic config (`model_config: ClassVar[ConfigDict] = ConfigDict(...)`). Annotate `@asynccontextmanager` functions `-> AsyncGenerator[None]`, not `AsyncIterator` (typeshed marks the latter deprecated). dishka types `provide` with `Any`, so its import carries `# pyright: ignore[reportUnknownVariableType]`.
- **`FAST001`** flags `response_model=` that repeats the return annotation — annotate the route's return type only.
- **`banned-api`** makes `from loguru import logger` an error everywhere except `core/logger.py`.
- **flake8** runs only `MFL`. `flake8-max-function-length` counts code lines only (it skips the `def` line, docstrings, blank lines and comments — the same as oxlint's `skipBlankLines` / `skipComments`).
- **pylint** runs only `too-many-lines` (`C0302`). It counts **every** line, blank and comment lines included — the frontend's `max-lines` is set to count every line too. Ruff has no line-count rule (checked in Ruff 0.17: only `PLR0915` statement counts and `C901` complexity).
- **tach** (rules in `tach.toml`, next section) mirrors a production NestJS layout — feature modules (`features/`), the root module (`app_module.py`, Nest's `AppModule`), app-wide setup (`core/`, like Nest's `config/` and database setup), shared code (`common/`, Nest's `common/`/`shared/`) — and checks imports between them: a router importing a repository fails (`Module 'src.app.features.items.routers' cannot depend on 'src.app.features.items.repositories'`), a repository importing a service fails, and with `root_module = "forbid"` a file that matches no module (e.g. `features/items/helpers.py`) fails as `Module '<root>' cannot depend on …` — but only if it imports or is imported; `test_structure.py` rejects it either way. Another feature's repositories, routers or dependencies are rejected too (`Module 'src.app.features.items.services' cannot depend on 'src.app.features.orders.repositories'`), through the per-feature domain files. Verified against NestJS's rules with 113 edge cases — every layer direction (own and other feature, `constants/`, `utils/`, `core/`, `common/`, `main`, the root module `app_module.py`: only it imports feature providers, only `main.py` imports it), import forms (inside a function, under `if TYPE_CHECKING:`, in `try/except`, `import … as`, star, relative, dynamic), a repository re-exported through a service module, a feature cycle, FastAPI in services/repositories/schemas, stray files and folders that import nothing, a loosened `tach.domain.toml`, a feature without tests, and `# tach-ignore` / `# noqa: TID251` / blanket `# noqa` / `# type: ignore`: 113/113 behave like Nest.
- **`tach check-external`** compares imports with `pyproject.toml`: a package imported but not declared (e.g. `pydantic`, which only arrives through FastAPI) or declared but never imported fails. `granian` is excluded in `tach.toml` (`[external] exclude`) because it runs as a command. The tach extension shows the same errors live (`Dependency 'pydantic' is not declared in package 'backend'`).
- **`test_structure.py`** covers what tach can't see: a file or folder outside the layout that imports nothing (tach only flags code that imports or is imported), a feature whose `tach.domain.toml` differs from `items`', a feature without `tests/features/<name>/test_*.py`, a `core/` file without a `tach.toml` module, and code that gets around the checks (`# tach-ignore`, `# noqa: TID…`, `reportImportCycles` ignores, `__import__(` / `import_module(`). Ruff `TID251` also bans `importlib.import_module`, and `PGH` rejects blanket `# noqa` / `# type: ignore`.
- **pytest 9** reads the native `[tool.pytest]` table (header shows `configfile: pyproject.toml`, `asyncio: mode=Mode.AUTO`).

### 4. Structure (NestJS-style feature modules)

```
backend/
├── pyproject.toml          ← every rule except layers
├── tach.toml               ← app-level layer rules (main, core, common); features have their own
├── .python-version
├── .env.example            ← settings to copy into .env (LOG_LEVEL, LOG_FORMAT)
├── uv.lock
├── src/app/
│   ├── main.py             ← create_app(): logger, routers, dishka (Nest main.ts)
│   ├── app_module.py       ← root module (Nest AppModule): dishka container with every feature's Provider — the only file that imports feature providers
│   ├── core/               ← app-wide setup (Nest config/ + database setup) — never imports a feature
│   │   ├── config.py       ← Settings (pydantic-settings, reads .env)
│   │   └── logger.py       ← loguru setup; the only place loguru is imported
│   ├── common/             ← code shared by 2+ features (NestJS common/) — never imports a feature
│   │   └── schemas.py      ← BaseSchema, Page[T], Limit/Offset (below)
│   └── features/
│       └── items/          ← sample feature (NestJS module) — copy it for a new one
│           ├── __init__.py
│           ├── routers/        HTTP only — Nest controllers; __init__.py combines them into one `router`
│           │   ├── __init__.py
│           │   └── items.py
│           ├── services/       business logic — Nest services
│           │   ├── __init__.py
│           │   └── items.py
│           ├── repositories/   data access (DB/Redis) — the only layer that touches storage
│           │   ├── __init__.py
│           │   └── items.py    (in-memory until a database is added)
│           ├── schemas/        Pydantic request/response models — Nest DTOs
│           │   ├── __init__.py
│           │   └── items.py
│           ├── constants/      fixed values used only by this feature (limits, mappings, enums)
│           │   └── __init__.py
│           ├── utils/          small helpers used only by this feature (formatting, transforming)
│           │   └── __init__.py
│           ├── dependencies.py dishka Provider — Nest module `providers`
│           └── tach.domain.toml this feature's layer rules (identical in every feature)
└── tests/
    ├── conftest.py         ← TestClient fixture (fresh app + container per test)
    ├── test_structure.py   ← fails on a missing or extra folder/file, edited layer rules, missing tests, bypasses
    └── features/items/     ← mirrors src/app/features/
```

Once a database exists, every feature also gets `models/` (SQLAlchemy models — Nest entities); see [Database pattern](#7-libraries-by-use-case).

Shared by 2+ features → `common/` (any feature may import it; it never imports a feature). Used by one feature → that feature's `constants/` or `utils/`.

`common/schemas.py` holds what every feature's schemas share (verified: unknown field → 422, `limit=0`/`101` or `offset=-1` → 422):

- `BaseSchema` — every request/response schema inherits it: unknown fields are rejected (`extra="forbid"`, like Nest's `ValidationPipe` `whitelist` + `forbidNonWhitelisted`), strings are trimmed
- `Page[T]` — every list endpoint returns `{"items": [...], "total": …, "limit": …, "offset": …}`, so the frontend handles every list the same way
- `Limit` / `Offset` — the list endpoint's query parameters (`limit` 1–100, `offset` ≥ 0), declared once

Responses: routes declare a Pydantic return type and no `response_class`, so FastAPI serializes with Pydantic in Rust (2x+ faster than `JSONResponse`; `ORJSONResponse`/`UJSONResponse` are deprecated) — verified: both routes take that path. FastAPI rejects a JSON body without `Content-Type: application/json` (`strict_content_type`, on by default). Pydantic v1-style code fails the checks: `.dict()`, `.parse_obj()`, `ORJSONResponse` are BasedPyright `reportDeprecated` warnings (fail with `failOnWarnings`), `class Config` fails pytest (`filterwarnings = ["error"]`) — verified.

Rules the tools enforce (details: `backend/CLAUDE.md` → NestJS-style structure):

- Every feature has `__init__.py`, `routers/`, `services/`, `repositories/`, `schemas/`, `constants/`, `utils/` (each a package with `__init__.py`), `dependencies.py`, `tach.domain.toml` (identical to `items`') and `tests/features/<name>/test_*.py` — and nothing else; `src/` holds only the layout; no bypass comments — `tests/test_structure.py`
- Imports go routers → services → repositories only; another feature is reachable only through its `services` (and `schemas` for DTO types), and only `*Service` classes leave `services/`; `constants/` and `utils/` are visible only inside the feature; files in the same layer folder may import each other; FastAPI/Starlette only in routers, `dependencies.py`, `main.py`, `core/` and `common/` — never in services, repositories, schemas, `constants/` or `utils/` (`tach check-external`) — tach
- One module per use-case area inside a layer folder (`services/items.py`, `services/item_exports.py`); split a file before it reaches 500 lines

Adding a feature `orders`:

1. Copy `src/app/features/items/` to `src/app/features/orders/` (its `tach.domain.toml` comes along — never edit it in one feature); rename the files inside the layer folders (`routers/items.py` → `routers/orders.py`, …), the classes and every import (tach rejects any import still pointing at `items`); point `routers/__init__.py` at the new router module.
2. Register the feature's `router` in `main.py` (`from src.app.features.orders.routers import router as orders_router` → `app.include_router(orders_router)`) and its provider in `app_module.py`.
3. Add `tests/features/orders/test_*.py` (the structure test requires it).
4. Run [Verify CLI](#verify-cli). tach already covers the new folder through the `features.*` globs.

### 5. Dependency injection — dishka

`features/<name>/dependencies.py` (one `Provider` per feature):

```python
from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType] -- dishka types it with Any
)

from src.app.features.items.repositories.items import ItemRepository
from src.app.features.items.services.items import ItemService


class ItemsProvider(Provider):
    """The feature's providers, like a Nest module's `providers` list."""

    @provide(scope=Scope.APP)  # in-memory store: one per app
    def repository(self) -> ItemRepository:
        return ItemRepository()

    @provide(scope=Scope.REQUEST)
    def service(self, repository: ItemRepository) -> ItemService:
        return ItemService(repository)
```

`app_module.py` — the root module, like Nest's `app.module.ts` next to `main.ts`:

```python
"""Root module (NestJS AppModule): the dishka container with every feature's Provider."""

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider

from src.app.features.items.dependencies import ItemsProvider


def create_container() -> AsyncContainer:
    return make_async_container(FastapiProvider(), ItemsProvider())
```

`routers/items.py` — `DishkaRoute` injects `FromDishka[...]` parameters without an `@inject` decorator per route:

```python
router = APIRouter(prefix="/items", tags=["items"], route_class=DishkaRoute)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_item(data: ItemCreate, service: FromDishka[ItemService]) -> ItemResponse:
    return await service.create(data)


@router.get("")
async def list_items(
    service: FromDishka[ItemService], limit: Limit = 20, offset: Offset = 0
) -> Page[ItemResponse]:
    return await service.list_items(limit=limit, offset=offset)
```

`routers/__init__.py` combines the feature's routers into one `router`, which `main.py` imports:

```python
"""The feature's HTTP routers (Nest controllers), combined into one `router` for main.py."""

from fastapi import APIRouter

from src.app.features.items.routers.items import router as items_router

router = APIRouter()
router.include_router(items_router)
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

**dishka and FastAPI together** — `list_items` above uses both: FastAPI parses the request (body, query/path/header parameters such as `limit`/`offset`, which appear in the OpenAPI docs); dishka (`FromDishka[...]`) builds everything you'd construct — services, repositories, DB sessions, clients — and stays out of the OpenAPI schema. FastAPI `Depends` only to group request parameters (_request decomposition_), never to build services or repositories.

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

Installed by default: `fastapi`, `granian`, `pydantic-settings` (config), `dishka` (DI), `loguru` (logging); dev: the tools above. Add the rest **only when a feature needs them**, with `uv add <pkg>` (latest stable):

| Need                      | Library                          | Install                                                      |
| ------------------------- | -------------------------------- | ------------------------------------------------------------ |
| Database ORM (PostgreSQL) | **SQLAlchemy** (async) + asyncpg | `uv add "sqlalchemy[asyncio]" asyncpg`                       |
| Migrations                | **Alembic**                      | `uv add alembic` → `uv run alembic init -t async migrations` |
| Cache, locks, rate limits | **redis** (`redis.asyncio`)      | `uv add redis`                                               |
| Outgoing HTTP calls       | **httpx2**                       | `uv add httpx2` (already a dev dependency for tests)         |

**Database pattern** (verified end to end on Python 3.15 with SQLAlchemy 2.1, dishka, redis-py 8, SQLite and fakeredis: Ruff, BasedPyright `recommended`, tach, flake8 and the structure test all pass; a successful request commits, a request that raises after an insert rolls back; every row gets a time-ordered UUIDv7 `id` and UTC `created_at`/`updated_at`, `updated_at` moves on update, and a soft-deleted row is hidden from `get_by_id`, `paginate` and `count`). This is the NestJS-style repository layer your team used: one shared base in `common/`, thin feature repositories on top — the same shape Polar uses in production (`server/polar/kit/repository/base.py`).

**Who does what:** SQLAlchemy talks to the database (models, queries, sessions). dishka creates and hands out the objects: one engine per app, a fresh session per request, the repository built with that session, the service with that repository — and it commits or rolls back when the request ends.

`src/app/common/repository.py` — the ORM `Base` (audit columns on every table, the same set Polar's `RecordModel` and your team's entities have) and the generic repository every feature inherits:

```python
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid7

from sqlalchemy import DateTime, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for every ORM model (features/<name>/models/); every table gets these columns."""

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)  # UUIDv7: time-ordered
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class RepositoryBase[M: Base]:
    """Generic data access shared by every feature repository.

    Feature repositories inherit it and add only their own queries. Repositories flush but never
    commit: the request-scoped session provider commits or rolls back once per request. Every
    query starts from `base_statement()`, which hides soft-deleted rows.
    """

    def __init__(self, session: AsyncSession, model: type[M]) -> None:
        self.session: AsyncSession = session
        self.model: type[M] = model

    def base_statement(self) -> Select[M]:
        return select(self.model).where(self.model.deleted_at.is_(None))

    async def get_by_id(self, entity_id: UUID) -> M | None:
        return await self.get_one_or_none(self.base_statement().where(self.model.id == entity_id))

    async def get_one_or_none(self, statement: Select[M]) -> M | None:
        return (await self.session.scalars(statement)).one_or_none()

    async def get_all(self, statement: Select[M]) -> Sequence[M]:
        return (await self.session.scalars(statement)).all()

    async def paginate(self, statement: Select[M], *, limit: int, offset: int = 0) -> Sequence[M]:
        return await self.get_all(statement.limit(limit).offset(offset))

    async def count(self, statement: Select[M]) -> int:
        total = await self.session.scalar(select(func.count()).select_from(statement.subquery()))
        return total or 0

    async def create(self, obj: M) -> M:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def soft_delete(self, obj: M) -> None:
        obj.deleted_at = utc_now()
        await self.session.flush()
```

Audit columns — why each one:

- `id` — **UUIDv7** primary key (`uuid.uuid7`, stdlib since Python 3.14): one ID used everywhere — joins, URLs, responses. Time-ordered, so new rows land at the end of the index like an integer key (random UUIDv4 keys scatter inserts); not guessable like `1, 2, 3`; made in Python, so an object has its `id` before the insert. PostgreSQL 18 also has a native `uuidv7()`. Response schemas declare `id: UUID`
- `created_at` / `updated_at` — set in Python (`utc_now`, as Polar does), not by the database: a server-side `onupdate` value would need a reload, and a lazy load fails under async SQLAlchemy
- `deleted_at` — soft delete: `soft_delete()` keeps the row, `base_statement()` hides it from every read. Hard deletes and purging old rows are a separate decision — ask

`src/app/core/database.py` — engine per app, session per request; dishka sends the request's exception into the generator, so the session commits only when the request succeeded:

```python
from collections.abc import AsyncGenerator, AsyncIterator

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType] -- dishka types it with Any
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.app.core.config import get_settings


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def engine(self) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(get_settings().database_url.get_secret_value())
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncGenerator[AsyncSession, BaseException | None]:
        async with factory() as session:
            exc = yield session  # dishka sends the request's exception, if any
            if exc is None:
                await session.commit()
            else:
                await session.rollback()
```

A feature on the database — `models/` (Nest entities), a repository that inherits the base, and request-scoped providers:

```python
# features/items/models/items.py
from sqlalchemy.orm import Mapped, mapped_column

from src.app.common.repository import Base


class Item(Base):
    __tablename__: str = "items"

    name: Mapped[str] = mapped_column()  # id and timestamps come from Base
```

```python
# features/items/repositories/items.py
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.common.repository import RepositoryBase
from src.app.features.items.models.items import Item


class ItemRepository(RepositoryBase[Item]):
    """Only this feature's own queries live here; generic ones come from RepositoryBase."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Item)

    async def list_by_name(self, name: str) -> Sequence[Item]:
        return await self.get_all(self.base_statement().where(Item.name == name))
```

The service keeps returning Pydantic schemas: it maps models to `ItemResponse`, so no SQLAlchemy object leaves the service.

Wiring checklist:

- `uv add "sqlalchemy[asyncio]" asyncpg` (and `alembic`); `database_url: SecretStr` in `Settings` (`postgresql+asyncpg://…` in `.env`, add it to `.env.example`); add `DatabaseProvider()` to `create_container()` in `app_module.py`
- `backend/tach.toml`: add `"asyncpg"` (and `"aiosqlite"` if used for tests) to `[external] exclude` — database drivers are loaded from the URL, never imported, so `tach check-external` would report them as unused (verified); add a module `src.app.core.database` (`depends_on = []`) and add `"src.app.core.database"` to `src.app.app_module`'s `depends_on`
- **Every** feature gets a `models/` package (empty if it has no tables): add `"models"` to `REQUIRED_PACKAGES` in `tests/test_structure.py`, replace `features/items/tach.domain.toml` with the version below (repositories, services and utils may use `models`; models may use `constants`) and copy it to every feature — the structure test requires identical copies (verified on the DB build):

```toml
# Layer rules for this feature — the same in every feature (tests/test_structure.py checks it).
# Paths are relative to this feature; "//" paths are absolute. Each path is a folder
# (e.g. "services" covers services/*.py).
# NestJS-style: routers -> services -> repositories; another feature only through its
# services (and its schemas for DTO types); constants/ and utils/ belong to this feature only.

[[modules]]
path = "routers"
depends_on = [
  "services",
  "schemas",
  "constants",
  "utils",
  "//src.app.features.*.services",
  "//src.app.features.*.schemas",
]

[[modules]]
path = "services"
depends_on = [
  "models",
  "repositories",
  "schemas",
  "constants",
  "utils",
  "//src.app.features.*.services",
  "//src.app.features.*.schemas",
]
cannot_depend_on_external = ["fastapi", "starlette"] # HTTP stays in routers

[[modules]]
path = "repositories"
depends_on = ["models", "schemas", "constants", "utils"]
cannot_depend_on_external = ["fastapi", "starlette"]

[[modules]]
path = "schemas"
depends_on = ["constants"]
cannot_depend_on_external = ["fastapi", "starlette"]

[[modules]]
path = "models"
depends_on = ["constants"]
cannot_depend_on_external = ["fastapi", "starlette"]

[[modules]]
path = "constants"
depends_on = []
cannot_depend_on_external = ["fastapi", "starlette"]

[[modules]]
path = "utils"
depends_on = ["models", "schemas", "constants"]
cannot_depend_on_external = ["fastapi", "starlette"]

[[modules]]
path = "dependencies"
depends_on = ["repositories", "services", "constants"]

# Only service classes leave services/: a router can't reach a repository through a
# service module's imports.
[[interfaces]]
expose = [".*Service"]
from = ["services"]
```

- Ruff — make "storage only in repositories" an error: add `"sqlalchemy".msg = "Database access goes through repositories."` and `"redis".msg = "Redis access goes through repositories."` to `[tool.ruff.lint.flake8-tidy-imports.banned-api]`, and `TID251` to `per-file-ignores` for `src/app/core/database.py`, `src/app/core/redis.py`, `src/app/common/*repository.py`, `src/app/features/*/repositories/*.py`, `src/app/features/*/models/*.py` and `src/app/features/*/dependencies.py` (verified: a `sqlalchemy` or `redis` import in a service is then a `TID251` error)
- Repositories **flush, never commit**; only the session provider commits or rolls back. No unbounded queries — list endpoints call `paginate` and `count` on the same `base_statement()` and return `Page[T]`
- Alembic: `uv run alembic init -t async migrations`, set `target_metadata = Base.metadata` (from `src.app.common.repository`); never edit an existing migration; review autogenerate output; run `alembic upgrade head` in CI/CD, never at app startup
- Tests: services and repositories now need a session — integration tests use a real test database and roll back after each test

### Redis pattern

Only when the user approves Redis (same verified build as above). Unlike the database there is **no per-request session and no commit/rollback**: one client (with its connection pool) serves the whole app, and redis-py's async client must be closed explicitly with `aclose()` (it has no destructor). Polar does the same.

`src/app/core/redis.py`:

```python
from collections.abc import AsyncIterator

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType] -- dishka types it with Any
)
from redis.asyncio import Redis

from src.app.core.config import get_settings


class RedisProvider(Provider):
    @provide(scope=Scope.APP)  # one client (and connection pool) for the whole app
    async def client(self) -> AsyncIterator[Redis]:
        url = get_settings().redis_url.get_secret_value()
        client = Redis.from_url(url, decode_responses=True)  # pyright: ignore[reportUnknownMemberType] -- redis-py types **kwargs as Any
        yield client
        await client.aclose()  # async clients have no destructor; close on shutdown
```

Two shared bases live in `common/`:

`src/app/common/redis_repository.py` — generic Redis access (key prefix per feature, TTL in **seconds**, typed Pydantic values) for counters, locks and custom caches:

```python
from uuid import UUID

from pydantic import BaseModel
from redis.asyncio import Redis


class RedisRepositoryBase:
    """Generic Redis access shared by every feature's Redis repository.

    Keys are namespaced per feature (`<prefix>:<part>:<part>`), values are typed Pydantic JSON,
    and every write expires (TTL in **seconds**) unless told otherwise. Feature repositories add
    their own key layouts and commands (counters, locks, sets) on top.
    """

    def __init__(self, redis: Redis, prefix: str, default_ttl_seconds: int | None = 3600) -> None:
        self.redis: Redis = redis
        self.prefix: str = prefix
        self.default_ttl_seconds: int | None = default_ttl_seconds

    def key(self, *parts: str | int | UUID) -> str:
        return ":".join([self.prefix, *map(str, parts)])

    async def get_model[T: BaseModel](self, model: type[T], *parts: str | int | UUID) -> T | None:
        raw: bytes | str | None = await self.redis.get(self.key(*parts))
        return None if raw is None else model.model_validate_json(raw)

    async def set_model(
        self, value: BaseModel, *parts: str | int | UUID, ttl_seconds: int | None = None
    ) -> None:
        ttl = self.default_ttl_seconds if ttl_seconds is None else ttl_seconds
        _ = await self.redis.set(self.key(*parts), value.model_dump_json(), ex=ttl)

    async def delete(self, *parts: str | int | UUID) -> None:
        _ = await self.redis.delete(self.key(*parts))
```

`src/app/common/cached_repository.py` — **cache-aside in front of a database repository** (the NestJS `Cached<X>Repository` pattern your team used): reads try Redis, fall back to the database repository and cache the result; writes go through the database repository and then delete the cached copy:

```python
from uuid import UUID

from pydantic import BaseModel
from redis.asyncio import Redis

from src.app.common.redis_repository import RedisRepositoryBase
from src.app.common.repository import Base, RepositoryBase


class CachedRepositoryBase[M: Base, S: BaseModel](RedisRepositoryBase):
    """Cache-aside in front of a database repository (the NestJS `Cached<X>Repository` pattern).

    Reads try Redis first, fall back to the database repository and cache the result; writes go
    through the database repository and then **delete** the cached copy (`invalidate_id`). Values
    are cached as Pydantic schemas `S`, so ORM objects never go into Redis.
    """

    def __init__(
        self,
        redis: Redis,
        repository: RepositoryBase[M],
        schema: type[S],
        prefix: str,
        default_ttl_seconds: int | None = 300,
    ) -> None:
        super().__init__(redis, prefix, default_ttl_seconds)
        self.repository: RepositoryBase[M] = repository
        self.schema: type[S] = schema

    async def get_by_id(self, entity_id: UUID) -> S | None:
        cached = await self.get_model(self.schema, "id", entity_id)
        if cached is not None:
            return cached
        entity = await self.repository.get_by_id(entity_id)
        if entity is None:
            return None
        value = self.schema.model_validate(entity, from_attributes=True)
        await self.set_model(value, "id", entity_id)
        return value

    async def invalidate_id(self, entity_id: UUID) -> None:
        await self.delete("id", entity_id)
```

A feature's cached repository lives in its `repositories/` folder next to the database one:

```python
# features/items/repositories/items_cached.py
from redis.asyncio import Redis

from src.app.common.cached_repository import CachedRepositoryBase
from src.app.features.items.models.items import Item
from src.app.features.items.repositories.items import ItemRepository
from src.app.features.items.schemas.items import ItemResponse


class CachedItemRepository(CachedRepositoryBase[Item, ItemResponse]):
    """Cache-aside reads for items; keys live under `items:`."""

    def __init__(self, redis: Redis, repository: ItemRepository) -> None:
        super().__init__(redis, repository, ItemResponse, prefix="items", default_ttl_seconds=300)
```

The service reads through the cache and **invalidates after every write**:

```python
# features/items/services/items.py (excerpt)
    async def get(self, item_id: UUID) -> ItemResponse | None:
        return await self._cache.get_by_id(item_id)

    async def rename(self, item_id: UUID, name: str) -> ItemResponse | None:
        item = await self._repository.get_by_id(item_id)
        if item is None:
            return None
        item.name = name
        await self._repository.session.flush()
        await self._cache.invalidate_id(item_id)  # write, then delete the cached copy
        return ItemResponse(id=item.id, name=item.name)
```

```python
# features/items/dependencies.py
class ItemsProvider(Provider):
    """The feature's providers, like a Nest module's `providers` list."""

    @provide(scope=Scope.REQUEST)
    def repository(self, session: AsyncSession) -> ItemRepository:
        return ItemRepository(session)

    @provide(scope=Scope.REQUEST)
    def cached_repository(self, redis: Redis, repository: ItemRepository) -> CachedItemRepository:
        return CachedItemRepository(redis, repository)

    @provide(scope=Scope.REQUEST)
    def service(self, repository: ItemRepository, cache: CachedItemRepository) -> ItemService:
        return ItemService(repository, cache)
```

Verified behaviour (SQLite + fakeredis): first read misses → loads from the database → cached with a 300 s TTL; the next read is served from Redis; a row changed **without** invalidation keeps serving the stale value until the TTL expires (that's the risk — always invalidate); update + `invalidate_id` → the next read is fresh; unknown id → `None`.

Wiring checklist:

- `uv add redis` (latest stable); `uv add --dev fakeredis` for tests (`FakeAsyncRedis(decode_responses=True)`, provided in place of `RedisProvider`)
- `redis_url: SecretStr` in `Settings` (`redis://user:pass@host:6379/0` in `.env`, add it to `.env.example`); add `RedisProvider()` to `create_container()` in `app_module.py`
- `backend/tach.toml`: add a module `src.app.core.redis` (`depends_on = []`) and add `"src.app.core.redis"` to `src.app.app_module`'s `depends_on`
- Keys always through `self.key(...)` so every key carries the feature prefix; every write has a TTL unless there is a reason not to
- Caching pattern: cache-aside (above) by default; delete the key after a write, never update it in place. Write-through only when a read right after a write must come from the cache; never write-behind (data loss if Redis fails before the flush)

### Switching to uvicorn

Only when the user picks `uvicorn[standard]` over Granian (verified on this app: 10,658 req/s with uvloop + httptools; plain `uvicorn` without the extra is 2.3× slower, so always install `[standard]`):

```bash
cd backend
uv remove granian
uv remove --dev granian
uv add 'uvicorn[standard]'   # latest stable; --reload is built in
uv run uvicorn src.app.main:app --reload                                  # dev
uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --workers 2    # prod
```

Then change the `backend: dev` task in `.vscode/tasks.json` and the README quick start to the dev command above, and in `backend/tach.toml` change `[external] exclude = ["granian"]` to `["uvicorn"]` — the server runs as a command, so `tach check-external` would otherwise report it as unused.

### 8. Verify CLI (backend)

```bash
cd backend
uv run ruff check src tests
uv run ruff format --check src tests
uv run basedpyright
uv run flake8 src tests
uv run pylint src tests
uv run tach check
uv run tach check-external
uv run pytest
uv run pip-audit
```

All must pass. Then boot once: `uv run granian --interface asgi src.app.main:app` → `curl -X POST localhost:8000/items -H 'content-type: application/json' -d '{"name":"Pen"}'` returns `{"id":"<UUIDv7>","name":"Pen"}`; `curl localhost:8000/items` returns `{"items":[…],"total":1,"limit":20,"offset":0}`.

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
        "skipBlankLines": false,
        "skipComments": false
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
- Size limits: `max-lines` 500 counting every line (like pylint on the backend) and `max-lines-per-function` 100 counting code lines only (like flake8). Test files are exempt from the function limit (a suite is one `describe` callback); shadcn's generated `src/components/ui/**` is exempt from return types and both limits (`shadcn add --overwrite` would undo hand edits). React components count as functions — split a component over 100 lines.
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

| Task                                 | Command (cwd)                                                                               | Problem matcher                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `backend: dev`                       | `uv run granian --interface asgi --reload src.app.main:app` (backend)                       | —                                                                                |
| `backend: ruff`                      | `uv run ruff check --output-format concise src tests`                                       | `ruff`                                                                           |
| `backend: basedpyright`              | `uv run basedpyright`                                                                       | `basedpyright` (absolute paths)                                                  |
| `backend: function length (flake8)`  | `uv run flake8 --color never src tests`                                                     | `flake8`                                                                         |
| `backend: file length (pylint)`      | `uv run pylint src tests --score=n --msg-template='{path}:{line}:{column}: {msg_id} {msg}'` | `pylint`                                                                         |
| `backend: structure (tach)`          | `uv run tach check; s=$?; uv run tach check-external                                        |                                                                                  | s=1; exit $s` | `tach` (`[FAIL] file:line:` when piped, `❌ file:line:` in a terminal — the pattern accepts both) |
| `backend: format`                    | `uv run ruff format --check src tests`                                                      | —                                                                                |
| `backend: test`                      | `uv run pytest --tb=line`                                                                   | `pytest` (failing assertion line)                                                |
| `frontend: dev`                      | `pnpm run dev` (frontend)                                                                   | —                                                                                |
| `frontend: lint`                     | `pnpm run --silent lint --format unix`                                                      | `oxlint`                                                                         |
| `frontend: typecheck`                | `pnpm run typecheck`                                                                        | `$tsc`, `fileLocation` = `frontend/`                                             |
| `frontend: format` / `test`          | `pnpm run format:check` / `pnpm run test`                                                   | —                                                                                |
| `backend: audit` / `frontend: audit` | `uv run pip-audit --progress-spinner off` / `pnpm run audit`                                | — (not part of `check: all`: they report vulnerable packages, not file problems) |
| **`check: all`**                     | every task above except `dev` and the two audits, in parallel                               | each task's own                                                                  |

Run **Tasks: Run Task → `check: all`** for a full-workspace scan: every file's problems land in the Problems panel (verified: entries from all eight tools appeared), one owner per tool, so a rerun of one task replaces only its own entries. Task problems stay until that task runs again.

- Task entries carry the source `<tool> (task)` (e.g. `tach (task)`); live editor entries carry the plain tool name (`tach`). A task entry is a snapshot of its last run: it stays — even for a file that was fixed or deleted — until that task runs again, so rerun `check: all` after big changes. The Tach extension re-checks a file only when it is opened or saved: its server ignores edits (`Received unknown notification: textDocument/didChange` in Output → **Tach**), so after an agent or `git` changes a file on disk its old errors stay. Clear them with **Tach: Restart Server** (or close and reopen the file).
- Every non-composite task sets `NO_COLOR=1` (and the BasedPyright task also `FORCE_COLOR=0`, which BasedPyright needs; Ruff reads any `FORCE_COLOR` as "on", so it isn't global), and flake8 gets `--color never`. VS Code runs tasks in a terminal, where these tools print colour codes otherwise, and the problem patterns would then match nothing (verified by running each task command in a pseudo-terminal against real violations).
- `check: all` runs its tasks **in parallel** (one terminal each). Keep it that way: with `"dependsOrder": "sequence"` VS Code stops at the first task that fails, and the remaining tools never report.
- Agents: the Claude Code `getDiagnostics` tool returns extension diagnostics only, not task problem-matcher results. Ask the user which sources appear in Problems after running `check: all`.
- Never add `"runOn": "folderOpen"` (it opens terminals on every reload) unless the user asks.

---

## User settings (once per machine)

Some settings only work from the user `settings.json`, because VS Code ignores _machine_-scoped settings in a workspace file (scopes checked in each extension's `package.json`). The agent may add these entries itself — tell the user what was added.

`~/Library/Application Support/Code/User/settings.json` (Cursor: `.../Cursor/User/settings.json`):

```json
{
  "files.autoSave": "onFocusChange",
  "pylint.lintOnChange": true
}
```

- `files.autoSave: "onFocusChange"` — a personal preference, so it stays out of the repo. Auto-save fires the workspace's format-on-save and fix-on-save when you click away from a file. It saves only files with **unsaved edits**: a file changed on disk by an agent isn't dirty, so nothing runs until you type in it or press Cmd+S.
- `pylint.lintOnChange: true` — Pylint re-checks while you type. Its scope is `machine`, so a workspace value is ignored; without it Pylint checks on open and save only. Pylint reads it only when its server starts: after adding it run **Pylint: Restart Server** (or reload the window) — verified in Output → **Pylint**: `"lintOnChange": true`, then every unsaved edit triggers a lint run.

How the agent edits it:

- The file is JSON **with comments** and holds the user's other settings: add or change only these keys with a targeted edit — never rewrite the file or drop entries.
- Remove these if present, because they fight the repo's rules: `ruff.lint.select`, `ruff.lineLength`, `ruff.configuration` (Ruff's default `configurationPreference: "editorFirst"` lets them override `pyproject.toml`), and any `python.analysis.*` (Pylance only).
- Language blocks (`[python]`, `[typescript]`, …) may stay; the workspace file sets them anyway.

Restarts are a setup-time thing only: after changing user settings or (un)installing extensions. During normal work every checker updates live; the only other time is after an agent or `git` deletes or rewrites many files behind the editor (see [Troubleshooting](#troubleshooting)).

**Trust the folder** (user, once): when VS Code asks _"Do you trust the authors of the files in this folder?"_, choose **Trust**. In Restricted Mode, VS Code ignores `ruff.interpreter` and `oxc.path.tsgolint` from the workspace file (both are listed under `restrictedConfigurations`), so Ruff falls back to a bundled copy and oxlint loses its type-aware rules.

---

## Verify CLI

```bash
cd backend && uv run ruff check src tests && uv run ruff format --check src tests && uv run basedpyright \
  && uv run flake8 src tests && uv run pylint src tests && uv run tach check && uv run tach check-external && uv run pytest && uv run pip-audit
cd ../frontend && pnpm run lint && pnpm run typecheck && pnpm run format:check \
  && pnpm run test && pnpm run build && pnpm run audit
```

All must pass.

## Verify editor (smoke test — delete after)

An agent can't see VS Code by itself. Two channels exist:

- **Claude Code's IDE connection.** The user runs `/ide` and picks VS Code. The agent then calls `getDiagnostics` (per file or all files) and gets exactly what the editor shows: Ruff, BasedPyright, Flake8, Pylint, tach, oxc, ts. It does **not** return task (problem-matcher) results, the `<tool> (task)` entries.
- **The user.** Some steps need a human in the editor. Ask for all of them in **one** message (the user may not be around for several round trips), and ask for a screenshot of the Problems tab where the agent can't read it.

### Step 0 — editor ready (user)

One message to the user covering: **trust the folder** when VS Code asks → install the extensions ([Required extensions](#required-vs-code-extensions)) → **Developer: Reload Window** → **Python: Select Interpreter → `backend/.venv/bin/python`** → **TypeScript: Select TypeScript Version → Use Workspace Version** (turns on the Next.js TypeScript plugin; VS Code needs this approval once and settings can't give it) → `/ide` in Claude Code. The Python extensions start only when a `.py` file is open: their activation looks for `pyproject.toml` / `*.py` at the **workspace root**, and this repo keeps them in `backend/`. So a Python file must be open once per session; BasedPyright then scans the whole workspace.

### Step 1 — create every smoke file (agent)

**Backend** — create `backend/src/app/features/items/smoke.py` (a function over 100 lines and a file over 500 lines):

```bash
cd backend && python3 -c "
body = ''.join(f'    n += {i}\n' for i in range(101))
open('src/app/features/items/smoke.py', 'w').write(
    '# SMOKE TEST: delete after verifying\nimport os\n\nfrom src.app.features.items.repositories.items import ItemRepository\n\n\n'
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

Also expect, source **tach** (verified), on `smoke.py` line 4: `Module '<root>' cannot depend on 'src.app.features.items.repositories'` (a file outside the feature module types). Type a character in `smoke.py` and click away: auto-save runs Ruff — the unused imports disappear.

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
# router skips the service, and reaches a repository through a service module (tach)
printf '\nfrom src.app.features.items.repositories.items import ItemRepository  # SMOKE TEST\nfrom src.app.features.items.services.items import ItemService as _S  # SMOKE TEST\nfrom src.app.features.items.services.items import ItemRepository as _R  # SMOKE TEST\n\n_SMOKE = (ItemRepository, _S, _R)\n' >> src/app/features/items/routers/items.py
# HTTP in a service (tach check-external)
printf '\nfrom fastapi import HTTPException  # SMOKE TEST\n\n_SMOKE_HTTP = HTTPException\n' >> src/app/features/items/services/items.py
# feature folder missing its files (pytest)
mkdir -p src/app/features/orders/routers && touch src/app/features/orders/__init__.py src/app/features/orders/routers/__init__.py
printf 'from fastapi import APIRouter\n\nrouter = APIRouter(prefix="/orders")\n' > src/app/features/orders/routers/orders.py
uv run tach check   # expect [FAIL] … Module 'src.app.features.items.routers' cannot depend on 'src.app.features.items.repositories', and … 'ItemRepository' is not part of the public interface for 'src.app.features.items.services'
uv run tach check-external   # expect [FAIL] … Module 'src.app.features.items.services' cannot depend on external package 'fastapi'
uv run pytest -q    # expect … src/app/features/orders/ is missing: dependencies.py, tach.domain.toml, services/, repositories/, schemas/, constants/, utils/ (and: tests/features/orders/ has no test_*.py files; src/app/features/items/ has entries outside the layout: smoke.py, smoke_closed.py)
```

**Pre-commit hook** — must refuse a commit while any smoke file exists:

```bash
git add -A && git commit -m "smoke: must be blocked"; echo "exit=$?"   # expect exit=1 and no new commit (git log)
git reset -q                                                          # unstage again
```

### Step 2 — one batched request to the user

> Please, in VS Code: (1) open `backend/src/app/features/items/smoke.py`, `backend/src/app/features/items/routers/items.py`, and the three `frontend/src/app/smoke*` files — but **not** `smoke_closed.py`; (2) in `smoke.py` and `frontend/src/app/smoke.ts` type one space and press Cmd+S; (3) **Tasks: Run Task → `check: all`**, wait for every terminal to finish; (4) send a screenshot of the Problems tab, then reply "done".

### Step 3 — verify (agent)

- **Editor checks** — `getDiagnostics` on each smoke file must show every row of the backend and frontend tables above, plus, source **tach** (verified live): on `routers/items.py` `Cannot use '…repositories.items.ItemRepository'. Module 'src.app.features.items.routers' cannot depend on …` and `The path '…services.items.ItemRepository' is not part of the public interface …`; on `services/items.py` `Module 'src.app.features.items.services' cannot depend on external package 'fastapi'`.
- **Whole-workspace mode** — `smoke_closed.py` (never opened) must show the basedpyright type error.
- **Fix/format on save** — read the files from disk: `smoke.py` no longer has `import os`; `smoke.ts` has single quotes, semicolons and no `readFile` import.
- **Tasks** — in the screenshot, entries with sources `ruff (task)`, `basedpyright (task)`, `flake8 (task)`, `pylint (task)`, `tach (task)`, `pytest (task)` (orders missing files), `oxlint (task)` and `tsc (task)`.
- If a task source is missing, run that task's command inside a pseudo-terminal and match its pattern by hand — tools print differently in a terminal than in a pipe: `script -q /dev/null sh -c '<command>' < /dev/null` with the task's `env`, then test the `regexp` from `tasks.json` against each line.

### Step 4 — clean up (agent, then user)

```bash
git checkout -- backend/src/app/features/items/routers/items.py backend/src/app/features/items/services/items.py
rm -r backend/src/app/features/orders
rm backend/src/app/features/items/smoke.py backend/src/app/features/items/smoke_closed.py
rm frontend/src/app/smoke.ts frontend/src/app/smoke-size.ts frontend/src/app/smoke-jsx.tsx
git status --short   # must be empty
```

Then ask the user to close the deleted files' tabs, run **TypeScript: Restart TS Server** (with a `.ts`/`.tsx` file active) and **Tach: Restart Server**, and one more **`check: all`** — tach keeps errors for files changed on disk and task entries stay until their task reruns, so without this the Problems tab keeps showing the deleted smoke files. A final `getDiagnostics` (all files) must return no errors.

---

## Keeping versions current

Run at setup and whenever refreshing the template (commands verified):

```bash
cd backend
uv tree --outdated --depth 1     # direct dependencies with a newer release
uv lock --upgrade && uv sync     # newest versions that satisfy every constraint together
cd ../frontend
pnpm outdated                    # current vs latest
pnpm update                      # newest versions inside the package.json ranges
pnpm add <pkg>@latest            # move a package to a new major on purpose
```

Then run [Verify CLI](#verify-cli) and the [editor smoke test](#verify-editor-smoke-test--delete-after). `uv lock --upgrade` only picks versions that satisfy every package's requirements together; `pnpm` respects peer dependencies. A newest major that resolves but breaks a check (types, lint, build, editor) is held back:

| Held back     | At                  | Why                                                                                                                                                    | Revisit when                                                      |
| ------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| `typescript`  | 6                   | TypeScript 7 passes `tsc`, oxlint and `next build`, but ships no `lib/tsserver.js`, so VS Code's project diagnostics and the Next.js plugin don't work | VS Code's built-in TypeScript supports 7 with project diagnostics |
| `@types/node` | Node LTS major (24) | must match the Node version in use (`.nvmrc` = `lts/*`), not the newest Node                                                                           | the next Node LTS                                                 |

Python is the newest stable CPython (`.python-version`, `requires-python`, `pythonVersion`, Ruff `target-version` — keep all four equal); upgrade uv first (`brew upgrade uv`), since its list of Python builds ships with it.

---

## Git pre-commit hook

`.githooks/pre-commit` runs the fast checks (every backend check except `pip-audit`, frontend lint/typecheck/format/test) and blocks the commit when one fails. Git doesn't enable committed hooks by itself — once per clone:

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
| `test_feature_has_required_files` fails                                                             | The feature folder is missing one of `__init__.py`, `dependencies.py`, `tach.domain.toml`, or a layer package (`routers/`, `services/`, `repositories/`, `schemas/`, `constants/`, `utils/`, each with `__init__.py`)                                                                                                                                                              |
| `test_feature_has_nothing_else` / `test_app_has_nothing_else` fails                                 | A file or folder sits outside the layout — move the code into a layer folder (one feature) or `common/` (2+ features). A genuinely new kind of folder: ask first, then add it to the layer rules and `REQUIRED_PACKAGES`                                                                                                                                                           |
| `test_feature_layer_rules_match_the_template` fails                                                 | One feature's `tach.domain.toml` was edited — copy `features/items/tach.domain.toml` over it. Rule changes go into `items`' file and are copied to every feature (ask first)                                                                                                                                                                                                       |
| `test_feature_has_tests` fails                                                                      | Add `tests/features/<name>/test_*.py` for the feature                                                                                                                                                                                                                                                                                                                              |
| `test_core_files_have_layer_rules` fails                                                            | A new `core/` file needs a `[[modules]]` entry in `tach.toml` (e.g. `src.app.core.database`, `depends_on = []`) and a line in `src.app.app_module`'s `depends_on` if the root module uses it                                                                                                                                                                                       |
| `test_nothing_gets_around_structure_checks` fails                                                   | Remove the `# tach-ignore`, `# noqa: TID…`, `reportImportCycles` ignore, `__import__(` or `import_module(` and fix the import instead                                                                                                                                                                                                                                              |
| tach output says `run 'tach sync' to update your module configuration`                              | Never run it — it rewrites `tach.toml` / `tach.domain.toml` to allow the imports that broke the rules. Fix the import instead                                                                                                                                                                                                                                                      |
| `tach`: `… is not part of the public interface for '…services'`                                     | Only service classes leave `services/` — import `ItemService`, never a repository or a whole module through `services/`                                                                                                                                                                                                                                                            |
| `tach check-external`: `Module '…services' cannot depend on external package 'fastapi'`             | HTTP stays in routers: the service raises a domain error and the router (or the app's exception handler) maps it to a status code                                                                                                                                                                                                                                                  |
| `MFL000` / `C0302` / `max-lines*` error                                                             | Split the function or file. Never raise `max` or add a disable comment                                                                                                                                                                                                                                                                                                             |
| BasedPyright `reportUnannotatedClassAttribute`                                                      | Annotate the attribute (`self._x: T = x`, `model_config: ClassVar[ConfigDict] = …`)                                                                                                                                                                                                                                                                                                |
| BasedPyright: `asynccontextmanager` is deprecated                                                   | Annotate the lifespan `-> AsyncGenerator[None]`, not `AsyncIterator[None]`                                                                                                                                                                                                                                                                                                         |
| BasedPyright `reportUnknownVariableType` on `from dishka import provide`                            | dishka types `provide` with `Any` — keep the `# pyright: ignore[reportUnknownVariableType]` on that import                                                                                                                                                                                                                                                                         |
| pytest fails on a third-party `DeprecationWarning` after an upgrade                                 | `filterwarnings = ["error"]` turns every warning into a failure. Fix it in our code if the warning is ours; if it comes from a dependency, add a narrow entry (`"ignore:<message>:DeprecationWarning:<module>"`) and note why — never remove `"error"`                                                                                                                             |
| `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`                  | `uv add --dev httpx2`                                                                                                                                                                                                                                                                                                                                                              |
| `uv python install` can't find the newest Python                                                    | Upgrade uv (`brew upgrade uv`) — its download list is built in                                                                                                                                                                                                                                                                                                                     |
| Ruff flags differ between editor and CLI                                                            | Remove `ruff.lint.select` / `ruff.lineLength` / `ruff.configuration` from user settings                                                                                                                                                                                                                                                                                            |
| `pnpm run lint` hangs for minutes                                                                   | oxlint is linting `node_modules` — missing `.gitignore` / `ignorePatterns`                                                                                                                                                                                                                                                                                                         |
| Editor shows only a few oxc **warnings** while `pnpm run lint` shows errors                         | `frontend/.oxlintrc.json` contains `options.typeAware` — not allowed in nested configs; remove it, then **Oxc: Restart Server**                                                                                                                                                                                                                                                    |
| Editor misses `no-floating-promises` / `no-unsafe-*`                                                | Set `"oxc.path.tsgolint": "frontend/node_modules/.bin/tsgolint"`, then Reload Window                                                                                                                                                                                                                                                                                               |
| Ruff or oxlint seem to use defaults / type-aware rules missing although settings look right         | The folder is in **Restricted Mode** — VS Code ignores `ruff.interpreter` and `oxc.path.tsgolint` there. Trust the folder (status bar or **Workspaces: Manage Workspace Trust**)                                                                                                                                                                                                   |
| Pylint only updates on save                                                                         | `pylint.lintOnChange` is machine-scoped — it must be in the user `settings.json`, not `.vscode/settings.json`                                                                                                                                                                                                                                                                      |
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
- [ ] **2b.** [Keeping versions current](#keeping-versions-current): upgrade to the newest compatible versions, record any hold
- [ ] **3.** Install the VS Code extensions, uninstall Pylance → Reload Window → **Select Interpreter** → `backend/.venv`
- [ ] **4.** User settings: `files.autoSave: "onFocusChange"`, `pylint.lintOnChange: true`; trust the folder
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
│   ├── src/app/                ← main.py, app_module.py, core/, common/, features/<name>/
│   └── tests/                  ← test_structure.py + features/ mirror
└── frontend/                   ← Next.js (App Router, src/, Tailwind, Turbopack)
    ├── CLAUDE.md, AGENTS.md    ← frontend rules + Next's agent rules
    ├── .oxlintrc.json, .prettierrc, tsconfig.json, vitest.config.mts, .nvmrc
    └── src/app/                ← layout, page (+ test), globals.css
```

---

## Agent completion criteria

Before marking tooling setup done, confirm:

1. Backend: `ruff check`, `ruff format --check`, `basedpyright`, `flake8`, `pylint`, `tach check`, `tach check-external`, `pytest`, `pip-audit` all pass; the server boots and `POST /items` works
2. Frontend: `lint`, `typecheck`, `format:check`, `test`, `build`, `audit` all pass
3. Editor smoke test (Steps 0–4 above): every row of the backend and frontend tables appears in Problems — as errors where listed — including the never-opened `smoke_closed.py`, the tach error on `routers/items.py`, and all eight `(task)` sources in the user's screenshot; fix/format on save confirmed on disk; the pre-commit hook refused the smoke commit; all smoke files removed and `getDiagnostics` clean
4. Size limits are errors in both: `max-function-length = 100` + `max-module-lines = 500` (backend), `max-lines-per-function` 100 + `max-lines` 500 (frontend)
5. `backend/tach.toml` has `root_module = "forbid"` and the routers → services → repositories rules; `tests/test_structure.py` exists
6. No stray config files: no `pyrightconfig.json`, `.flake8`, `.pylintrc`, `[tool.tach]` in `pyproject.toml`, `eslint.config.mjs`, `frontend/.gitignore`
7. Extensions installed as listed; Pylance and ESLint not installed; the interpreter is `backend/.venv`
8. Versions are the newest stable ones that pass every check; any held-back major is recorded in Troubleshooting
