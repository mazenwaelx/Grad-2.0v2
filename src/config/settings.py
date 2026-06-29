"""
Application configuration and constants.

Uses Pydantic BaseSettings for validation and .env support.
"""
import os
import sys
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class RetrievalSettings(BaseSettings):
    """Configuration for document retrieval."""

    chunk_size: int = Field(
        default=2000,
        description="BGE-M3 can handle up to 8192 tokens",
    )
    chunk_overlap: int = Field(default=200)
    top_k_documents: int = Field(
        default=6,
        description="Default fallback (now using dynamic retrieval)",
    )
    enable_dynamic_retrieval: bool = Field(default=True)
    min_documents: int = Field(default=2)
    max_documents: int = Field(default=6)


class AppSettings(BaseSettings):
    """Top-level application settings."""

    model_name: str = Field(default="models/gemini-2.5-flash")
    google_api_key: str = Field(default="")

    # Paths
    faiss_index_dir: Path = Field(default=Path("storage/labour_faiss"))

    # Nested settings
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)

    model_config = {"env_prefix": "", "env_nested_delimiter": "__"}

    # ── Derived paths ──────────────────────────────────────────────
    @property
    def faiss_stats_path(self) -> Path:
        return self.faiss_index_dir / "stats.json"

    # ── API-key helpers ────────────────────────────────────────────
    def get_api_key(self) -> str:
        """Return the Google API key (stripped)."""
        key = self.google_api_key or os.environ.get("GOOGLE_API_KEY", "")
        return key.strip()

    def validate_api_key(self) -> bool:
        """Return *True* if the API key looks usable."""
        key = self.get_api_key()
        return bool(key and key != "YOUR_GEMINI_API_KEY_HERE")


# ── Module-level singleton ─────────────────────────────────────────
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Return (and lazily create) the global settings instance."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def configure_utf8() -> None:
    """Ensure stdout / stderr use UTF-8 encoding.

    Call this once at application startup — not at import time.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


# ── Backward-compatible module-level constants ─────────────────────
# These are kept so existing ``from src.config.settings import MODEL_NAME``
# statements continue to work without any change.
_s = get_settings()

MODEL_NAME: str = _s.model_name
FAISS_INDEX_DIR: Path = _s.faiss_index_dir
FAISS_STATS_PATH: Path = _s.faiss_stats_path
CHUNK_SIZE: int = _s.retrieval.chunk_size
CHUNK_OVERLAP: int = _s.retrieval.chunk_overlap
TOP_K_DOCUMENTS: int = _s.retrieval.top_k_documents
ENABLE_DYNAMIC_RETRIEVAL: bool = _s.retrieval.enable_dynamic_retrieval
MIN_DOCUMENTS: int = _s.retrieval.min_documents
MAX_DOCUMENTS: int = _s.retrieval.max_documents


def get_api_key() -> str:
    """Backward-compatible wrapper."""
    return get_settings().get_api_key()


def validate_api_key() -> bool:
    """Backward-compatible wrapper."""
    return get_settings().validate_api_key()
