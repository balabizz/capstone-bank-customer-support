import tempfile
import unittest
from pathlib import Path

from agents.orchestrator.graph import build_graph
from integrations.database.ticket_repository import TicketRepository
from integrations.llm.client import LLMServiceError


class FakeLLM:
    def classify(self, message: str) -> str:
        lowered = message.lower()
        if "charged" in lowered or "unhappy" in lowered:
            return "negative_feedback"
        if "ticket" in lowered or "status" in lowered:
            return "query"
        return "positive_feedback"

    def thank_customer(self, message: str, customer_name: str | None) -> str:
        if customer_name:
            return f"Thank you, {customer_name}!"
        return "Thank you for your kind words!"

    def acknowledge_complaint(self, message: str, ticket_number: str) -> str:
        return f"We apologize for the inconvenience. Ticket #{ticket_number} is open."


class BrokenLLM(FakeLLM):
    def classify(self, message: str) -> str:
        raise LLMServiceError("Model unavailable.")


class SupportWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "tickets.db"
        self.tickets = TicketRepository(database_path)
        self.graph = build_graph(llm=FakeLLM(), tickets=self.tickets)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_positive_feedback_uses_feedback_agent(self) -> None:
        result = self.graph.invoke(
            {"user_message": "Thanks for your help. My name is Alex."}
        )

        self.assertEqual(result["classification"], "positive_feedback")
        self.assertEqual(result["agent_used"], "feedback_handler")
        self.assertIn("Alex", result["response"])
        self.assertEqual(result["error"], "")

    def test_negative_feedback_creates_seven_digit_ticket(self) -> None:
        result = self.graph.invoke(
            {"user_message": "I am unhappy because my card was charged twice."}
        )

        self.assertEqual(result["classification"], "negative_feedback")
        self.assertRegex(result["ticket_number"], r"^\d{7}$")
        self.assertEqual(self.tickets.get_ticket(result["ticket_number"])["status"], "New")
        self.assertIn(result["ticket_number"], result["response"])

    def test_ticket_query_returns_current_status(self) -> None:
        ticket_number = self.tickets.create_ticket("A payment issue")
        self.tickets.update_status(ticket_number, "In Progress")

        result = self.graph.invoke(
            {"user_message": f"What is the status of ticket {ticket_number}?"}
        )

        self.assertEqual(result["classification"], "query")
        self.assertEqual(result["agent_used"], "query_handler")
        self.assertIn("In Progress", result["response"])

    def test_unknown_ticket_is_reported(self) -> None:
        result = self.graph.invoke({"user_message": "Check ticket 7654321"})

        self.assertEqual(result["agent_used"], "query_handler")
        self.assertEqual(result["error"], "Ticket not found.")
        self.assertIn("was not found", result["response"])

    def test_query_without_ticket_number_requests_one(self) -> None:
        result = self.graph.invoke(
            {"user_message": "Can you tell me the status of my support ticket?"}
        )

        self.assertEqual(result["agent_used"], "query_handler")
        self.assertEqual(
            result["response"],
            "Please include the seven-digit ticket number you want to check.",
        )

    def test_invalid_classifier_output_does_not_route(self) -> None:
        class InvalidClassifier(FakeLLM):
            def classify(self, message: str) -> str:
                return "billing"

        graph = build_graph(llm=InvalidClassifier(), tickets=self.tickets)

        result = graph.invoke({"user_message": "Please help me"})

        self.assertEqual(
            result["error"],
            "The classifier returned an unsupported category.",
        )
        self.assertNotIn("agent_used", result)

    def test_classifier_failure_is_returned_without_routing(self) -> None:
        graph = build_graph(llm=BrokenLLM(), tickets=self.tickets)

        result = graph.invoke({"user_message": "Please help me"})

        self.assertEqual(result["error"], "Model unavailable.")
        self.assertNotIn("agent_used", result)

    def test_empty_input_is_rejected(self) -> None:
        result = self.graph.invoke({"user_message": "  "})

        self.assertEqual(result["error"], "Please enter a message before submitting.")
        self.assertNotIn("classification", result)


if __name__ == "__main__":
    unittest.main()
