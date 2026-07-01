# Dev Tooling Setup Guide

Production-ready linting and type-checking for Python (Ruff + BasedPyright) and TypeScript/JavaScript (ESLint + TypeScript). Use this checklist when bootstrapping a new monorepo or single-package project.

**Path:** `backend/docs/setup.md` (this repo). Point agents here for editor + CLI tooling setup.

---

## For AI agents — read this first

When setting up or verifying dev tooling in a similar repo:

1. **Follow the three-layer rule** — rules in config files; paths only in `.vscode/settings.json`; format-on-save in user settings.
2. **Do not create** a root `pyrightconfig.json` if `[tool.basedpyright]` already exists in `pyproject.toml`.
3. **Do not add** `runOn: folderOpen` auto tasks unless the user explicitly wants visible terminal processes on every reload.
4. **Do not use** deprecated or wrong settings: `python.analysis.*`, `cursorpyright.*`, `ruff.lint.run`, `typescript.tsserver.experimental.enableProjectDiagnostics`.
5. **Verify with CLI** before claiming done (commands in [Verify CLI](#4-verify-cli) and [Frontend verify](#4-verify-cli-1)).
6. **Verify editor** with a temporary smoke test (see [Verify editor Problems panel](#verify-editor-problems-panel)), then remove it.

### Workspace diagnostics — yes / no (verified)

| Tool | Silent background LSP for **all** workspace files? | Full project scan (Problems or CLI)? |
|------|---------------------------------------------------|--------------------------------------|
| **BasedPyright** | **YES** — `basedpyright.analysis.diagnosticMode: "workspace"` | **YES** — same via LSP + `uv run basedpyright` |
| **Ruff** | **NO** — extension lints **open/edited files only** ([ruff-vscode #145](https://github.com/astral-sh/ruff-vscode/issues/145)) | **YES** — `uv run ruff check` or manual VS Code task |
| **TypeScript** | **NO** — built-in TS server is open/edited files only; `enableProjectDiagnostics` is abandoned by Microsoft | **YES** — `pnpm run typecheck` or manual `frontend: typecheck` task |
| **ESLint** | **NO** — extension lints **open/edited files only** ([vscode-eslint README](https://github.com/microsoft/vscode-eslint)) | **YES** — `pnpm run lint` or **Tasks → eslint: lint whole folder** (with `eslint.lintTask.enable`) |

**Empty Problems panel = clean code.** That is expected when CLI passes.

---

## Architecture: three layers

| Layer | Location | Purpose | Commit? |
|-------|----------|---------|---------|
| **Rules** | `pyproject.toml`, `eslint.config.mjs` | What to enforce — shared by CLI and editor | Yes |
| **Project wiring** | `.vscode/settings.json` | Where tools find config, venv, subdirs | Yes |
| **Personal prefs** | User `settings.json` | Format-on-save, global extension toggles | No (per machine) |

**Golden rule:** put lint/type **rules** in config files, not in VS Code settings. VS Code settings only wire paths and LSP behavior.

---

## Required extensions

Install once per machine (workspace recommends these via `.vscode/extensions.json`):

| Extension | ID | Role |
|-----------|-----|------|
| BasedPyright | `detachhead.basedpyright` | Python type checking (LSP) |
| Ruff | `charliermarsh.ruff` | Python lint + format (LSP) |
| Python | `ms-python.python` | Interpreter selection |
| ESLint | `dbaeumer.vscode-eslint` | JS/TS lint (LSP) |
| Prettier | `esbenp.prettier-vscode` | JS/TS format (optional but used below) |

After installing: **Cmd+Shift+P → Developer: Reload Window**.

---

## Python backend

### 1. Install dev dependencies

```bash
cd backend
uv add --dev ruff basedpyright pytest pytest-asyncio
uv sync
```

Select interpreter: status bar → `backend/.venv/bin/python`.

### 2. Configure `backend/pyproject.toml`

Copy this block and adjust `pythonVersion`, `target-version`, and paths for your project.

```toml
[dependency-groups]
dev = [
    "pytest>=9.1.1",
    "pytest-asyncio>=1.4.0",
    "ruff>=0.15.18",
    "basedpyright>=1.39.8",
]

# --- Type checking (BasedPyright) ---
[tool.basedpyright]
pythonVersion = "3.14"              # match runtime
typeCheckingMode = "recommended"    # production default (not "standard")
failOnWarnings = true               # CLI fails on warnings too
include = ["src", "tests"]
exclude = [
    "**/node_modules",
    "**/__pycache__",
    "**/.pytest_cache",
    "**/.ruff_cache",
    "**/.venv",
]
extraPaths = ["src"]                # for `from src.app...` imports
reportMissingTypeStubs = "none"
baselineFile = ".basedpyright/baseline.json"

# --- Lint + format (Ruff) ---
[tool.ruff]
target-version = "py314"            # match pythonVersion
line-length = 100
src = ["src", "tests"]
unsafe-fixes = true

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "I",      # isort
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "G",      # flake8-logging-format
    "SIM",    # flake8-simplify
    "TID252", # banned relative imports
    "S",      # security (bandit)
    "ANN",    # flake8-annotations
]
ignore = ["S101"]                   # allow assert in src
unfixable = ["F841"]

# Do NOT enable "COM" — conflicts with ruff formatter (COM812)

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["ANN", "S101", "S105", "S106"]
"src/app/features/**/dependencies.py" = ["B008"]   # FastAPI Depends()
"src/app/repositories/**/*.py" = ["ANN401"]        # **kwargs: Any in repos

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

### 3. Baseline (existing codebases only)

When upgrading to `recommended` on code that already has type warnings:

```bash
cd backend
uv run basedpyright src tests                    # see all warnings
uv run basedpyright --writebaseline src tests    # snapshot existing warnings
```

Commit `backend/.basedpyright/baseline.json`. If `.gitignore` ignores `.basedpyright/`, add:

```gitignore
backend/.basedpyright/
!backend/.basedpyright/baseline.json
```

After baseline:

- **Existing** warnings → ignored by CLI
- **New** warnings/errors → fail `basedpyright`
- After fixing old issues → re-run `--writebaseline` to shrink the file

Greenfield projects can skip the baseline until warnings appear.

### 4. Verify CLI

```bash
cd backend
uv run ruff check src tests
uv run ruff format --check src tests
uv run basedpyright src tests
```

All three must pass before merging.

---

## Frontend (Next.js + ESLint + TypeScript)

### 1. Install dev dependencies

```bash
cd frontend
pnpm add -D eslint eslint-config-next @eslint/eslintrc typescript
```

### 2. Create `frontend/eslint.config.mjs`

ESLint 9+ flat config. Rules live here — not in VS Code settings.

```js
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

const config = [
  ...nextVitals,
  ...nextTypescript,
  {
    rules: {
      // project-specific overrides only
    },
  },
];

export default config;
```

### 3. Add scripts to `frontend/package.json`

```json
{
  "scripts": {
    "lint": "eslint .",
    "typecheck": "tsc --noEmit"
  }
}
```

**Note:** ESLint = lint rules. `tsc --noEmit` = full project type checking. Separate tools.

### 4. Verify CLI

```bash
cd frontend
pnpm run lint
pnpm run typecheck
```

---

## Workspace settings (commit `.vscode/`)

### `.vscode/extensions.json`

```json
{
  "recommendations": [
    "detachhead.basedpyright",
    "charliermarsh.ruff",
    "ms-python.python",
    "dbaeumer.vscode-eslint"
  ]
}
```

### `.vscode/settings.json` — monorepo (Python in `backend/`, frontend in `frontend/`)

This is the **current production config** for this repo:

```json
{
  "npm.autoDetect": "off",

  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.languageServer": "None",

  "basedpyright.analysis.configFilePath": "${workspaceFolder}/backend",
  "basedpyright.analysis.baselineFile": "${workspaceFolder}/backend/.basedpyright/baseline.json",
  "basedpyright.analysis.diagnosticMode": "workspace",

  "ruff.cwd": "${workspaceFolder}/backend",

  "typescript.tsdk": "frontend/node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,

  "eslint.useFlatConfig": true,
  "eslint.workingDirectories": [
    { "directory": "frontend", "changeProcessCWD": true }
  ]
}
```

Optional — enables **Tasks → eslint: lint whole folder** (manual full-project ESLint, not background LSP):

```json
"eslint.lintTask.enable": true
```

### `.vscode/settings.json` — single Python package at repo root

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.languageServer": "None",
  "basedpyright.analysis.diagnosticMode": "workspace",
  "ruff.cwd": "${workspaceFolder}"
}
```

### What NOT to put in workspace settings

| Setting | Why not |
|---------|---------|
| `basedpyright.analysis.typeCheckingMode` | Duplicates `pyproject.toml` — causes CLI/LSP drift |
| `python.analysis.*` | Pylance only — **ignored by BasedPyright** |
| `cursorpyright.*` | Cursor built-in checker — **not BasedPyright** |
| `ruff.lint.run` | Deprecated ruff-lsp setting — use Ruff native extension only |
| `typescript.tsserver.experimental.enableProjectDiagnostics` | Unreliable — Microsoft will not fix it |
| ESLint rule overrides | Belong in `eslint.config.mjs` |
| `runOn: folderOpen` tasks | Spawns visible terminal processes on every reload — avoid unless user asks |

### `.vscode/tasks.json` — manual only

Tasks are for **Run Task** from the command palette or pre-merge checks. **Do not** set `"runOn": "folderOpen"` unless the user explicitly wants auto-starting terminal processes.

Current manual tasks in this repo:

| Task label | Command | Problem matcher |
|------------|---------|-----------------|
| `backend: dev` | `uv run uvicorn src.app.main:app --reload ...` | — |
| `backend: ruff check` | `uv run ruff check src tests` | `$ruff` |
| `backend: ruff format` | `uv run ruff format --check src tests` | — |
| `backend: basedpyright` | `uv run basedpyright src tests` | — |
| `frontend: dev` | `pnpm run dev` | — |
| `frontend: lint` | `pnpm run lint` | `$eslint-stylish` |
| `frontend: typecheck` | `pnpm run typecheck` | `$tsc` |

---

## User settings (once per machine)

Path on macOS (Cursor/VS Code):

```
~/Library/Application Support/Cursor/User/settings.json
```

### Minimal tooling template

```json
{
  "files.autoSave": "onFocusChange",

  "python.languageServer": "None",
  "python.createEnvironment.trigger": "off",
  "python.testing.pytestEnabled": true,

  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll": "always",
      "source.organizeImports": "always"
    }
  },
  "ruff.enable": true,
  "ruff.lint.enable": true,
  "ruff.fixAll": true,
  "ruff.organizeImports": true,

  "[javascript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.codeActionsOnSave": {
      "source.fixAll.eslint": "always",
      "source.organizeImports": "always"
    }
  },
  "[javascriptreact]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.codeActionsOnSave": {
      "source.fixAll.eslint": "always",
      "source.organizeImports": "always"
    }
  },
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.codeActionsOnSave": {
      "source.fixAll.eslint": "always",
      "source.organizeImports": "always"
    }
  },
  "[typescriptreact]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.codeActionsOnSave": {
      "source.fixAll.eslint": "always",
      "source.organizeImports": "always"
    }
  },
  "eslint.enable": true,
  "eslint.validate": ["javascript", "javascriptreact", "typescript", "typescriptreact"],
  "eslint.workingDirectories": [{ "mode": "auto" }]
}
```

### Do NOT set in user settings

| Setting | Why |
|---------|-----|
| `python.defaultInterpreterPath` | Per-project — use workspace `.vscode/settings.json` |
| `basedpyright.analysis.configFilePath` | Per-project — use workspace settings |
| `python.analysis.diagnosticMode` | Pylance only — use `basedpyright.analysis.diagnosticMode` in workspace |
| `cursorpyright.*` | Wrong tool if using BasedPyright extension |

---

## What runs automatically vs manually

### Runs in the editor (background LSP — no terminal tasks)

| When | Tool | Scope | What happens |
|------|------|-------|--------------|
| While typing | **BasedPyright** | **Whole workspace** (`src/`, `tests/`) | Type errors → Problems panel |
| While typing | **Ruff** | **Open/edited files only** | Lint squiggles + Problems |
| While typing | **ESLint** | **Open/edited files only** | Lint squiggles + Problems |
| While typing | **TypeScript** | **Open/edited files only** | Type errors → Problems (`ts` source) |
| On save / focus change | **Ruff** | Current file | Format + auto-fix + organize imports |
| On save / focus change | **ESLint + Prettier** | Current file | Auto-fix + format JS/TS |

With `"files.autoSave": "onFocusChange"`, save actions fire when you **leave a file**, not only on Cmd+S.

### Manual / pre-merge (full project — all files)

```bash
# Backend — scans all Python files
uv run ruff check src tests
uv run ruff format --check src tests
uv run basedpyright src tests

# Frontend — scans all TS/JS files
pnpm run lint
pnpm run typecheck
```

Or run matching tasks from **Tasks: Run Task** in VS Code.

For ESLint whole-folder via extension: set `eslint.lintTask.enable: true`, then **Tasks → eslint: lint whole folder**.

---

## Verify editor Problems panel

Use temporary smoke tests, then **delete them** after confirming diagnostics appear.

### Python (BasedPyright — should show even if file not open)

Add to any file under `backend/src/` (e.g. `main.py`):

```python
# --- SMOKE TEST: delete after verifying ---
def _pyright_smoke_test() -> int:
    value: int = "not-an-int"
    return value
```

Expect **2 errors** in Problems (`reportAssignmentType`). Source: **basedpyright**.

### TypeScript (open file only unless you run `pnpm run typecheck`)

Add to any `.ts` file under `frontend/src/`:

```typescript
// --- SMOKE TEST: delete after verifying ---
const _smokeNumber: number = "not-a-number";
```

Expect **1 error** in Problems when file is open. Source: **ts**.

### ESLint (open file only)

Unused variable in the same `.ts` file often triggers `@typescript-eslint/no-unused-vars`. Source: **eslint**.

---

## New project checklist

Copy in this order:

- [ ] **1.** Create `backend/pyproject.toml` with `[tool.basedpyright]` + `[tool.ruff]`
- [ ] **2.** `uv sync` — select `backend/.venv` interpreter
- [ ] **3.** Create `frontend/eslint.config.mjs` + `lint` / `typecheck` scripts
- [ ] **4.** Add `.vscode/settings.json` (monorepo paths)
- [ ] **5.** Add `.vscode/extensions.json`
- [ ] **6.** Add `.vscode/tasks.json` (manual tasks only — no `runOn: folderOpen`)
- [ ] **7.** Confirm user `settings.json` tooling block (once per machine)
- [ ] **8.** Install extensions → Reload Window
- [ ] **9.** Run CLI verify commands — all green
- [ ] **10.** Run editor smoke tests — confirm Problems panel → remove smoke tests
- [ ] **11.** (Existing codebase) Generate BasedPyright baseline → commit `baseline.json`
- [ ] **12.** Commit all config files — never rely on personal settings alone

---

## Logging (Loguru — env-aware)

### `core/logger.py`

Configure once. Dev gets verbose colored output, prod gets JSON for log aggregators.

```python
import sys

from loguru import logger

from src.app.core.config import get_settings

def setup_logger() -> None:
    settings = get_settings()
    logger.remove()

    if settings.log_format == "json":
        logger.add(sys.stderr, level=settings.log_level, serialize=True)
    else:
        logger.add(
            sys.stderr,
            level=settings.log_level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level:<8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
        )
```

### Add to `core/config.py`

```python
log_level: str = Field(
    default="DEBUG",
    description="Logging level. Dev: DEBUG. Prod: WARNING.",
)
log_format: str = Field(
    default="pretty",
    description="Log output format. 'pretty' for dev (colored), 'json' for prod (structured).",
)
```

### `.env` per environment

```bash
# Dev (default — verbose, colored)
LOG_LEVEL=DEBUG
LOG_FORMAT=pretty

# Prod (errors + warnings only, JSON for aggregators)
LOG_LEVEL=WARNING
LOG_FORMAT=json
```

### Call `setup_logger()` in `main.py`

```python
from src.app.core.logger import setup_logger
setup_logger()  # call before create_app()
```

### What each level captures

| Level | Dev | Prod | Examples |
|-------|-----|------|----------|
| DEBUG | ✅ | ❌ | Internal state, variable values |
| INFO | ✅ | ❌ | External API calls, DB writes, run start/end |
| WARNING | ✅ | ✅ | Deprecations, fallback paths taken |
| ERROR | ✅ | ✅ | Exceptions, failed external calls |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Problems empty, CLI finds Python errors | Install BasedPyright extension; `python.languageServer: "None"`; `configFilePath` for monorepos; reload window |
| `failed to parse baseline file` (monorepo) | Set `basedpyright.analysis.baselineFile` to `${workspaceFolder}/backend/.basedpyright/baseline.json` — default path is workspace root |
| BasedPyright not running | Output panel → **BasedPyright**; check extension enabled |
| Wrong Python venv | Status bar → select `backend/.venv/bin/python` |
| Ruff can't find config | Set `ruff.cwd` to Python root in workspace settings |
| ESLint can't find config | Set `eslint.workingDirectories` to `frontend/` |
| `python.analysis.*` does nothing | Pylance setting — use `basedpyright.*` instead |
| Deprecated ruff-lsp warning | Remove `ruff.lint.run` from settings |
| Ruff lint missing in closed files | **Expected** — run `uv run ruff check` for full scan |
| TS errors missing in closed files | **Expected** — run `pnpm run typecheck` for full scan |
| Three terminal tasks on reload | Remove `"runOn": "folderOpen"` from tasks.json |
| Formatter + lint conflict | Remove `COM` from Ruff select |

---

## Reference: this repo's layout

```
Market Agent/
├── backend/
│   ├── docs/setup.md             ← this file
│   ├── pyproject.toml            ← Python rules (single source of truth)
│   ├── .basedpyright/baseline.json
│   └── .venv/
├── frontend/
│   ├── eslint.config.mjs         ← ESLint rules
│   ├── package.json
│   └── tsconfig.json             ← TypeScript (separate from ESLint)
└── .vscode/
    ├── settings.json             ← monorepo wiring only
    ├── extensions.json
    └── tasks.json                ← manual CLI tasks only
```

---

## Agent completion criteria

Before marking tooling setup done, confirm:

1. `uv run ruff check`, `uv run ruff format --check`, `uv run basedpyright` pass in `backend/`
2. `pnpm run lint` and `pnpm run typecheck` pass in `frontend/`
3. BasedPyright smoke test appears in Problems (then removed)
4. No duplicate config files (`pyrightconfig.json` at root if `pyproject.toml` exists)
5. No deprecated settings (`ruff.lint.run`, `enableProjectDiagnostics`, `cursorpyright.*`)
6. No auto `runOn: folderOpen` tasks unless user requested them
