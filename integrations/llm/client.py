from openai import APIError, OpenAI

from config.settings import get_settings

CLASSIFICATION_PROMPT = """Classify the customer message into exactly one category:
positive_feedback, negative_feedback, or query.

positive_feedback means praise, thanks, or other favorable feedback.
negative_feedback means a complaint or dissatisfaction that needs follow-up.
Messages containing a valid seven-digit ticket number are routed to ticket lookup
by the application before this classification step.
For messages without a ticket number, classify by sentiment first:
- Complaints, dissatisfaction, frustration, or unresolved problems are negative_feedback,
  even when phrased as a question or asking for a ticket update without its number.
- Praise or thanks are positive_feedback.
- Neutral questions or requests for information are query.
For example, "Why is my transfer still delayed?" and "I am unhappy; where is my ticket?"
are negative_feedback. "Can you check my ticket status?" is query.
Return only the category label, with no punctuation or explanation."""


class LLMServiceError(RuntimeError):
    """An expected model configuration or request failure."""


class OpenAIService:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.openai_model

    def _client(self) -> OpenAI:
        if not self._api_key:
            raise LLMServiceError(
                "OpenAI is not configured. Set OPENAI_API_KEY in the project .env file."
            )
        return OpenAI(api_key=self._api_key)

    def _generate(self, instructions: str, message: str) -> str:
        try:
            response = self._client().responses.create(
                model=self.model,
                instructions=instructions,
                input=message,
            )
        except APIError as error:
            raise LLMServiceError(
                "The language model request failed. Check the API configuration and try again."
            ) from error
        result = response.output_text.strip()
        if not result:
            raise LLMServiceError("The language model returned an empty response.")
        return result

    def classify(self, message: str) -> str:
        return self._generate(CLASSIFICATION_PROMPT, message).strip().lower()

    def thank_customer(self, message: str, customer_name: str | None) -> str:
        instructions = (
            "You represent Bank Customer Support. "
            "Write a concise, warm thank-you for positive feedback. "
            "Return only the message body without a greeting, customer name, or signature; "
            "the application adds the salutation and Regards, Customer Support signature. "
            "Do not invent details."
        )
        return self._generate(instructions, message)

    def acknowledge_complaint(self, message: str, ticket_number: str) -> str:
        instructions = (
            "You represent Bank Customer Support. "
            "Return only the message body without a greeting or signature; "
            "the application adds the salutation and Regards, Customer Support signature. "
            "Write a brief, empathetic acknowledgment of the customer's complaint. "
            "Apologize for the inconvenience, say the support team will follow up, "
            f"and include this ticket number exactly: {ticket_number}. "
            "Do not claim the issue is already resolved."
        )
        return self._generate(instructions, message)
