import pytest

from src.app.features.items.repository import ItemRepository
from src.app.features.items.schemas import ItemCreate
from src.app.features.items.service import ItemService


@pytest.mark.unit
async def test_create_item_is_listed() -> None:
    service = ItemService(ItemRepository())

    item = await service.create(ItemCreate(name="Pen"))

    assert await service.list_items() == [item]
