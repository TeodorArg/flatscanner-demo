from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    debug: bool = False

    # Telegram
    telegram_bot_token: str = ""

    # Database – asyncpg driver will be added when storage layer lands
    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/flatscanner"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3-haiku"

    # Apify
    apify_api_token: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
