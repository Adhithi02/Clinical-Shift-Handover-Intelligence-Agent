"""
FastAPI Backend — Main application entry point.
Provides REST endpoints, WebSocket streaming, and manages A2A agent lifecycle.
"""
import os
import sys
import json
import asyncio
import logging
import shutil
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_workflow, run_replan, set_ws_broadcast
from utils.llm import check_ollama, is_simulation_mode

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)


# --- WebSocket Connection Manager ---

class ConnectionManager:
    """Manages WebSocket connections for real-time streaming."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.message_history: list[dict] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active: {len(self.active_connections)}")
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        # Store in history
        try:
            msg_data = json.loads(message)
            self.message_history.append(msg_data)
            # Keep last 500 messages
            if len(self.message_history) > 500:
                self.message_history = self.message_history[-500:]
        except json.JSONDecodeError:
            pass
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# --- Application State ---

# In-memory storage for patient results
app_state = {
    "patients": {},           # patient_id -> patient data
    "sbar_results": {},       # patient_id -> SBAR result
    "risk_results": {},       # patient_id -> risk result
    "missing_results": {},    # patient_id -> missing result
    "task_graph": [],         # current task graph
    "patients_data": [],      # raw patient data
    "workflow_status": "idle", # idle, running, complete
    "uploaded_files": [],     # list of uploaded file paths
}


# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("=" * 60)
    logger.info("Clinical Shift Handover Intelligence Agent")
    logger.info("=" * 60)
    
    # Check Ollama availability
    ollama_available = check_ollama()
    if ollama_available:
        logger.info("Mode: LLM (Ollama + Llama 3.2)")
    else:
        logger.info("Mode: SIMULATION (rule-based, no LLM)")
        logger.info("  → Install Ollama and run 'ollama pull llama3.2' for LLM mode")
    
    # Create patients directory
    os.makedirs("patients", exist_ok=True)
    
    # Set WebSocket broadcast function
    set_ws_broadcast(manager.broadcast)
    
    # Check for demo data
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_data")
    if os.path.exists(demo_dir):
        demo_pdfs = [f for f in os.listdir(demo_dir) if f.endswith('.pdf')]
        logger.info(f"Demo data available: {len(demo_pdfs)} PDFs in {demo_dir}")
    
    logger.info("Server ready at http://localhost:8000")
    logger.info("=" * 60)
    
    yield
    
    logger.info("Shutting down...")


# --- FastAPI App ---

app = FastAPI(
    title="Clinical Shift Handover Intelligence Agent",
    description="Multi-agent AI system for patient handover using SBAR format",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REST Endpoints ---

@app.get("/")
async def root():
    """Health check and system status."""
    return {
        "system": "Clinical Shift Handover Intelligence Agent",
        "status": app_state["workflow_status"],
        "mode": "simulation" if is_simulation_mode() else "llm",
        "patients_loaded": len(app_state["patients"]),
        "sbar_briefs": len(app_state["sbar_results"]),
        "websocket": "ws://localhost:8000/ws"
    }


@app.post("/upload")
async def upload_pdfs(files: list[UploadFile] = File(...)):
    """
    Upload patient PDF reports and trigger the handover workflow.
    Accepts multiple PDF files simultaneously.
    """
    if app_state["workflow_status"] == "running":
        raise HTTPException(status_code=409, detail="Workflow already running")
    
    app_state["workflow_status"] = "running"
    saved_paths = []
    
    try:
        # Save uploaded files
        for file in files:
            if not file.filename.endswith('.pdf'):
                continue
            
            file_path = os.path.join("patients", file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            saved_paths.append(os.path.abspath(file_path))
            logger.info(f"Saved: {file_path}")
        
        if not saved_paths:
            app_state["workflow_status"] = "idle"
            raise HTTPException(status_code=400, detail="No valid PDF files uploaded")
        
        app_state["uploaded_files"] = saved_paths
        
        # Run workflow asynchronously
        asyncio.create_task(_run_workflow_async(saved_paths))
        
        return {
            "message": f"Uploaded {len(saved_paths)} PDF(s). Workflow started.",
            "files": [os.path.basename(p) for p in saved_paths],
            "status": "running"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_state["workflow_status"] = "error"
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-demo")
async def upload_demo():
    """
    Load demo patient PDFs from the demo_data directory.
    Quick start for demonstration purposes.
    """
    if app_state["workflow_status"] == "running":
        raise HTTPException(status_code=409, detail="Workflow already running")
    
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_data")
    
    if not os.path.exists(demo_dir):
        raise HTTPException(status_code=404, detail="Demo data directory not found. Run generate_demo_pdfs.py first.")
    
    demo_files = sorted([
        os.path.join(demo_dir, f) for f in os.listdir(demo_dir) 
        if f.endswith('.pdf')
    ])
    
    if not demo_files:
        raise HTTPException(status_code=404, detail="No demo PDFs found. Run generate_demo_pdfs.py first.")
    
    # Copy to patients directory
    os.makedirs("patients", exist_ok=True)
    saved_paths = []
    for src in demo_files:
        dst = os.path.join("patients", os.path.basename(src))
        shutil.copy2(src, dst)
        saved_paths.append(os.path.abspath(dst))
    
    app_state["workflow_status"] = "running"
    app_state["uploaded_files"] = saved_paths
    
    # Run workflow
    asyncio.create_task(_run_workflow_async(saved_paths))
    
    return {
        "message": f"Loaded {len(saved_paths)} demo patient PDFs. Workflow started.",
        "files": [os.path.basename(p) for p in saved_paths],
        "status": "running"
    }


async def _run_workflow_async(file_paths: list[str]):
    """Run the clinical handover workflow asynchronously."""
    try:
        result = await run_workflow(file_paths, manager.broadcast)
        
        # Extract results from the last step
        if result:
            app_state["sbar_results"] = result.get("sbar_results", {})
            app_state["risk_results"] = result.get("risk_results", {})
            app_state["missing_results"] = result.get("missing_results", {})
            app_state["task_graph"] = result.get("task_graph", [])
            app_state["patients_data"] = result.get("patients_data", [])
            
            # Build patients lookup
            for p in app_state["patients_data"]:
                pid = p.get("patient_id", "")
                if pid:
                    # Remove raw_text for API response
                    patient_copy = {k: v for k, v in p.items() if k != "raw_text"}
                    app_state["patients"][pid] = patient_copy
        
        app_state["workflow_status"] = "complete"
        logger.info("Workflow completed successfully")
        
    except Exception as e:
        app_state["workflow_status"] = "error"
        logger.error(f"Workflow error: {e}", exc_info=True)
        await manager.broadcast(json.dumps({
            "type": "workflow_status",
            "agent": "orchestrator",
            "patient": "all",
            "status": "error",
            "message": f"Workflow error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }))


@app.post("/feedback")
async def doctor_feedback(feedback: dict):
    """
    Receive doctor's correction and trigger workflow replan.
    
    Expected body:
    {
        "patient_id": "PAT-B-2024-0892",
        "instruction": "Patient has naturally low BP, reconsider risk level"
    }
    """
    patient_id = feedback.get("patient_id", "")
    instruction = feedback.get("instruction", "")
    
    if not patient_id or not instruction:
        raise HTTPException(status_code=400, detail="patient_id and instruction are required")
    
    if patient_id not in app_state.get("sbar_results", {}):
        raise HTTPException(status_code=404, detail=f"No results found for patient {patient_id}")
    
    app_state["workflow_status"] = "replanning"
    
    try:
        # Build current state for replan
        current_state = {
            "patients_data": app_state.get("patients_data", []),
            "risk_results": app_state.get("risk_results", {}),
            "missing_results": app_state.get("missing_results", {}),
            "sbar_results": app_state.get("sbar_results", {}),
        }
        
        result = await run_replan(
            current_state, patient_id, instruction, manager.broadcast
        )
        
        # Update state
        if result:
            app_state["sbar_results"].update(result.get("sbar_results", {}))
            app_state["risk_results"].update(result.get("risk_results", {}))
            app_state["missing_results"].update(result.get("missing_results", {}))
        
        app_state["workflow_status"] = "complete"
        
        return {
            "message": "Replan complete",
            "patient_id": patient_id,
            "new_sbar": app_state["sbar_results"].get(patient_id, {}),
            "status": "complete"
        }
        
    except Exception as e:
        app_state["workflow_status"] = "error"
        logger.error(f"Replan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patients")
async def list_patients():
    """List all processed patients with their current status."""
    patients_summary = []
    
    for pid, patient in app_state.get("patients", {}).items():
        sbar = app_state.get("sbar_results", {}).get(pid, {})
        patients_summary.append({
            "patient_id": pid,
            "name": patient.get("name", "Unknown"),
            "age": patient.get("age", ""),
            "admission_reason": patient.get("admission_reason", ""),
            "color": sbar.get("color", "GREY"),
            "severity": sbar.get("severity", ""),
            "has_sbar": bool(sbar)
        })
    
    return {
        "patients": patients_summary,
        "total": len(patients_summary),
        "workflow_status": app_state["workflow_status"]
    }


@app.get("/sbar/{patient_id}")
async def get_sbar(patient_id: str):
    """Get SBAR brief for a specific patient."""
    sbar = app_state.get("sbar_results", {}).get(patient_id)
    
    if not sbar:
        raise HTTPException(status_code=404, detail=f"No SBAR brief found for {patient_id}")
    
    return sbar


@app.get("/results")
async def get_all_results():
    """Get all results including SBAR briefs, risk assessments, and task graph."""
    return {
        "workflow_status": app_state["workflow_status"],
        "mode": "simulation" if is_simulation_mode() else "llm",
        "task_graph": app_state.get("task_graph", []),
        "sbar_results": app_state.get("sbar_results", {}),
        "risk_results": app_state.get("risk_results", {}),
        "missing_results": app_state.get("missing_results", {}),
        "patients": app_state.get("patients", {})
    }


@app.get("/messages")
async def get_messages():
    """Get WebSocket message history."""
    return {
        "messages": manager.message_history[-100:],
        "total": len(manager.message_history)
    }


# --- WebSocket Endpoint ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent status streaming."""
    await manager.connect(websocket)
    
    # Send current state on connect
    await websocket.send_text(json.dumps({
        "type": "connection",
        "status": "connected",
        "workflow_status": app_state["workflow_status"],
        "mode": "simulation" if is_simulation_mode() else "llm",
        "timestamp": datetime.now().isoformat()
    }))
    
    # Send recent message history
    for msg in manager.message_history[-20:]:
        try:
            await websocket.send_text(json.dumps(msg))
        except Exception:
            break
    
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            # Client can send ping or other commands
            if data == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# --- Main ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
