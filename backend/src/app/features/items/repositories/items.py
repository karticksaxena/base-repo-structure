from uuid import UUID, uuid7

from src.app.features.items.schemas.items import ItemCreate, ItemResponse


class ItemRepository:
    """In-memory store. Swap for an SQLAlchemy session when the first database lands (SETUP.md)."""

    def __init__(self) -> None:
        self._items: dict[UUID, ItemResponse] = {}

    async def create(self, data: ItemCreate) -> ItemResponse:
        item = ItemResponse(id=uuid7(), name=data.name)
        self._items[item.id] = item
        return item

    async def list_page(self, *, limit: int, offset: int) -> list[ItemResponse]:
        return list(self._items.values())[offset : offset + limit]

    async def count(self) -> int:
        return len(self._items)
