# Backend Coding Rules

## Dev tooling setup

For linting, type-checking, and editor configuration (BasedPyright, Ruff, ESLint, VS Code settings), follow **`docs/setup.md`**. Do not duplicate rules in `.vscode/settings.json` or create a root `pyrightconfig.json`.

## Stack
B2B platform · Google Cloud Run/GKE · FastAPI · SQLAlchemy (async) · Redis Cloud · `uv` (package manager) · `dishka` (DI)

---

## Backend Rules
1. **REPOSITORY PATTERN** — ALL DB/Redis ops through repositories
2. **ABSOLUTE IMPORTS** — `from src.app.X import Y` in `.py`; relative imports only in `__init__.py`
3. **DUAL PYDANTIC** — always set both `response_model=` and return type annotation
4. **LOG CRITICAL OPS** — external calls, exceptions, state changes; use `{}` placeholders, never f-strings
5. **FIELD DESCRIPTIONS** — all Pydantic `Field()` must include `description=` for readability and OpenAPI docs
6. **NO `api/` FOLDER** — register feature routers directly in `main.py`. No versioning layer unless there's an actual v2.

---

## Project Structure (Hybrid)

Two patterns coexist. Choose based on what the code IS, not where it goes.

### When to use which
- **Feature-based** → REST API business domains (auth, users, orders, payments)
- **Layer-based** → shared infrastructure + AI agent systems

### Standard FastAPI REST Project (Feature-Based)

```
src/app/
  features/
    auth/
      router.py        # HTTP layer only
      service.py       # business logic
      repository.py    # DB/Redis access
      schemas.py        # Pydantic DTOs
      dependencies.py  # feature-scoped DI providers
      __init__.py
    users/
      router.py
      service.py
      repository.py
      schemas.py
      __init__.py
  common/
    exceptions.py      # shared exception types
    constants.py       # app-wide constants
  core/
    config.py
    logger.py
    container.py       # dishka container
    database.py        # SQLAlchemy engine/session
  main.py
tests/
  conftest.py
  features/
    auth/
      test_router.py
      test_service.py
```

### AI Agent Project (Hybrid: Layer-Based Infra + Feature-Based REST)

```
src/app/
  # Shared infrastructure — layer-based (used by agents + REST)
  core/                 # config, logger, database
  common/               # exceptions, constants
  models/               # SQLAlchemy ORM models
  repositories/
    db/                 # DB repositories
    redis/              # Redis repositories
  services/
    adzuna/             # external API client
    linkedin/           # external API client
    source_items.py     # collector pipeline DTOs (SourceItemBase + subclasses)

  # Agent system — layer-based (tools/prompts shared across agents)
  agents/
    recruiter_agent/
      agent.py
      tools/            # agent-specific tools (if any)
      prompts.py        # agent-specific prompts
      schemas.py        # agent workflow types (GraphDeps, TriageResult, etc.)
    market_analyst_agent/
      agent.py
      schemas.py        # agent workflow types
  shared/
    tools/              # shared tools (2+ agents use)
    callbacks/          # shared ADK callbacks
    prompts/            # shared prompts (2+ agents use)
    schemas/            # ADK tool input schemas (2+ agents share)
    sub_agents/         # sub-agents used by 2+ agents
    utils/               # shared helpers

  # REST API domains — feature-based
  features/
    auth/
      router.py
      service.py
      schemas.py        # HTTP request/response DTOs only
    jobs/
      router.py
      service.py
      schemas.py        # HTTP request/response DTOs only

  main.py               # registers feature routers directly
```

### Feature Rules (REST domains)
- New REST feature = new folder under `features/` — never add to existing feature
- No cross-feature imports — share only via `common/`
- Router → service → repository, all within same folder
- Shared logic → `common/` only when 2+ features need it
- Routers registered in `main.py`, never auto-discovered
- Router handles HTTP · service handles logic · repository handles data

