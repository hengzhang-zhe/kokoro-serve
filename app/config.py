from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Kokoro Serve"
    app_version: str = "0.1.0"

    model_repo: str = "hexgrad/Kokoro-82M"
    device: str = "cpu"

    max_input_chars: int = 4096
    max_concurrency: int = 2
    sample_rate: int = 24000

    model_config = SettingsConfigDict(
        env_prefix="KOKORO_SERVE_",
        env_file=".env",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
