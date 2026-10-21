from typing import Literal, TypedDict
from typing_extensions import NotRequired

Classification = Literal["positive_feedback", "negative_feedback", "query"]


class SupportState(TypedDict):
    user_message: str
    classification: NotRequired[Classification]
    ticket_number: NotRequired[str]
    response: NotRequired[str]
    agent_used: NotRequired[str]
    error: NotRequired[str]
