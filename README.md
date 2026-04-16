# Clinical Shift Handover Intelligence Agent

A production-ready AI orchestration system for automating clinical patient handovers.

## Project Structure

- **[backend/](file:///c:/Users/Adhithi%20C%20Iyer/Desktop/philips_/clinical-handover/backend/)**: FastAPI & LangGraph orchestration logic.
- **[frontend/](file:///c:/Users/Adhithi%20C%20Iyer/Desktop/philips_/clinical-handover/frontend/)**: React & React Flow dashboard.
- **[demo_data/](file:///c:/Users/Adhithi%20C%20Iyer/Desktop/philips_/clinical-handover/demo_data/)**: Synthetic patient records for testing.

## Getting Started

1.  **Ollama**: Ensure Ollama is running with Llama 3.2 installed.
2.  **Backend**: 
    ```bash
    cd backend
    pip install -r requirements.txt
    python main.py
    ```
3.  **Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## Technology Stack
- **AI**: Ollama (Llama 3.2), LangGraph.
- **Backend**: Python, FastAPI, WebSockets.
- **Frontend**: React 18, Vite, React Flow (Glassmorphism UI).
