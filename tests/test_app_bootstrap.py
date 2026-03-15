"""Tests for FastAPI application bootstrap and configuration."""

import os

import pytest
from fastapi.testclient import TestClient

from src.app.config import Settings
from src.app.main import create_app


def _test_settings(**overrides) -> Settings:
    """Return a Settings instance with safe test defaults."""
    defaults = {
        "app_env": "testing",
        "telegram_bot_token": "test-token",
        "openrouter_api_key": "test-key",
        "apify_api_token": "test-apify",
        "database_url": "postgresql://test:test@localhost:5432/test",
        "redis_url": "redis://localhost:6379/1",
    }
    defaults.update(overrides)
    return Settings(**defaults)


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.app_env == "development"
        assert s.debug is False
        assert s.openrouter_model == "anthropic/claude-3-haiku"
        assert s.database_url.startswith("postgresql")
        assert s.redis_url.startswith("redis://")

    def test_override_via_kwargs(self):
        s = Settings(app_env="production", debug=True)
        assert s.app_env == "production"
        assert s.debug is True

    def test_env_fields_present(self):
        """Confirm all expected integration env vars are declared."""
        s = Settings()
        assert hasattr(s, "telegram_bot_token")
        assert hasattr(s, "openrouter_api_key")
        assert hasattr(s, "apify_api_token")

    def test_settings_loaded_from_environment(self, monkeypatch):
        """Settings should read values injected via environment variables."""
        monkeypatch.setenv("APP_ENV", "staging")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env-token")
        s = Settings()
        assert s.app_env == "staging"
        assert s.debug is True
        assert s.telegram_bot_token == "env-token"

    def test_database_url_default_is_driver_agnostic(self):
        """Default database_url must not reference a driver that isn't installed."""
        s = Settings()
        assert "asyncpg" not in s.database_url


class TestCreateApp:
    def test_returns_fastapi_instance(self):
        from fastapi import FastAPI

        app = create_app(settings=_test_settings())
        assert isinstance(app, FastAPI)

    def test_settings_attached_to_state(self):
        settings = _test_settings(app_env="testing")
        app = create_app(settings=settings)
        assert app.state.settings is settings

    def test_debug_propagated(self):
        app = create_app(settings=_test_settings(debug=True))
        assert app.debug is True

    def test_app_title(self):
        app = create_app(settings=_test_settings())
        assert app.title == "flatscanner"


class TestCreateAppFreshSettings:
    def test_create_app_reads_env_without_explicit_settings(self, monkeypatch):
        """create_app() must read current env vars, not a cached Settings instance."""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("APP_ENV", "testing")
        app = create_app()
        assert app.debug is True
        assert app.state.settings.app_env == "testing"

    def test_create_app_produces_independent_instances(self, monkeypatch):
        """Two create_app() calls with different env vars must yield independent apps."""
        monkeypatch.setenv("APP_ENV", "first")
        app1 = create_app()
        monkeypatch.setenv("APP_ENV", "second")
        app2 = create_app()
        assert app1.state.settings.app_env == "first"
        assert app2.state.settings.app_env == "second"


class TestHealthEndpoint:
    def test_health_returns_200(self):
        app = create_app(settings=_test_settings())
        with TestClient(app) as client:
            response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self):
        app = create_app(settings=_test_settings())
        with TestClient(app) as client:
            response = client.get("/health")
        assert response.json() == {"status": "ok"}
