"""Settings, read once from environment variables (and the repo-root .env file)."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _flag(name: str) -> bool | None:
    value = os.getenv(name, "").strip().lower()
    if value in ("1", "true", "yes"):
        return True
    if value in ("0", "false", "no"):
        return False
    return None


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENFDA_API_KEY = os.getenv("OPENFDA_API_KEY", "")
MODEL = os.getenv("PILLPAL_MODEL", "claude-opus-5-5")

# Demo mode skips the Claude calls and uses a built-in sample medication list,
# so the app runs end to end without an API key. RxNorm/openFDA are still live.
_demo = _flag("PILLPAL_DEMO_MODE")
DEMO_MODE = _demo if _demo is not None else not ANTHROPIC_API_KEY

CACHE_DIR = Path(os.getenv("PILLPAL_CACHE_DIR", str(ROOT / "backend" / ".cache")))

FRONTEND_ORIGINS = [
    o.strip()
    for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

# Readings below this confidence are flagged for manual review.
LOW_CONFIDENCE = 0.7

LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "zh": "Simplified Chinese",
    "vi": "Vietnamese",
    "tl": "Tagalog",
    "ko": "Korean",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
    "fr": "French",
    "ht": "Haitian Creole",
    "pt": "Portuguese",
}
