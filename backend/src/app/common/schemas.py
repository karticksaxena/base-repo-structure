"""Schemas shared by every feature: strict request checking and one shape for list responses."""

from typing import Annotated, ClassVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base for every request/response schema: unknown fields are rejected, strings are trimmed."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Page[T](BaseSchema):
    """One shape for every list response, so the frontend handles all lists the same way."""

    items: list[T] = Field(description="The items on this page.")
    total: int = Field(description="Number of items across all pages.")
    limit: int = Field(description="Maximum number of items per page.")
    offset: int = Field(description="Number of items skipped before this page.")


# Query parameters for list endpoints: `limit: Limit = 20, offset: Offset = 0`
Limit = Annotated[int, Query(ge=1, le=100, description="Maximum number of items to return.")]
Offset = Annotated[int, Query(ge=0, description="Number of items to skip.")]
