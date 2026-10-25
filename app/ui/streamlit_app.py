import sys
import uuid
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.orchestrator.graph import build_graph
from config.settings import get_settings
from integrations.database.ticket_repository import TicketRepository
from utils.logger import log_event, read_events

settings = get_settings()
tickets = TicketRepository(settings.database_path)
graph = build_graph(tickets=tickets)

st.set_page_config(page_title="Bank Customer Support", page_icon="🏦", layout="wide")
st.title("Bank Customer Support")
st.caption("A LangGraph-powered assistant for feedback and support-ticket queries.")


def process_message(message: str) -> dict[str, object]:
    result = graph.invoke({"user_message": message})
    log_event(
        settings.log_path,
        {
            "request_id": str(uuid.uuid4()),
            "user_input": message,
            "classification": result.get("classification"),
            "agent_used": result.get("agent_used"),
            "response": result.get("response"),
            "ticket_number": result.get("ticket_number"),
            "success": not bool(result.get("error")),
            "error": result.get("error"),
        },
    )
    st.session_state["last_result"] = result
    return result


chat_tab, ticket_tab, logs_tab, scenarios_tab = st.tabs(
    ["Chat", "Ticket Viewer", "Logs", "Test Scenarios"]
)

with chat_tab:
    with st.form("support_message_form"):
        user_message = st.text_area(
            "How can we help?",
            placeholder="Share feedback or ask about a seven-digit support ticket.",
            height=120,
        )
        submitted = st.form_submit_button("Send message", type="primary")

    if submitted:
        process_message(user_message)

    result = st.session_state.get("last_result")
    if result:
        left, right = st.columns(2)
        left.metric("Classification", result.get("classification", "Not classified"))
        right.metric("Agent", result.get("agent_used", "None"))
        if result.get("ticket_number"):
            st.info(f"Ticket number: **{result['ticket_number']}**")
        if result.get("error"):
            st.warning(result["error"])
        st.markdown("**Assistant response**")
        st.write(result.get("response", "No response was generated."))

with ticket_tab:
    st.subheader("Support tickets")
    ticket_rows = tickets.list_tickets()
    if ticket_rows:
        st.dataframe(ticket_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No support tickets have been created yet.")

with logs_tab:
    st.subheader("Recent agent activity")
    try:
        events = read_events(settings.log_path)
    except (OSError, ValueError) as error:
        st.error(f"Could not read the application log: {error}")
    else:
        if events:
            st.dataframe(events, use_container_width=True, hide_index=True)
        else:
            st.info("No workflow events have been logged yet.")

with scenarios_tab:
    st.subheader("Try a sample scenario")
    sample_scenarios = {
        "Positive feedback": "Thank you for helping me with my transfer. My name is Alex.",
        "Negative feedback": "I was charged twice and need help resolving it.",
        "Ticket status": "Can you check the status of ticket 1234567?",
        "Ticket number missing": "Can you tell me the status of my support ticket?",
    }
    selected_scenario = st.selectbox("Scenario", list(sample_scenarios))
    scenario_message = sample_scenarios[selected_scenario]
    st.code(scenario_message)
    if st.button("Run scenario"):
        scenario_result = process_message(scenario_message)
        st.write(
            f"Classification: {scenario_result.get('classification', 'Not classified')}"
        )
        if scenario_result.get("error"):
            st.warning(str(scenario_result["error"]))
        st.write(scenario_result.get("response", "No response was generated."))
