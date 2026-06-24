"""
Application configuration and constants
"""
import os
import sys
from pathlib import Path

# Model Configuration
MODEL_NAME = "models/gemini-2.5-flash"


# Paths
FAISS_INDEX_DIR = Path("storage/labour_faiss")
FAISS_STATS_PATH = FAISS_INDEX_DIR / "stats.json"

# Retrieval Configuration
CHUNK_SIZE = 2000  # BGE-M3 can handle up to 8192 tokens
CHUNK_OVERLAP = 200
TOP_K_DOCUMENTS = 6  # Default fallback (now using dynamic retrieval)

# Dynamic Retrieval Settings
ENABLE_DYNAMIC_RETRIEVAL = True  # Set to False to use fixed TOP_K_DOCUMENTS
MIN_DOCUMENTS = 2  # Minimum documents to retrieve
MAX_DOCUMENTS = 6  # Maximum documents to retrieve

# Ensure UTF-8 support
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def get_api_key() -> str:
    """Get Google API key from environment"""
    return os.environ.get("GOOGLE_API_KEY", "").strip()


def validate_api_key() -> bool:
    """Check if API key is valid"""
    key = get_api_key()
    return bool(key and key != "YOUR_GEMINI_API_KEY_HERE")
