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

    async def list_items(self) -> list[ItemResponse]:
        return await self._repository.list_all()
