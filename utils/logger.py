import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_LONG_NUMBER = re.compile(r"(?<!\d)\d{6,}(?!\d)")


def redact_text(value: str) -> str:
    value = _EMAIL.sub("[redacted email]", value)
    return _LONG_NUMBER.sub("[redacted number]", value)


def log_event(log_path: str | Path, event: dict[str, Any]) -> None:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    if "user_input" in record:
        record["user_input"] = redact_text(str(record["user_input"]))
    with path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_events(log_path: str | Path, limit: int = 200) -> list[dict[str, Any]]:
    path = Path(log_path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as log_file:
        lines = log_file.readlines()[-limit:]
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON log entry near recent line {line_number}.") from error
        if isinstance(event, dict):
            events.append(event)
    return list(reversed(events))
