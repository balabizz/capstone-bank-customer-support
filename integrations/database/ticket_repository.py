import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import get_settings
from integrations.database.connection import initialize_database, managed_connection

TICKET_STATUSES = ("New", "In Progress", "Resolved")


class TicketRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self._settings = get_settings()
        initialize_database(self.database_path)

    def create_ticket(
        self,
        message: str,
        customer_name: str | None = None,
    ) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        with managed_connection(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for _ in range(self._settings.ticket_id_generation_attempts):
                ticket_number = f"{secrets.randbelow(9_000_000) + 1_000_000:07d}"
                try:
                    connection.execute(
                        """
                        INSERT INTO support_tickets
                            (ticket_id, customer_name, message, status, created_at, updated_at)
                        VALUES (?, ?, ?, 'New', ?, ?)
                        """,
                        (ticket_number, customer_name, message, timestamp, timestamp),
                    )
                    return ticket_number
                except sqlite3.IntegrityError as error:
                    if "UNIQUE constraint failed: support_tickets.ticket_id" not in str(error):
                        raise
            raise RuntimeError(
                "Could not generate a unique ticket number after "
                f"{self._settings.ticket_id_generation_attempts} attempts."
            )

    def get_ticket(self, ticket_number: str) -> dict[str, Any] | None:
        with managed_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM support_tickets WHERE ticket_id = ?",
                (ticket_number,),
            ).fetchone()
        return dict(row) if row is not None else None

    def list_tickets(self, limit: int | None = None) -> list[dict[str, Any]]:
        if limit is None:
            limit = self._settings.ticket_list_limit
        with managed_connection(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM support_tickets ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_status(self, ticket_number: str, status: str) -> bool:
        if status not in TICKET_STATUSES:
            raise ValueError(f"Unsupported ticket status: {status}")
        timestamp = datetime.now(timezone.utc).isoformat()
        with managed_connection(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE support_tickets
                SET status = ?, updated_at = ?
                WHERE ticket_id = ?
                """,
                (status, timestamp, ticket_number),
            )
        return cursor.rowcount == 1
