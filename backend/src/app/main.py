from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from src.app.core.container import create_container
from src.app.core.logger import setup_logger
from src.app.features.items.router import router as items_router


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


app = create_app()
