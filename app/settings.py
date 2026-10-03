from functools import lru_cache
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    tavily_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434/v1"
    arbiter_api_key: str = "dev-key-change-me"
    arbiter_db_path: str = "data/arbiter.db"
    arbiter_config: str = "config.yaml"


@lru_cache
def env() -> Env:
    return Env()


@lru_cache
def config() -> dict:
    return yaml.safe_load(Path(env().arbiter_config).read_text())
