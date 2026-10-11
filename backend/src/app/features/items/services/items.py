from src.app.common.schemas import Page
from src.app.core.logger import logger
from src.app.features.items.repositories.items import ItemRepository
from src.app.features.items.schemas.items import ItemCreate, ItemResponse


class ItemService:
    def __init__(self, repository: ItemRepository) -> None:
        self._repository: ItemRepository = repository

    async def create(self, data: ItemCreate) -> ItemResponse:
        item = await self._repository.create(data)
        logger.info("Created item {}", item.id)
        return item

    async def list_items(self, *, limit: int, offset: int) -> Page[ItemResponse]:
        items = await self._repository.list_page(limit=limit, offset=offset)
        total = await self._repository.count()
        return Page[ItemResponse](items=items, total=total, limit=limit, offset=offset)
