from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunMode(str, Enum):
    STUB = "stub"
    MANUAL = "manual"
    LIVE = "live"


class Profile(str, Enum):
    LOCAL = "local"
    SERVER = "server"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCHWERKPUNKT_", extra="ignore")

    mode: RunMode = RunMode.STUB
    profile: Profile = Profile.LOCAL
    data_dir: str = "./data"
    fixtures_dir: str = "./fixtures"
    rules_path: str = "./fixtures/igc_rules.json"
    host: str = "127.0.0.1"
    port: int = 8000
    database_url: str = "postgresql://schwerpunkt:schwerpunkt@127.0.0.1:5432/schwerpunkt"
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    @property
    def db_path(self) -> str:
        return f"{self.data_dir}/schwerpunkt.db"


def get_settings() -> Settings:
    return Settings()
