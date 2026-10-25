import sqlite3
import tempfile
import unittest
from pathlib import Path

from integrations.database.connection import SCHEMA, managed_connection
from integrations.database.ticket_repository import TicketRepository


class TicketStatusTests(unittest.TestCase):
    def test_legacy_statuses_migrate_without_losing_ticket_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.db"
            legacy_schema = SCHEMA.replace(
                "'Unresolved', 'Resolved'", "'New', 'In Progress', 'Resolved'"
            )
            rows = [
                (str(1000000 + i), "Alex", "Payment issue", status, "created", "updated")
                for i, status in enumerate(("New", "In Progress", "Resolved"))
            ]
            with sqlite3.connect(path) as connection:
                connection.execute(legacy_schema)
                connection.executemany(
                    "INSERT INTO support_tickets VALUES (?, ?, ?, ?, ?, ?)", rows
                )
            tickets = TicketRepository(path)
            TicketRepository(path)  # Initialization is safe to repeat.
            for row, status in zip(rows, ("Unresolved", "Unresolved", "Resolved")):
                ticket = tickets.get_ticket(row[0])
                self.assertEqual(tuple(ticket.values()), (*row[:3], status, *row[4:]))
            self.assertEqual(tickets.get_ticket(tickets.create_ticket("New complaint"))["status"], "Unresolved")

    def test_only_required_statuses_are_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.db"
            tickets = TicketRepository(path)
            number = tickets.create_ticket("Complaint")
            for status in ("Resolved", "Unresolved"):
                self.assertTrue(tickets.update_status(number, status))
                self.assertEqual(tickets.get_ticket(number)["status"], status)
            for status in ("New", "In Progress", "Closed"):
                with self.assertRaises(ValueError):
                    tickets.update_status(number, status)
                with self.assertRaises(sqlite3.IntegrityError):
                    with managed_connection(path) as connection:
                        connection.execute(
                            "UPDATE support_tickets SET status = ? WHERE ticket_id = ?",
                            (status, number),
                        )
