# Bank Customer Support

A Streamlit banking-support assistant using LangGraph, OpenAI, and SQLite. The classifier routes each message to a positive/negative feedback handler or a ticket-status query handler.

## Run locally

1. Create and activate a Python 3.10+ environment.
2. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. The default model is `gpt-4o-mini`.
4. Launch the dashboard from the project root:

   ```powershell
   streamlit run app/ui/streamlit_app.py
   ```

The SQLite database and JSON Lines workflow log are created automatically under `data/` and `logs/`. Override their paths with `SUPPORT_DB_PATH` and `AGENT_LOG_PATH`. Additional operational settings are `SUPPORT_DB_TIMEOUT_SECONDS` (default `10`), `SUPPORT_TICKET_LIST_LIMIT` (default `500`), and `SUPPORT_TICKET_ID_GENERATION_ATTEMPTS` (default `20`). Numeric settings must be positive; the database timeout must also be finite.

## Tests

The agent workflow tests use a deterministic fake language model and a temporary SQLite database, so they do not require an OpenAI key:

```powershell
python -m unittest discover -s tests -v
```

## Ticket statuses

Tickets are created with status `New`. Supported statuses are `New`, `In Progress`, and `Resolved`.
