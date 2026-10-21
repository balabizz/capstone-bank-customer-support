import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    database_path: Path
    log_path: Path


def get_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    database_path = Path(os.getenv("SUPPORT_DB_PATH", "data/support_tickets.db"))
    log_path = Path(os.getenv("AGENT_LOG_PATH", "logs/agent_events.jsonl"))
    if not database_path.is_absolute():
        database_path = PROJECT_ROOT / database_path
    if not log_path.is_absolute():
        log_path = PROJECT_ROOT / log_path
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        database_path=database_path,
        log_path=log_path,
    )
