from typing import Protocol

from agents.orchestrator.state import SupportState
from integrations.llm.client import LLMServiceError

ALLOWED_CLASSIFICATIONS = {"positive_feedback", "negative_feedback", "query"}


class ClassifierLLM(Protocol):
    def classify(self, message: str) -> str: ...


def classifier_node(llm: ClassifierLLM):
    def classify_message(state: SupportState) -> dict[str, str]:
        message = state["user_message"].strip()
        if not message:
            return {
                "error": "Please enter a message before submitting.",
                "response": "I could not process an empty message.",
            }
        try:
            classification = llm.classify(message).strip().lower()
        except LLMServiceError as error:
            return {
                "error": str(error),
                "response": "I could not classify your message. Please try again later.",
            }
        if classification not in ALLOWED_CLASSIFICATIONS:
            return {
                "error": "The classifier returned an unsupported category.",
                "response": "I could not determine how to route your message. Please try rephrasing it.",
            }
        return {"classification": classification, "error": ""}

    return classify_message
