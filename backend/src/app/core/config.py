from functools import lru_cache
from typing import ClassVar, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file=".env", extra="ignore")

    log_level: str = Field(default="DEBUG", description="Logging level. Dev: DEBUG. Prod: WARNING.")
    log_format: Literal["pretty", "json"] = Field(
        default="pretty",
        description="'pretty' for dev (colored), 'json' for prod (structured).",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
