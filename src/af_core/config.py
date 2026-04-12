"""Platform configuration loaded from environment."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "AF_"}

    database_url: str = "sqlite+aiosqlite:///./af_platform.db"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    workspace_root: str = "."


settings = Settings()
