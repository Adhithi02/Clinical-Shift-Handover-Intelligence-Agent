# Backend - Clinical Handover AI Orchestrator

This is the core intelligence engine of the system, powered by **LangGraph** and **Llama 3.2**.

## Technical Architecture

The backend consists of four main agentic nodes coordinated via a StateGraph:

1.  **Planner Agent**: Analyzes clinical input and routes patients to specialized agents.
2.  **Risk Flag Agent**: Performs deep-dive vital trend analysis and pharmacological checks.
3.  **Missing Info Agent**: Identifies document gaps and incomplete clinical data.
4.  **Synthesis Agent**: Merges all findings into a concise, professional SBAR brief.

### Key Features
- **Parallel Execution**: Uses LangGraph's branching logic to run Risk and Missing checks simultaneously.
- **Doctor-in-the-Loop**: Includes a feedback mechanism for real-time assessment adjustment.
- **WebSocket Streaming**: Real-time status updates broadcast to the React dashboard.

## Setup & Running

Requires **Python 3.10+** and **Ollama**.

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn main:app --reload --port 8000
```

## API Endpoints
- `POST /upload`: Process clinical PDFs.
- `POST /feedback`: Submit doctor corrections and trigger replanning.
- `WS /ws/clinical`: Real-time state synchronization.
