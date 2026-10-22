"""Root module (NestJS AppModule): the dishka container with every feature's Provider."""

from dishka import AsyncContainer, Provider, make_async_container
from dishka.integrations.fastapi import FastapiProvider

from src.app.features.items.dependencies import ItemsProvider


def create_container(*overrides: Provider) -> AsyncContainer:
    """`overrides` replace the providers of the same types (tests; Nest's `overrideProvider`)."""
    return make_async_container(FastapiProvider(), ItemsProvider(), *overrides)
