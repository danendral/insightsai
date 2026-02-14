"""
core/config.py - Application Settings

WHY THIS EXISTS:
  Before: os.getenv("ANTHROPIC_API_KEY") scattered everywhere in main.py.
  Now: One typed Settings object. Import it anywhere, always consistent.

HOW pydantic-settings WORKS:
  1. Define fields as class attributes with types
  2. Pydantic reads values from environment variables automatically
     (it matches field name → env var name, case-insensitive)
  3. If a required field is missing, it raises a clear ValidationError at
     startup — you find out immediately, not buried inside a 500 error

DEPENDENCY INJECTION PATTERN:
  FastAPI's Depends() lets you inject get_settings() into any endpoint.
  That means you can swap out settings in tests without monkey-patching.

  Example endpoint usage:
      @router.post("/query")
      async def query(settings: Settings = Depends(get_settings)):
          client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------------------------------------------------------------ #
    # Anthropic
    # ------------------------------------------------------------------ #
    anthropic_api_key: str  # Required — app won't start without it

    # ------------------------------------------------------------------ #
    # File handling
    # ------------------------------------------------------------------ #
    max_file_size_bytes: int = 10 * 1024 * 1024  # 10 MB default
    upload_dir: Path = Path(__file__).parent.parent / "uploads"
    sample_data_path: Path = Path(__file__).parent.parent / "sample_data" / "sales_data.csv"

    # ------------------------------------------------------------------ #
    # AI model
    # ------------------------------------------------------------------ #
    ai_model: str = "claude-sonnet-4-5-20250929"
    ai_max_tokens: int = 1024

    # ------------------------------------------------------------------ #
    # Pydantic-settings config
    # ------------------------------------------------------------------ #
    # env_file: which .env file to read
    # extra="ignore": silently ignore unknown env vars (e.g. PATH, HOME)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    lru_cache means this function only runs ONCE per process.
    Every call after the first returns the same object — no repeated
    disk reads or validation.

    In tests, call get_settings.cache_clear() to force re-creation
    with test environment variables.
    """
    return Settings()
