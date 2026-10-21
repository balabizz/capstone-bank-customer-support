from typing import Protocol

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents.classifier.agent import classifier_node
from agents.feedback_handler_agent import feedback_handler_node
from agents.orchestrator.state import SupportState
from agents.query_handler_agent import query_handler_node
from config.settings import get_settings
from integrations.database.ticket_repository import TicketRepository
from integrations.llm.client import OpenAIService


class SupportLLM(Protocol):
    def classify(self, message: str) -> str: ...

    def thank_customer(self, message: str, customer_name: str | None) -> str: ...

    def acknowledge_complaint(self, message: str, ticket_number: str) -> str: ...


def build_graph(
    llm: SupportLLM | None = None,
    tickets: TicketRepository | None = None,
) -> CompiledStateGraph:
    settings = get_settings()
    language_model = llm or OpenAIService()
    ticket_repository = tickets or TicketRepository(settings.database_path)

    builder = StateGraph(SupportState)
    builder.add_node("classifier", classifier_node(language_model))
    builder.add_node(
        "feedback_handler",
        feedback_handler_node(language_model, ticket_repository),
    )
    builder.add_node("query_handler", query_handler_node(ticket_repository))
    builder.add_edge(START, "classifier")

    def route_classification(state: SupportState) -> str:
        if state.get("error"):
            return "end"
        if state.get("classification") in {"positive_feedback", "negative_feedback"}:
            return "feedback_handler"
        if state.get("classification") == "query":
            return "query_handler"
        return "end"

    builder.add_conditional_edges(
        "classifier",
        route_classification,
        {
            "feedback_handler": "feedback_handler",
            "query_handler": "query_handler",
            "end": END,
        },
    )
    builder.add_edge("feedback_handler", END)
    builder.add_edge("query_handler", END)
    return builder.compile()
