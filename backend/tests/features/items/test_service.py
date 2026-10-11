import pytest

from src.app.features.items.repositories.items import ItemRepository
from src.app.features.items.schemas.items import ItemCreate
from src.app.features.items.services.items import ItemService


@pytest.mark.unit
async def test_list_items_returns_requested_page() -> None:
    service = ItemService(ItemRepository())
    first = await service.create(ItemCreate(name="Pen"))
    second = await service.create(ItemCreate(name="Book"))

    page = await service.list_items(limit=1, offset=1)

    assert page.items == [second]
    assert page.total == 2
    assert first not in page.items
