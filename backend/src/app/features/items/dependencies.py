from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType] -- dishka types it with Any
)

from src.app.features.items.repository import ItemRepository
from src.app.features.items.service import ItemService


class ItemsProvider(Provider):
    """The feature's providers, like a Nest module's `providers` list."""

    @provide(scope=Scope.APP)  # in-memory store: one per app
    def repository(self) -> ItemRepository:
        return ItemRepository()

    @provide(scope=Scope.REQUEST)
    def service(self, repository: ItemRepository) -> ItemService:
        return ItemService(repository)
