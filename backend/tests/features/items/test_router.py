import pytest
from fastapi.testclient import TestClient

from src.app.features.items.schemas.items import ItemResponse


@pytest.mark.unit
def test_create_then_list_items(client: TestClient) -> None:
    created = client.post("/items", json={"name": "  Pen  "})

    assert created.status_code == 201
    item = ItemResponse.model_validate_json(created.content)
    assert item.name == "Pen"
    assert item.id.version == 7
    assert client.get("/items").json() == {
        "items": [item.model_dump(mode="json")],
        "total": 1,
        "limit": 20,
        "offset": 0,
    }


@pytest.mark.unit
def test_create_item_rejects_unknown_fields(client: TestClient) -> None:
    response = client.post("/items", json={"name": "Pen", "price": 1})

    assert response.status_code == 422


@pytest.mark.unit
@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_list_items_rejects_out_of_range_paging(client: TestClient, query: str) -> None:
    assert client.get(f"/items?{query}").status_code == 422
