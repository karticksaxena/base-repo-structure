from src.app.features.items.schemas import ItemCreate, ItemResponse


class ItemRepository:
    """In-memory store. Swap for an SQLAlchemy session when the first database lands (SETUP.md)."""

    def __init__(self) -> None:
        self._items: dict[int, ItemResponse] = {}

    async def create(self, data: ItemCreate) -> ItemResponse:
        item = ItemResponse(id=len(self._items) + 1, name=data.name)
        self._items[item.id] = item
        return item

    async def list_all(self) -> list[ItemResponse]:
        return list(self._items.values())
