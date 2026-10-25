import re
import sqlite3
from typing import Protocol

from agents.orchestrator.state import SupportState
from integrations.database.ticket_repository import TicketRepository
from integrations.llm.client import LLMServiceError

_NAME_PATTERNS = (
    re.compile(r"\bmy name is\s+([A-Za-z][A-Za-z' -]{0,60})", re.IGNORECASE),
    re.compile(r"\bthis is\s+([A-Za-z][A-Za-z' -]{0,60})", re.IGNORECASE),
    re.compile(r"\bi am\s+([A-Za-z][A-Za-z' -]{0,60})", re.IGNORECASE),
)


class FeedbackLLM(Protocol):
    def thank_customer(self, message: str, customer_name: str | None) -> str: ...

    def acknowledge_complaint(self, message: str, ticket_number: str) -> str: ...


def extract_customer_name(message: str) -> str | None:
    for pattern in _NAME_PATTERNS:
        match = pattern.search(message)
        if match:
            name = re.split(r"[,!.?;\n]", match.group(1), maxsplit=1)[0].strip()
            name = re.split(r"\b(?:and|but|because|i)\b", name, maxsplit=1, flags=re.IGNORECASE)[0]
            name = name.strip()
            if name and name[0].isupper():
                return name
    return None


def feedback_handler_node(llm: FeedbackLLM, tickets: TicketRepository):
    def handle_feedback(state: SupportState) -> dict[str, str]:
        message = state["user_message"].strip()
        classification = state.get("classification", "")
        if classification == "positive_feedback":
            customer_name = extract_customer_name(message)
            try:
                response = llm.thank_customer(message, customer_name)
                return {
                    "agent_used": "feedback_handler",
                    "response": response,
                    "error": "",
                }
            except LLMServiceError as error:
                return {
                    "agent_used": "feedback_handler",
                    "response": "Thank you for your kind words! We're delighted to assist you.",
                    "error": f"Generated a standard thank-you because the language model failed: {error}",
                }

        if classification != "negative_feedback":
            return {
                "agent_used": "feedback_handler",
                "response": "The feedback category was not recognized.",
                "error": "Feedback handler received an unsupported classification.",
            }

        customer_name = extract_customer_name(message)
        try:
            ticket_number = tickets.create_ticket(message, customer_name)
        except (sqlite3.Error, OSError, RuntimeError) as error:
            return {
                "agent_used": "feedback_handler",
                "response": "I could not create a support ticket. Please try again later.",
                "error": f"Ticket creation failed: {error}",
            }

        try:
            response = llm.acknowledge_complaint(message, ticket_number)
            error_message = ""
        except LLMServiceError as error:
            response = (
                "We apologize for the inconvenience. A new ticket "
                f"#{ticket_number} has been generated, and our team will follow up shortly."
            )
            error_message = (
                f"Ticket {ticket_number} was created; a standard acknowledgment was used "
                f"because the language model failed: {error}"
            )
        return {
            "agent_used": "feedback_handler",
            "ticket_number": ticket_number,
            "response": response,
            "error": error_message,
        }

    return handle_feedback
