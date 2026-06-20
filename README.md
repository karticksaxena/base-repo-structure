# Base Repository Structure

A **production-grade FastAPI boilerplate** designed as a foundational template for building scalable AI agent systems. This repository provides a robust directory structure and architectural pattern combining **FastAPI**, **Google ADK (Agent Development Kit)**, and **dishka** for dependency injection.

**Use this repository as a starting point (template) for new projects.**

---

## 🚀 Key Features

- **Architecture:** Modular Monolith / Layered Architecture (API -> Services -> Repositories).
- **AI Integration:** Native support for Google ADK Multi-Agent systems and **MCP (Model Context Protocol)**.
- **Package Manager:** [uv](https://github.com/astral-sh/uv) for ultra-fast, deterministic dependency management.
- **Dependency Injection:** [dishka](https://github.com/reagento/dishka) for clean, type-safe wiring.
- **Validation:** Pydantic v2 for robust data validation and settings management.
- **Logging:** Loguru for structured, easy-to-use logging.

---

## 📋 Table of Contents

1. [Project Structure](#-project-structure)
2. [Quick Start](#-quick-start)
3. [Architecture Overview](#-architecture-overview)
4. [Dependency Management (UV)](#-dependency-management-with-uv)
5. [Development Workflow](#-development-workflow)

---

## 📁 Project Structure

This is a **production-grade monorepo** designed for building and deploying **multiple AI agents** with shared code. The structure separates concerns effectively while enabling code reuse, independent deployments, and scalability to 10+ agents.

```text
base-repo-structure/
│
├── backend/                                # ⭐ FastAPI + Google ADK backend
│   ├── src/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                     # FastAPI Entry Point
│   │   │   │
│   │   │   ├── agents/                     # ⭐ MULTIPLE AGENTS (Each agent isolated)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_agent.py           # Optional: Base class for all agents
│   │   │   │   ├── recruiter_agent/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── agent.py            # Defines root_agent (entry point for deployment)
│   │   │   │   │   ├── prompts.py          # Agent-specific prompts
│   │   │   │   │   ├── callbacks/          # Agent-specific callbacks (if needed)
│   │   │   │   │   ├── schemas/            # Agent-specific tool input schemas (if needed)
│   │   │   │   │   ├── tools/              # Agent-specific tools (if needed)
│   │   │   │   │   └── README.md
│   │   │   │   ├── career_advisor_agent/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── agent.py
│   │   │   │   │   ├── prompts.py
│   │   │   │   │   └── README.md
│   │   │   │   └── ... (more agents, same pattern)
│   │   │   │
│   │   │   ├── features/                   # ⭐ REST API Domains (Feature-Based)
│   │   │   │   ├── __init__.py
│   │   │   │   └── feature1/               # [Example] Replace with real domain (auth, users, etc.)
│   │   │   │       ├── __init__.py
│   │   │   │       ├── router.py           # HTTP layer only
│   │   │   │       ├── service.py          # Business logic
│   │   │   │       ├── repository.py       # DB/Redis access
│   │   │   │       ├── schemas.py          # Pydantic DTOs (request/response)
│   │   │   │       └── dependencies.py     # Feature-scoped DI providers
│   │   │   │
│   │   │   ├── api/                        # Route registration & versioning
│   │   │   │   ├── __init__.py
│   │   │   │   └── v1/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── dependencies.py     # Route-level dependencies
│   │   │   │       └── routes/
│   │   │   │           ├── __init__.py
│   │   │   │           └── items.py        # [Example] Resource endpoints
│   │   │   │
│   │   │   ├── common/                     # App-wide utilities
│   │   │   │   ├── __init__.py
│   │   │   │   ├── constants.py            # App-wide constants
│   │   │   │   └── exceptions.py           # Base exception hierarchy
│   │   │   │
│   │   │   ├── containers/                 # dishka DI Containers
│   │   │   │   ├── __init__.py
│   │   │   │   └── app_container.py        # Main DI container
│   │   │   │
│   │   │   ├── core/                       # Infrastructure & Config
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py               # Settings (Env vars, secrets)
│   │   │   │   ├── database.py             # DB Connection setup
│   │   │   │   └── logger.py               # Logging setup
│   │   │   │
│   │   │   ├── metadata/                   # Project Metadata/Plans
│   │   │   │   ├── __init__.py
│   │   │   │   └── plans/
│   │   │   │
│   │   │   ├── middleware/                 # FastAPI Middleware
│   │   │   │   ├── __init__.py
│   │   │   │   └── logging_middleware.py
│   │   │   │
│   │   │   ├── models/                     # SQLAlchemy ORM (DB tables)
│   │   │   │   ├── __init__.py
│   │   │   │   └── item.py                 # [Example]
│   │   │   │
│   │   │   ├── repositories/               # ALL DB/Redis access
│   │   │   │   ├── __init__.py
│   │   │   │   ├── db/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── item_repository.py  # [Example]
│   │   │   │   └── redis/
│   │   │   │       ├── __init__.py
│   │   │   │       └── cache_repository.py
│   │   │   │
│   │   │   ├── schemas/                    # HTTP API Pydantic schemas (request/response)
│   │   │   │   ├── __init__.py
│   │   │   │   └── common.py
│   │   │   │
│   │   │   ├── services/                   # External API clients (shared across agents + features)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── service1/               # [Example] Replace with real service (adzuna, linkedin, etc.)
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── service.py
│   │   │   │   │   └── exceptions.py
│   │   │   │   └── service2/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── service.py
│   │   │   │       └── exceptions.py
│   │   │   │
│   │   │   └── shared/                     # ⭐ SHARED AGENT LAYER (2+ agents only)
│   │   │       ├── __init__.py
│   │   │       ├── callbacks/              # Shared ADK callbacks
│   │   │       │   ├── __init__.py
│   │   │       │   ├── caching_callback.py
│   │   │       │   ├── guardrails_callback.py
│   │   │       │   └── logging_callback.py
│   │   │       ├── prompts/                # Shared prompts (2+ agents)
│   │   │       │   └── __init__.py
│   │   │       ├── schemas/                # ADK tool input Pydantic models
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service1_inputs.py  # [Example]
│   │   │       │   └── service2_inputs.py
│   │   │       ├── sub_agents/             # Sub-agents used by 2+ agents
│   │   │       │   ├── __init__.py
│   │   │       │   ├── analyzer_agent.py
│   │   │       │   └── research_agent.py
│   │   │       ├── tools/                  # Shared tools (2+ agents)
│   │   │       │   ├── __init__.py
│   │   │       │   ├── service1/           # [Example] One file per tool, <100 lines
│   │   │       │   │   └── __init__.py
│   │   │       │   ├── service2/
│   │   │       │   │   └── __init__.py
│   │   │       │   └── mcp_servers/
│   │   │       │       └── __init__.py
│   │   │       └── utils/
│   │   │           ├── __init__.py
│   │   │           ├── formatters.py
│   │   │           └── state_helpers.py
│   │   │
│   │   └── __init__.py
│   │
│   ├── tests/
│   │   ├── agents/
│   │   ├── features/
│   │   │   └── feature1/
│   │   ├── services/
│   │   └── shared/
│   │       ├── callbacks/
│   │       ├── schemas/
│   │       └── tools/
│   │
│   ├── deploy/                             # Deployment Scripts
│   │   ├── agent_engine/
│   │   │   ├── deploy_all.sh
│   │   │   └── ... (one per agent)
│   │   ├── cloud_run/
│   │   │   ├── deploy_all.sh
│   │   │   └── ... (one per agent)
│   │   └── common/
│   │       ├── env_template.sh
│   │       └── gcp_setup.sh
│   │
│   ├── docker/                             # Docker Configuration
│   │   ├── Dockerfile.base                 # Base image with shared deps
│   │   └── ... (one per agent)
│   │   ├── DEPLOYMENT.md
│   │   └── SHARED_LAYER_GUIDE.md
│   │
│   ├── .python-version                     # 3.14
│   ├── .env.example                        # Template for environment variables
│   ├── docker-compose.yml                  # Local dev with all agents
│   ├── pyproject.toml                      # Project config & dependencies (dishka, google-adk, fastapi)
│   └── uv.lock
│
├── frontend/                               # Frontend (empty — add your framework here)
│
└── README.md
```

---

## 🔑 Key Structural Points

- **`src/app/agents/`**: Each agent is completely isolated. NO cross-agent imports.
- **`src/app/features/`**: REST API business domains (auth, users, etc.) — feature-based layout. Each feature owns its router, service, repository, and schemas.
- **`src/app/shared/`**: Reusable code (tools, callbacks, schemas, prompts) used by 2+ agents.
- **`src/app/services/`**: External API clients — reusable across agents AND features.
- **`src/app/schemas/`**: HTTP API-level Pydantic schemas (request/response). `shared/schemas/` = ADK tool input schemas. `models/` = SQLAlchemy ORM.
- **`docker/`** and **`deploy/`**: Each agent has its own Dockerfile and deployment script.
- **`tests/`**: Tests organized per module (shared, agents, services, features).
- **`docs/`**: Architecture documentation, guides, and agent creation templates.

---

## 📈 Example: Scaling to 10+ Agents

Below is how the full structure looks when scaled to **10+ agents**. This demonstrates the pattern: one monorepo, multiple agents, all organized alphabetically as they appear in the actual codebase.

```text
base-repo-structure/
│
├── backend/
│   ├── src/app/
│   │   ├── agents/                         # ⭐ 10+ AGENTS
│   │   │   ├── career_advisor_agent/
│   │   │   │   ├── agent.py
│   │   │   │   ├── prompts.py              # agent-specific prompts
│   │   │   │   └── README.md
│   │   │   ├── compliance_agent/
│   │   │   ├── executive_recruiter_agent/
│   │   │   ├── hr_specialist_agent/
│   │   │   ├── market_analyst_agent/
│   │   │   ├── recruiter_agent/
│   │   │   ├── sourcing_manager_agent/
│   │   │   ├── talent_scout_agent/
│   │   │   ├── technical_recruiter_agent/
│   │   │   ├── training_specialist_agent/
│   │   │   └── ... (same pattern)
│   │   │
│   │   ├── features/                       # ⭐ REST API domains
│   │   │   └── feature1/
│   │   │       ├── router.py
│   │   │       ├── service.py
│   │   │       ├── repository.py
│   │   │       ├── schemas.py
│   │   │       └── dependencies.py
│   │   │
│   │   ├── shared/                         # ⭐ Shared agent layer (2+ agents only)
│   │   │   ├── callbacks/
│   │   │   ├── prompts/                    # Only truly shared prompts
│   │   │   ├── schemas/                    # ADK tool input models
│   │   │   ├── sub_agents/
│   │   │   ├── tools/
│   │   │   │   ├── service1/               # One file per tool, <100 lines
│   │   │   │   ├── service2/
│   │   │   │   └── mcp_servers/
│   │   │   └── utils/
│   │   │
│   │   ├── services/                       # External API clients
│   │   │   ├── service1/
│   │   │   └── service2/
│   │   │
│   │   ├── api/v1/routes/
│   │   ├── common/
│   │   ├── containers/                     # dishka DI
│   │   ├── core/
│   │   ├── metadata/plans/
│   │   ├── middleware/
│   │   ├── models/                         # SQLAlchemy ORM
│   │   ├── repositories/db/ + redis/
│   │   └── schemas/                        # HTTP API Pydantic schemas
│   │
│   ├── tests/
│   │   ├── agents/
│   │   │   ├── career_advisor_agent/
│   │   │   └── ... (one per agent)
│   │   ├── features/
│   │   ├── services/
│   │   └── shared/
│   │
│   ├── deploy/
│   │   ├── agent_engine/                   # One script per agent
│   │   ├── cloud_run/                      # One script per agent
│   │   └── common/
│   │
│   ├── docker/
│   │   ├── Dockerfile.base
│   │   └── Dockerfile.<agent_name> ...     # One per agent
│   │
│   ├── docs/
│   ├── .python-version                     # 3.14
│   ├── .env.example
│   ├── docker-compose.yml
│   ├── pyproject.toml
│   └── uv.lock
│
├── frontend/                               # Frontend (empty — add your framework here)
│
└── README.md
```

### Key Points for Scaling:

- **Monorepo split** — `backend/` has all Python/FastAPI/ADK code. `frontend/` is separate and independent.
- **Agents are minimal** — `agent.py` (~80 lines) + `prompts.py` + optional agent-specific tools/schemas/callbacks
- **Agent prompts live in the agent folder** — `agents/<name>/prompts.py`. Only prompts used by 2+ agents go in `shared/prompts/`
- **Shared = 2+ consumers** — nothing goes in `shared/` unless 2+ agents use it
- **Hybrid structure** — REST domains in `features/` (feature-based), agent infra in `shared/` + `services/` (layer-based)
- **Tools are modularized** — one file per tool, ~50-100 lines each
- **Docker & Deploy** — one Dockerfile per agent, one deploy script per agent, independently deployable

---

## ⚡ Quick Start

### Prerequisites
- **Python 3.14+**
- **uv** (Package Manager)

### Installation

1. **Clone the Template**
   ```bash
   git clone <your-repo-url> my-new-project
   cd my-new-project/backend
   ```

2. **Install Dependencies**
   ```bash
   uv sync
   ```

3. **Run the Server**
   ```bash
   uv run uvicorn src.app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

---

## 🏗️ Architecture Overview

This template enforces a strict separation of concerns to maintain code quality as the project grows.

### Hybrid Architecture: Layer-Based + Feature-Based

This template uses a **hybrid structure** — two patterns coexist based on what the code is:

| Pattern | Where | Why |
|---|---|---|
| Layer-based | `agents/`, `services/`, `repositories/`, `shared/` | Shared infra used across many consumers |
| Feature-based | `features/` | REST API domains isolated per business capability |

### 1. Features Layer (`src/app/features/`)
- **Responsibility:** Each REST API domain owns its router, service, repository, and schemas.
- **Rule:** No cross-feature imports. Share only via `common/`. Router → service → repository within one folder.

### 2. API Layer (`src/app/api/`)
- **Responsibility:** Register feature routers, handle versioning and route-level dependencies.
- **Rule:** No business logic here — just wiring.

### 3. Services Layer (`src/app/services/`)
- **Responsibility:** External API clients (third-party integrations). Reusable across agents AND features.
- **Rule:** Services never access DB directly — that's repositories.

### 4. Repository Layer (`src/app/repositories/`)
- **Responsibility:** Abstract all data access (SQL, Redis).
- **Rule:** ALL DB/Redis ops go through repositories. Never query DB from service or agent directly.

### 5. Agents Layer (`src/app/agents/`)
- **Responsibility:** Encapsulate AI logic using Google ADK. Each agent is independently deployable.
- **Rule:** No cross-agent imports. ADK handles agent routing via `get_fast_api_app()`.
- **Structure:** Top-level agents → use tools from `shared/tools/` → call services → call repositories.

### 6. Dependency Injection (`src/app/containers/`)
- Uses **dishka** for clean, type-safe DI wiring.
- `FromDishka[ServiceType]` in route handlers — no manual instantiation.

### Three Schema Types — Never Confuse
| Location | Type | Purpose |
|---|---|---|
| `models/` | SQLAlchemy | Database table definitions |
| `schemas/` | Pydantic | HTTP API request/response contracts |
| `shared/schemas/` | Pydantic | ADK tool function input models |

*Data flows: Schema (input) → Feature Service → Repository → Model (DB) → Repository → Schema (output)*

---

## 📦 Dependency Management with UV

This project uses `uv` for superior speed and reliability.

### Common Commands

- **Sync Environment (Install):**
  ```bash
  uv sync
  ```
  *Creates `.venv` and installs packages from `uv.lock`.*

- **Add a Package:**
  ```bash
  uv add sqlalchemy
  uv add --dev pytest
  ```

- **Run Commands:**
  ```bash
  uv run pytest
  uv run python scripts/setup_db.py
  ```

- **Update Dependencies:**
  ```bash
  uv sync --upgrade
  ```

### `pyproject.toml`
Defines the project metadata and direct dependencies.

```toml
[project]
name = "my-new-project"
version = "0.1.0"
description = "My awesome AI project"
requires-python = ">=3.14"
dependencies = [
    "fastapi",
    "google-adk",
    "dishka",
    # ...
]
```

---

## 🛠️ Development Workflow

1.  **Start coding:**
    Create a new Feature Branch.
    ```bash
    git checkout -b feature/new-agent-capability
    ```

2.  **Develop:**
    - Add a Schema in `schemas/`.
    - Add a Model in `models/`.
    - Create a Repository in `repositories/`.
    - Implement Business Logic in `services/`.
    - Expose via Endpoint in `api/`.

3.  **Test:**
    ```bash
    uv run pytest
    ```

4.  **Lint & Format:**
    This repo assumes standard tools (Ruff/Black) are configured.
    ```bash
    uv run ruff check .
    ```

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).