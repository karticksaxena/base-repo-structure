from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider

from src.app.features.items.dependencies import ItemsProvider


def create_container() -> AsyncContainer:
    return make_async_container(FastapiProvider(), ItemsProvider())
