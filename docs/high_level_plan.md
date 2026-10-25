# Banking Customer Support Multi-Agent System — High-Level Plan

This project is a banking customer support assistant built around a LangGraph multi-agent workflow, a SQLite support-ticket database, OpenAI-powered classification and response generation, and a Streamlit interface.

## 1. Goals and Scope

The assistant accepts an unstructured customer message and handles one of three intents:

- **Positive feedback:** return a personalized thank-you response.
- **Negative feedback:** create a support ticket and return an empathetic acknowledgment with its ticket number.
- **Query:** look up a ticket by its seven-digit number and return its current status, or explain that the ticket was not found.

The application also provides a dashboard for trying scenarios, inspecting ticket records, viewing agent activity, and evaluating workflow quality.

## 2. Multi-Agent Architecture

Use LangGraph's Python `StateGraph` as the workflow state machine. Each agent is a graph node; conditional edges route execution using the classifier's result.

### Shared graph state

Define a typed state that carries the information needed between nodes:

- `user_message`: incoming customer text
- `classification`: `positive_feedback`, `negative_feedback`, or `query`
- `ticket_number`: seven-digit ticket ID, when applicable
- `response`: customer-facing result
- `agent_used`: handler selected by routing
- `error`: actionable workflow or lookup error, when applicable

Nodes return state updates rather than managing routing themselves. Keep the state limited to the current request and its result.

### Nodes and routing

1. **Classifier node** — sends the message to an OpenAI model with a classification prompt and validates the result against the three supported labels.
2. **Feedback handler node** — handles both feedback classes:
   - Positive: identify a customer name if present; otherwise use a generic greeting. Use the LLM to produce a warm, concise thank-you response.
   - Negative: generate a unique seven-digit ticket number, save a ticket with initial status `Unresolved`, and use the LLM to produce an empathetic acknowledgment that includes the ticket number.
3. **Query handler node** — extracts a seven-digit ticket number from the message, looks it up in SQLite, and returns its status or a clear not-found/invalid-ticket response.

The classifier node routes positive and negative feedback to the feedback handler and queries to the query handler. Each handler writes its result to state and transitions to the graph end. The compiled graph is the single workflow entry point used by the UI.

## 3. Ticket Database

Use SQLite for local support-ticket storage. Define one table, `support_tickets`, consistently across the schema, handlers, and UI:

| Column | Type | Rules / purpose |
| --- | --- | --- |
| `ticket_id` | TEXT | Primary key; exactly seven digits |
| `customer_name` | TEXT | Nullable when the name is not provided |
| `message` | TEXT | Customer's negative-feedback message |
| `status` | TEXT | `Unresolved` or `Resolved` |
| `created_at` | TIMESTAMP | Ticket creation time |
| `updated_at` | TIMESTAMP | Most recent status update |

New tickets start with status `Unresolved`. Ticket generation must handle collisions by checking the primary key and generating another ID before insertion.

## 4. Request Flow

1. The customer enters a message in Streamlit.
2. The UI initializes graph state with the message and invokes the compiled LangGraph workflow.
3. The classifier node uses the OpenAI classification prompt and records the validated classification.
4. LangGraph conditionally routes state to the feedback or query handler.
5. The selected handler generates a response and, where applicable, creates a ticket or queries SQLite.
6. The handler records its outcome in state; the graph returns the final state to Streamlit.
7. The UI displays the classification, selected agent, response, ticket/database result, and any error.
8. The logging system records the request outcome for monitoring and debugging.

## 5. Recommended Project Structure

```text
capstone-bank-customer-support/
├── agents/
│   ├── classifier/
│   │   └── agent.py                # OpenAI classification node
│   ├── feedback_handler_agent.py   # Positive and negative feedback node
│   ├── query_handler_agent.py      # Ticket lookup node
│   └── orchestrator/
│       ├── graph.py                # LangGraph StateGraph and conditional edges
│       └── state.py                # Typed shared graph state
├── app/
│   └── ui/
│       └── streamlit_app.py        # Chat and monitoring dashboard
├── config/
│   └── settings.py                 # Environment-based configuration
├── integrations/
│   ├── database/
│   │   ├── connection.py           # SQLite connection and initialization
│   │   └── ticket_repository.py    # Ticket insert, lookup, and listing
│   └── llm/
│       └── client.py               # OpenAI client/configuration helpers
├── evaluation/
│   ├── evaluator.py                # Metrics and evaluation runner
│   └── test_cases.py               # Labeled examples and edge cases
├── tests/
│   └── agent_scenarios/
├── utils/
│   └── logger.py                   # Structured workflow logging
├── data/                           # SQLite database (created at runtime)
├── logs/                           # JSON Lines events (created at runtime)
└── docs/
```

## 6. Component Responsibilities

- **`agents/`** contains focused agents and the LangGraph orchestration. The classifier returns a supported label; handlers perform their domain action; the graph owns conditional routing.
- **`integrations/database/`** owns SQLite initialization and ticket persistence/retrieval. Agents should use the repository rather than duplicate SQL.
- **`integrations/llm/`** centralizes OpenAI client configuration and model access. Load API credentials from environment/configuration, never hard-code them.
- **`app/ui/`** invokes the compiled graph and presents chat, routing, ticket, and log views; it should not contain agent or database business logic.
- **`evaluation/`** holds labeled test scenarios and computes routing, response-quality, and ticket-generation metrics.
- **`utils/logger.py`** records structured workflow events for the dashboard and debugging, with basic redaction for email addresses and long numeric values in user input.

## 7. Streamlit Interface

Provide these dashboard sections:

- **Chat interface:** text input and generated response.
- **Agent status:** classification and agent/node that handled the request, with a simple visualization of the route.
- **Ticket viewer:** table of tickets and their statuses.
- **Logs viewer:** historical request outcomes and agent actions.
- **Test scenarios:** preloaded examples for each intent, ticket status, and edge case.

Show database interaction success/failure and workflow errors explicitly; do not present an unsuccessful lookup or ticket creation as a successful response.

## 8. Logging, Evaluation, and LLMOps

### Logging

Record timestamp, request identifier, user input, classification, selected agent, response, ticket ID when relevant, and success/failure status. Support local JSON or CSV log storage under `logs/`. Prompt traces and database actions may be included in a debug view. Avoid logging credentials or unnecessary sensitive banking/customer information.

### Evaluation

Maintain labeled cases for positive feedback, negative feedback, queries across ticket statuses, missing or malformed ticket numbers, unknown tickets, ambiguous messages, and model/DB failures. Measure:

- Classification accuracy against labeled test cases
- Agent routing success rate
- Response quality for empathy and clarity
- Ticket ID uniqueness and successful persistence
- Ticket lookup correctness, including not-found handling

Keep repeatable evaluation results in `evaluation/reports/` or the configured reporting location.

## 9. Error Handling and Operational Considerations

- Validate classifier output before routing; surface an actionable error if the model returns an unsupported label or fails.
- Handle missing/invalid ticket numbers and unknown tickets as explicit query outcomes.
- Handle SQLite and OpenAI failures explicitly, log the failure, and return a clear customer-safe message.
- Ensure ticket creation is persisted before telling the customer that a ticket was created.
- Keep API keys in environment variables or a secrets manager; do not expose them in the UI or logs.

## 10. Implementation Direction

Implement the Python agents as LangGraph nodes and compile a `StateGraph` with typed shared state and classification-based conditional edges. Use OpenAI for message classification and generated feedback responses, SQLite for ticket persistence, and Streamlit as the workflow client and monitoring UI. Build and test the database repository and individual agents, then wire and test the graph, evaluation runner, logging, and dashboard.
