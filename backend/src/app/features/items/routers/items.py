from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from src.app.features.items.schemas.items import ItemCreate, ItemResponse
from src.app.features.items.services.items import ItemService

router = APIRouter(prefix="/items", tags=["items"], route_class=DishkaRoute)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_item(data: ItemCreate, service: FromDishka[ItemService]) -> ItemResponse:
    return await service.create(data)


@router.get("")
async def list_items(service: FromDishka[ItemService]) -> list[ItemResponse]:
    return await service.list_items()
