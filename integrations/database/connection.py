from contextlib import contextmanager
import sqlite3
from pathlib import Path
from collections.abc import Iterator

from config.settings import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id TEXT PRIMARY KEY CHECK (
        length(ticket_id) = 7 AND ticket_id NOT GLOB '*[^0-9]*'
    ),
    customer_name TEXT,
    message TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('New', 'In Progress', 'Resolved')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def connect(
    database_path: str | Path,
    timeout: float | None = None,
) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if timeout is None:
        timeout = get_settings().database_timeout_seconds
    connection = sqlite3.connect(path, timeout=timeout)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def managed_connection(
    database_path: str | Path,
    timeout: float | None = None,
) -> Iterator[sqlite3.Connection]:
    connection = connect(database_path, timeout)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(database_path: str | Path) -> None:
    with managed_connection(database_path) as connection:
        connection.execute(SCHEMA)
