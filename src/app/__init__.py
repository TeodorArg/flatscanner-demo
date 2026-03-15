# FastAPI application bootstrap and shared configuration
from src.app.main import create_app
from src.app.config import Settings, get_settings

__all__ = ["create_app", "Settings", "get_settings"]
