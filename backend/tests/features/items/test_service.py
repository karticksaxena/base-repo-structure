import pytest

from src.app.features.items.repositories.items import ItemRepository
from src.app.features.items.schemas.items import ItemCreate
from src.app.features.items.services.items import ItemService


@pytest.mark.unit
async def test_create_item_is_listed() -> None:
    service = ItemService(ItemRepository())

    item = await service.create(ItemCreate(name="Pen"))

    assert await service.list_items() == [item]
