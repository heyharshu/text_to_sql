"""Load configuration without printing or logging credentials."""
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
import os

from dotenv import load_dotenv
from .errors import AppError

ROOT = Path(__file__).resolve().parents[1]
TABLES = ("customers", "products", "orders", "order_items")


@dataclass(frozen=True)
class Settings:
    database_url: str = field(repr=False)
    ollama_url: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:7b"
    max_rows: int = 200
    statement_timeout_ms: int = 10000
    model_timeout_seconds: int = 180


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env", override=False)
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise AppError("Add DATABASE_URL to your .env file, then restart the app.")
    ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    try:
        parsed = urlsplit(ollama_url)
        if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
                or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
            raise ValueError
        parsed.port
        max_rows = int(os.getenv("MAX_ROWS", "200"))
        timeout = int(os.getenv("STATEMENT_TIMEOUT_MS", "10000"))
        model_timeout = int(os.getenv("MODEL_TIMEOUT_SECONDS", "180"))
        if not 1 <= max_rows <= 1000 or not 100 <= timeout <= 60000 or not 10 <= model_timeout <= 600:
            raise ValueError
    except ValueError:
        raise AppError("Check .env: Ollama must use a local HTTP address; row and timeout limits must be in range.") from None
    return Settings(database_url, ollama_url, os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), max_rows, timeout, model_timeout)
