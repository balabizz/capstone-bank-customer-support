import math
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
    database_timeout_seconds: float
    ticket_list_limit: int
    ticket_id_generation_attempts: int


def _positive_int_setting(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive integer.") from error
    if parsed <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return parsed


def _positive_float_setting(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive finite number.") from error
    if parsed <= 0 or not math.isfinite(parsed):
        raise ValueError(f"{name} must be a positive finite number.")
    return parsed


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
        database_timeout_seconds=_positive_float_setting(
            "SUPPORT_DB_TIMEOUT_SECONDS", 10.0
        ),
        ticket_list_limit=_positive_int_setting("SUPPORT_TICKET_LIST_LIMIT", 500),
        ticket_id_generation_attempts=_positive_int_setting(
            "SUPPORT_TICKET_ID_GENERATION_ATTEMPTS", 20
        ),
    )
