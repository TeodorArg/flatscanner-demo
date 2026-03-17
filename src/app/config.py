from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_ENVS = frozenset({"development", "testing"})


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
    # Shared secret for webhook authentication (X-Telegram-Bot-Api-Secret-Token).
    # Required in all environments except 'development' and 'testing'.
    telegram_webhook_secret: str = ""

    @model_validator(mode="after")
    def _require_credentials_outside_dev(self) -> "Settings":
        if self.app_env not in _DEV_ENVS:
            if not self.telegram_webhook_secret:
                raise ValueError(
                    "telegram_webhook_secret must be set when app_env is not "
                    "'development' or 'testing'"
                )
            if not self.telegram_bot_token:
                raise ValueError(
                    "telegram_bot_token must be set when app_env is not "
                    "'development' or 'testing'"
                )
            if not self.apify_api_token:
                raise ValueError(
                    "apify_api_token must be set when app_env is not "
                    "'development' or 'testing'"
                )
            if not self.openrouter_api_key:
                raise ValueError(
                    "openrouter_api_key must be set when app_env is not "
                    "'development' or 'testing'"
                )
        return self

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
    # Actor used to scrape Airbnb listings.  Override to switch to a different
    # actor version without changing application code.
    apify_airbnb_actor_id: str = "dtrungtin~airbnb-scraper"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