### Agent Rules
- Each agent folder is isolated — no cross-agent imports
- Shared tool/callback/prompt → `shared/` only when 2+ agents need it
- Agent-specific prompt → lives inside agent folder (`agent_name/prompts.py`)
- ADK handles agent routing — REST feature routers are registered directly in `main.py`

### Schema Rules (4 homes, 4 jobs)
| Location | Boundary | Contains |
|----------|----------|----------|
| `features/*/schemas.py` | HTTP in/out | Request/response DTOs only |
| `agents/*/schemas.py` | Agent workflow | Graph deps, triage results, run results |
| `services/source_items.py` | Collector pipeline | `SourceItemBase` + per-source subclasses |
| `common/` | Cross-layer internal | Dedup markers, shared internal DTOs |
| `shared/schemas/` | ADK tool inputs | Only when 2+ agents share tool input models |

- **No top-level `schemas/` folder** — it becomes a dumping ground
- `models/` = SQLAlchemy ORM only
- Schema location matches the boundary it serves, not "it's Pydantic so schemas/"

### ❌ DON'T
- `from src.app.features.auth.service import X` inside another feature
- Business logic in `router.py`
- DB queries in `service.py`
- Cross-agent imports — never `from src.app.agents.recruiter_agent import X` in another agent
- Put agent-specific prompts in `shared/prompts/` — only truly shared prompts go there
- Put collector DTOs or internal types in a top-level `schemas/` folder

---

## Dependency Injection (dishka)

```python
from dishka import Provider, Scope, provide, make_async_container
from dishka.integrations.fastapi import FromDishka, setup_dishka

class AppProviders(Provider):
    @provide(scope=Scope.APP)
    async def db_engine(self, settings: Settings) -> AsyncEngine:
        engine = create_async_engine(settings.db.url)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    async def redis_client(self, settings: Settings) -> Redis:
        client = Redis.from_url(settings.redis.url)
        yield client
        await client.aclose()

class RequestProviders(Provider):
    @provide(scope=Scope.REQUEST)
    async def db_session(self, engine: AsyncEngine) -> AsyncSession:
        async with AsyncSession(engine) as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def user_repo(self, session: AsyncSession) -> UserRepository:
        return UserRepository(session)

# Route usage
@router.post("")
async def create_user(data: UserCreate, service: FromDishka[UserService]) -> UserResponse:
    return await service.create_user(data)
```

---

## Logging

```python
# ✅ Always import from here
from src.app.core.logger import logger

# ❌ Never
from loguru import logger

# {} placeholders (lazy eval)
logger.info("Processing {}", user_id)           # ✅
logger.info(f"Processing {user_id}")            # ❌

# Related logs → bind()
tool_logger = logger.bind(tool_name="load_metadata")
tool_logger.info("Started")
tool_logger.info("Returned {} items", count)

# Exceptions → always .exception() with bind()
try:
    operation()
except Exception as e:
    logger.bind(tool_name="op", error_type=type(e).__name__).exception("Operation failed")
    raise ServiceException("Failed") from e

# ❌ Never — loses traceback
logger.error("Operation failed")
```

**Log**: external APIs, DB writes, exceptions, state changes, slow ops (>1s)
**Never log**: loops, reads, helpers

---

## Exception Hierarchy

```python
# common/exceptions.py
class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AppError):
    def __init__(self, msg: str): super().__init__(msg, 404)

class ValidationError(AppError):
    def __init__(self, msg: str): super().__init__(msg, 400)

class UnauthorizedError(AppError):
    def __init__(self, msg: str): super().__init__(msg, 401)

class ConflictError(AppError):
    def __init__(self, msg: str): super().__init__(msg, 409)

class ServiceError(AppError):
    def __init__(self, msg: str): super().__init__(msg, 500)
```

- Service layer raises domain exceptions — never `HTTPException`
- Router never catches — global handler in `main.py` maps to HTTP
- Use specific subclass (`NotFoundError`, not `AppError`)
- `HTTPException` only in auth middleware / dependencies

---

## Security (OWASP Top 10)

