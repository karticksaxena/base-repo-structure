from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100, description="Display name of the item.")


class ItemResponse(BaseModel):
    id: int = Field(description="Item ID.")
    name: str = Field(description="Display name of the item.")
