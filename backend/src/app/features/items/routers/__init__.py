"""The feature's HTTP routers (Nest controllers), combined into one `router` for main.py."""

from fastapi import APIRouter

from src.app.features.items.routers.items import router as items_router

router = APIRouter()
router.include_router(items_router)
