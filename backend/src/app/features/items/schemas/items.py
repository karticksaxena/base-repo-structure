from uuid import UUID

from pydantic import Field

from src.app.common.schemas import BaseSchema


class ItemCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=100, description="Display name of the item.")


class ItemResponse(BaseSchema):
    id: UUID = Field(description="Item ID (UUIDv7).")
    name: str = Field(description="Display name of the item.")
