import re
import sqlite3

from agents.orchestrator.state import SupportState
from integrations.database.ticket_repository import TicketRepository

_TICKET_PATTERN = re.compile(r"(?<!\d)\d{7}(?!\d)")


def extract_ticket_number(message: str) -> str | None:
    match = _TICKET_PATTERN.search(message)
    return match.group(0) if match else None


def query_handler_node(tickets: TicketRepository):
    def handle_query(state: SupportState) -> dict[str, str]:
        ticket_number = extract_ticket_number(state["user_message"])
        if ticket_number is None:
            return {
                "agent_used": "query_handler",
                "response": "Please include the seven-digit ticket number you want to check.",
                "error": "No valid seven-digit ticket number was found.",
            }

        try:
            ticket = tickets.get_ticket(ticket_number)
        except (sqlite3.Error, OSError) as error:
            return {
                "agent_used": "query_handler",
                "ticket_number": ticket_number,
                "response": "I could not look up that ticket right now. Please try again later.",
                "error": f"Ticket lookup failed: {error}",
            }
        if ticket is None:
            return {
                "agent_used": "query_handler",
                "ticket_number": ticket_number,
                "response": f"Ticket #{ticket_number} was not found. Please check the number and try again.",
                "error": "Ticket not found.",
            }
        status = ticket["status"]
        return {
            "agent_used": "query_handler",
            "ticket_number": ticket_number,
            "response": f"Your ticket #{ticket_number} is currently marked as: {status}.",
            "error": "",
        }

    return handle_query