```python
# Rate limiting
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest): ...

# Input validation
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

# Secrets via settings only
api_key = settings.external_api.key.get_secret_value()   # ✅
API_KEY = "sk-1234"                                       # ❌
```

**NEVER**: hard-code secrets, commit `.env`, log PII, use `allow_origins=["*"]`, build SQL with f-strings
**ALWAYS**: env vars, `SecretStr` in Pydantic, parameterized queries (ORM), rotate keys

---

## Repository Pattern

All repositories inherit from `BaseRepository[T]` which provides common CRUD (`get_by_id`, `get_all`, `create`, `delete`). Domain-specific methods go in the child class only.

```python
# repositories/db/base_repository.py
class BaseRepository[T: DeclarativeBase]:
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None:
        return await self.session.get(self.model, id)

    async def get_all(self, limit: int = 100) -> list[T]:
        result = await self.session.execute(select(self.model).limit(limit))
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: int) -> None:
        obj = await self.get_by_id(id)
        if obj:
            await self.session.delete(obj)
            await self.session.flush()

# repositories/db/user_repository.py — only domain-specific methods
class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email),
        )
        return result.scalar_one_or_none()
```

- Every repository inherits `BaseRepository[ModelType]`
- Never repeat `session.add()` / `flush()` / `refresh()` — use `self.create(**kwargs)`
- IntegrityError handling goes in the child method that needs it, not the base

---

## Alembic Migrations

- Never edit existing migration — always create new one
- Always review autogenerate output before committing
- One migration per PR unless tightly coupled
- Never run `alembic upgrade head` in app startup — separate CI/CD step
- Destructive ops (drop column/table): add `# DANGER` comment, review manually

---

## API Versioning

```
/api/v1/users    ← always use URL prefix for B2B
/api/v2/users    ← only on breaking change
```

```
features/users/
  v1/router.py · v1/schemas.py
  v2/router.py · v2/schemas.py
  service.py    ← shared across versions
  repository.py ← shared across versions
```

- Version only on breaking changes (schema change, removal, required param added)
- Never header-based versioning
- Deprecation: add `X-API-Deprecation` header + sunset date before removing

---

## Testing

```python
# pyproject.toml markers
# unit: isolated, no DB
# integration: hits real DB/Redis

@pytest.mark.unit
def test_parse_email(): ...

@pytest.mark.integration
async def test_create_user_db(): ...
```

- Unit tests: mock external deps, no DB
- Integration tests: real test DB, rollback after each test
- **Never mock DB in integration tests**
- Never hit external APIs in tests (mock them)
- Mirror feature structure in `tests/features/`

---

## Database Patterns

```python
# N+1 prevention
users = await session.execute(
    select(User).options(selectinload(User.orders))
)

# Bulk insert
self.session.add_all([Item(**item) for item in items])
await self.session.flush()

# Transactions — share session, always refresh after commit
async def create_user_with_profile(session: AsyncSession, ...):
    try:
        user = await UserRepository(session).create(email)
        profile = await ProfileRepository(session).create(user.id, data)
        await session.commit()
        await session.refresh(user)
        await session.refresh(profile)
        return user, profile
    except Exception as e:
        await session.rollback()
        logger.bind(error_type=type(e).__name__).exception("Transaction failed")
        raise ServiceError("Failed") from e
```

---

## Locks

```python
# Redis lock (cross-container, distributed)
async with redis_manager.lock(f"user:create:{email}", timeout=10):
    ...  # keep critical section <5s

# asyncio lock (single-container)
class SessionService:
    def __init__(self):
        self._lock = asyncio.Lock()

    async def update_state(self, data: dict):
        async with self._lock:
            self._state.update(data)
```

Never nest locks.

---

## Timezone

UTC everywhere in DB. Convert to user timezone only at display layer.

```python
from datetime import datetime, timezone
utc_now = datetime.now(timezone.utc)

from zoneinfo import ZoneInfo
display = utc_datetime.astimezone(ZoneInfo(user.timezone))
```
