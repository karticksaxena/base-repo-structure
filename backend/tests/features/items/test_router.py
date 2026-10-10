import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_create_then_list_items(client: TestClient) -> None:
    created = client.post("/items", json={"name": "  Pen  "})

    assert created.status_code == 201
    assert created.json() == {"id": 1, "name": "Pen"}
    assert client.get("/items").json() == [{"id": 1, "name": "Pen"}]


@pytest.mark.unit
def test_create_item_rejects_unknown_fields(client: TestClient) -> None:
    response = client.post("/items", json={"name": "Pen", "price": 1})

    assert response.status_code == 422
