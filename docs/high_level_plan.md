# Banking Customer Support Multi-Agent System — High-Level Plan

This project is based on the capstone brief in the workspace PDF: a banking customer support assistant using a multi-agent architecture, with a Streamlit interface and Python-based services.

## 1. Solution Overview

The system will process customer messages in three major stages:

1. Classifier Agent
   - Reads an incoming unstructured customer message.
   - Classifies it as one of:
     - Positive Feedback
     - Negative Feedback
     - Query
   - Routes the message to the relevant downstream agent.

2. Feedback Handler Agent
   - For positive feedback: generates a warm, personalized thank-you response.
   - For negative feedback: creates a new support ticket and returns a polite response with the ticket number.

3. Query Handler Agent
   - Extracts a ticket number from the user message.
   - Checks the banking support database.
   - Returns the current ticket status to the customer.

A Streamlit dashboard will expose this workflow for simulation, monitoring, and debugging.

## 2. Core Design Principles

- Keep each agent focused on a single responsibility.
- Use a lightweight orchestration layer to route tasks.
- Store ticket data in a structured support database.
- Keep logs and traces for debugging and evaluation.
- Add a UI layer for agent testing and monitoring.
- Track quality with evaluation prompts and test scenarios.

## 3. Recommended Folder Structure

```text
capstone-bank-customer-support/
├── app/
│   ├── ui/
│   ├── pages/
│   └── .gitkeep
├── agents/
│   ├── orchestrator/
│   ├── classifier/
│   ├── feedback_handler/
│   ├── query_handler/
│   └── .gitkeep
├── domain/
│   ├── models/
│   ├── schemas/
│   └── .gitkeep
├── integrations/
│   ├── database/
│   ├── llm/
│   └── .gitkeep
├── data/
│   ├── raw/
│   ├── processed/
│   └── .gitkeep
├── evaluation/
│   ├── prompts/
│   ├── test_cases/
│   ├── reports/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── config/
│   └── .gitkeep
├── docs/
│   └── .gitkeep
├── tests/
│   ├── agent_scenarios/
│   ├── ui_scenarios/
│   └── .gitkeep
└── README.md (optional project overview)
```

## 4. Folder Responsibilities

### app/
- Houses the Streamlit user interface and dashboard views.
- Includes pages for chat simulation, ticket lookup, logs, and evaluation views.

### agents/
- Contains the individual LLM-based operational agents.
- orchestrator/: coordinates the workflow and selects the correct agent.
- classifier/: classifies messages into feedback/query categories.
- feedback_handler/: handles positive and negative feedback logic.
- query_handler/: resolves ticket status requests.

### domain/
- Defines shared business entities, such as customer messages, tickets, feedback types, and status fields.
- Keeps the model layer separate from logic and UI.

### integrations/
- database/: stores the support ticket table and retrieval logic.
- llm/: keeps model connection code, prompt templates, and response-generation utilities.

### data/
- raw/: initial customer messages, historical tickets, and evaluation data.
- processed/: cleaned or transformed records used for testing and QA.

### evaluation/
- prompts/: prompt templates for LLM evaluation.
- test_cases/: scenarios for feedback classification, ticket creation, and status lookup.
- reports/: results from model accuracy, routing success, and QA reviews.

### logs/
- Stores prompt traces, agent actions, ticket IDs, and debugging records.

### config/
- Environment settings, model parameters, and app configuration.

### tests/
- Agent-level validation scenarios.
- UI test coverage for dashboards, message simulation, and log views.

### docs/
- Planning, architecture notes, and requirements documentation.

## 5. High-Level Execution Flow

1. User enters a support message in Streamlit.
2. Streamlit sends the message to the orchestration layer.
3. Classifier Agent decides if the input is positive feedback, negative feedback, or a query.
4. The orchestrator routes the message to the relevant agent.
5. The selected agent performs the action.
   - Positive feedback: generates a thank-you message.
   - Negative feedback: creates a support ticket and sends a polite acknowledgment.
   - Query: fetches ticket status from the support database.
6. Results are displayed on the Streamlit dashboard.
7. Logs, traces, and evaluation scores are recorded for monitoring and improvement.

## 6. LLMOps and Monitoring

The project should include:

- Prompt evaluation and QA-based scoring
- Classification routing accuracy checks
- Ticket creation and status lookup validation
- Log capture for prompts, outputs, and agent decisions
- Feedback loop for historical improvement and tuning

## 7. Implementation Direction

This plan is intentionally high-level and does not include code. The next step would be to build the actual Python modules, connect Streamlit, set up the support ticket database, and then implement each agent and evaluation pipeline.
