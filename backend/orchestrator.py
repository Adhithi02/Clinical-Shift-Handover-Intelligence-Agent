"""
LangGraph Orchestrator — Dynamic workflow graph for clinical handover.
Uses StateGraph with conditional routing based on Planner Agent's decisions.
Each node calls the corresponding A2A agent and broadcasts WebSocket updates.
"""
import json
import asyncio
import logging
from typing import TypedDict, Annotated, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


# --- State Definition ---

class ClinicalState(TypedDict):
    """State schema for the clinical handover workflow."""
    # Input
    file_paths: list[str]
    patients_data: list[dict]
    
    # Planner output
    task_graph: list[dict]
    
    # Per-patient results
    risk_results: dict[str, dict]      # patient_id -> risk assessment
    missing_results: dict[str, dict]   # patient_id -> missing info
    sbar_results: dict[str, dict]      # patient_id -> SBAR brief
    
    # Workflow state
    current_patient: str
    current_agent: str
    status: str
    messages: list[dict]
    
    # Replan
    feedback: Optional[dict]


# --- WebSocket broadcaster (set by main.py) ---
_ws_broadcast = None
_main_loop = None


def set_ws_broadcast(broadcast_fn):
    """Set the WebSocket broadcast function from main.py."""
    global _ws_broadcast
    _ws_broadcast = broadcast_fn


async def _broadcast(message: dict):
    """Broadcast a message via WebSocket if available."""
    global _ws_broadcast
    if "timestamp" not in message:
        message["timestamp"] = datetime.now().isoformat()
    if _ws_broadcast:
        try:
            await _ws_broadcast(json.dumps(message))
        except Exception as e:
            logger.warning(f"WebSocket broadcast failed: {e}")
    logger.info(f"[{message.get('agent', '?')}] {message.get('patient', '?')}: {message.get('status', '?')} - {message.get('message', '')}")


def _broadcast_sync(message: dict):
    """Synchronous wrapper for broadcast."""
    global _main_loop
    if "timestamp" not in message:
        message["timestamp"] = datetime.now().isoformat()
    
    if _main_loop and not _main_loop.is_closed():
        asyncio.run_coroutine_threadsafe(_broadcast(message), _main_loop)
    else:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(_broadcast(message))
            else:
                loop.run_until_complete(_broadcast(message))
        except RuntimeError:
            logger.info(f"[{message.get('agent', '?')}] {message.get('status', '?')}: {message.get('message', '')}")


# --- Graph Nodes ---

def plan_node(state: ClinicalState) -> dict:
    """
    Planner node: Extract data from PDFs and create routing plan.
    Calls the Planner Agent to analyze all patients.
    """
    from agents.planner import PlannerAgent
    
    _broadcast_sync({
        "type": "agent_status",
        "agent": "planner",
        "patient": "all",
        "status": "running",
        "message": "Analyzing uploaded patient reports..."
    })
    
    planner = PlannerAgent()
    
    file_paths = state.get("file_paths", [])
    
    # Prepare request
    import json as json_mod
    
    # Call planner's internal method directly (in-process)
    from tools.mcp_server import extract_pdf_text
    
    patients_data = []
    for fp in file_paths:
        _broadcast_sync({
            "type": "agent_status",
            "agent": "planner",
            "patient": "all",
            "status": "running",
            "message": f"Extracting data from {fp.split('/')[-1].split(chr(92))[-1]}..."
        })
        try:
            patient = extract_pdf_text(fp)
            patients_data.append(patient)
        except Exception as e:
            logger.error(f"Error extracting {fp}: {e}")
    
    # Route patients
    plan_result = planner._plan_routing(patients_data)
    task_graph = plan_result.get("task_graph", [])
    
    for entry in task_graph:
        _broadcast_sync({
            "type": "agent_status",
            "agent": "planner",
            "patient": entry.get("patient_id", ""),
            "status": "complete",
            "message": f"Routed {entry.get('name', 'Unknown')} → {entry.get('route', 'unknown')} ({entry.get('reason', '')})",
            "result": {
                "route": entry.get("route"),
                "priority": entry.get("priority"),
                "agents_to_invoke": entry.get("agents_to_invoke", [])
            }
        })
    
    return {
        "patients_data": patients_data,
        "task_graph": task_graph,
        "status": "planned",
        "risk_results": {},
        "missing_results": {},
        "sbar_results": {},
        "messages": []
    }


def risk_node(state: ClinicalState) -> dict:
    """
    Risk assessment node: Process patients routed to Risk Flag Agent.
    """
    from agents.risk_agent import RiskFlagAgent
    
    task_graph = state.get("task_graph", [])
    patients_data = state.get("patients_data", [])
    risk_results = dict(state.get("risk_results", {}))
    
    risk_agent = RiskFlagAgent()
    
    # Find patients that need risk assessment (case-insensitive)
    risk_patients = [t for t in task_graph if any("risk" in agent.lower() for agent in t.get("agents_to_invoke", []))]
    
    for task_entry in risk_patients:
        patient_id = task_entry.get("patient_id", "")
        name = task_entry.get("name", "Unknown")
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "risk",
            "patient": patient_id,
            "status": "running",
            "message": f"Analyzing risk flags for {name}..."
        })
        
        # Find patient data
        patient = next((p for p in patients_data if p.get("patient_id") == patient_id), {})
        
        # Call risk agent directly (in-process)
        result = risk_agent._assess_risk(patient)
        risk_results[patient_id] = result
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "risk",
            "patient": patient_id,
            "patient_name": name,
            "status": "complete",
            "message": f"Risk assessment complete: {result.get('severity', 'N/A')} severity",
            "result": {
                "severity": result.get("severity"),
                "color": "RED" if result.get("severity") == "HIGH" else ("AMBER" if result.get("severity") == "MEDIUM" else "GREEN"),
                "flags": result.get("flags", []),
                "recommendation": result.get("recommendation", "")
            }
        })
    
    return {"risk_results": risk_results}


def missing_node(state: ClinicalState) -> dict:
    """
    Missing info node: Process patients routed to Missing Info Agent.
    """
    from agents.missing_agent import MissingInfoAgent
    
    task_graph = state.get("task_graph", [])
    patients_data = state.get("patients_data", [])
    missing_results = dict(state.get("missing_results", {}))
    
    missing_agent = MissingInfoAgent()
    
    # Find patients that need missing info check (case-insensitive)
    missing_patients = [t for t in task_graph if any("missing" in agent.lower() for agent in t.get("agents_to_invoke", []))]
    
    for task_entry in missing_patients:
        patient_id = task_entry.get("patient_id", "")
        name = task_entry.get("name", "Unknown")
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "missing",
            "patient": patient_id,
            "status": "running",
            "message": f"Checking for missing clinical data for {name}..."
        })
        
        patient = next((p for p in patients_data if p.get("patient_id") == patient_id), {})
        
        # Call missing agent directly
        result = missing_agent._check_missing(patient)
        missing_results[patient_id] = result
        
        missing_count = result.get("total_missing", 0)
        high_count = result.get("high_significance_count", 0)
        _broadcast_sync({
            "type": "agent_status",
            "agent": "missing",
            "patient": patient_id,
            "patient_name": name,
            "status": "complete",
            "message": f"Found {missing_count} missing items ({high_count} high significance)",
            "result": {
                "total_missing": missing_count,
                "high_significance_count": high_count,
                "color": "AMBER" if high_count > 0 else "GREEN",
                "missing_fields": result.get("missing_fields", [])
            }
        })
    
    return {"missing_results": missing_results}


def synthesis_node(state: ClinicalState) -> dict:
    """
    Synthesis node: Generate SBAR briefs for ALL patients.
    """
    from agents.synthesis import SynthesisAgent
    
    task_graph = state.get("task_graph", [])
    patients_data = state.get("patients_data", [])
    risk_results = state.get("risk_results", {})
    missing_results = state.get("missing_results", {})
    sbar_results = dict(state.get("sbar_results", {}))
    
    synth_agent = SynthesisAgent()
    
    for task_entry in task_graph:
        patient_id = task_entry.get("patient_id", "")
        name = task_entry.get("name", "Unknown")
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "synthesis",
            "patient": patient_id,
            "status": "running",
            "message": f"Generating SBAR handover brief for {name}..."
        })
        
        patient = next((p for p in patients_data if p.get("patient_id") == patient_id), {})
        risk = risk_results.get(patient_id, {})
        missing = missing_results.get(patient_id, {})
        
        # Call synthesis agent directly
        result = synth_agent._synthesize({
            "patient": patient,
            "risk": risk,
            "missing": missing
        })
        
        sbar_results[patient_id] = result
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "synthesis",
            "patient": patient_id,
            "patient_name": name,
            "status": "complete",
            "message": f"SBAR brief complete — {result.get('color', 'GREEN')} status",
            "result": {
                "color": result.get("color", "GREEN"),
                "severity": result.get("severity", "LOW"),
                "patient_name": name,
                "sbar": result.get("sbar", {})
            }
        })
    
    return {
        "sbar_results": sbar_results,
        "status": "complete"
    }


# --- Routing Logic ---

def route_after_plan(state: ClinicalState) -> list[str]:
    """
    Determine which nodes to execute after planning.
    Returns list of next nodes based on patient routing.
    """
    task_graph = state.get("task_graph", [])
    
    needs_risk = any(any("risk" in agent.lower() for agent in t.get("agents_to_invoke", [])) for t in task_graph)
    needs_missing = any(any("missing" in agent.lower() for agent in t.get("agents_to_invoke", [])) for t in task_graph)
    
    next_nodes = []
    if needs_risk:
        next_nodes.append("assess_risk")
    if needs_missing:
        next_nodes.append("check_missing")
    
    # If no specialized agents needed, go directly to synthesis
    if not next_nodes:
        next_nodes.append("synthesize")
    
    return next_nodes


# --- Build Graph ---

def build_clinical_graph() -> StateGraph:
    """
    Build the LangGraph StateGraph for clinical handover workflow.
    
    Flow:
    plan → (conditional) → assess_risk → synthesize
                          → check_missing → synthesize
                          → (direct) → synthesize
    """
    graph = StateGraph(ClinicalState)
    
    # Add nodes
    graph.add_node("plan", plan_node)
    graph.add_node("assess_risk", risk_node)
    graph.add_node("check_missing", missing_node)
    graph.add_node("synthesize", synthesis_node)
    
    # Set entry point
    graph.set_entry_point("plan")
    
    # Add conditional edges from plan allowing dynamic list routing
    graph.add_conditional_edges(
        "plan",
        route_after_plan
    )
    
    # After risk/missing, go to synthesis
    graph.add_edge("assess_risk", "synthesize")
    graph.add_edge("check_missing", "synthesize")
    
    # Synthesis is the end
    graph.add_edge("synthesize", END)
    
    return graph


def compile_graph():
    """Compile the clinical graph for execution."""
    graph = build_clinical_graph()
    return graph.compile()


# --- Execution ---

async def run_workflow(file_paths: list[str], broadcast_fn=None) -> dict:
    """
    Execute the clinical handover workflow for uploaded PDFs.
    
    Args:
        file_paths: List of PDF file paths to process
        broadcast_fn: WebSocket broadcast function
    
    Returns:
        Final state with all results
    """
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    
    if broadcast_fn:
        set_ws_broadcast(broadcast_fn)
    
    app = compile_graph()
    
    initial_state = {
        "file_paths": file_paths,
        "patients_data": [],
        "task_graph": [],
        "risk_results": {},
        "missing_results": {},
        "sbar_results": {},
        "current_patient": "",
        "current_agent": "",
        "status": "starting",
        "messages": [],
        "feedback": None
    }
    
    _broadcast_sync({
        "type": "workflow_status",
        "agent": "orchestrator",
        "patient": "all",
        "status": "starting",
        "message": f"Starting clinical handover workflow with {len(file_paths)} patient reports"
    })
    
    # Run the graph
    full_state = dict(initial_state)
    async for step in app.astream(initial_state):
        if isinstance(step, dict):
            for node_name, node_output in step.items():
                if isinstance(node_output, dict):
                    full_state.update(node_output)
        logger.info(f"Graph step completed: {list(step.keys())}")
    
    _broadcast_sync({
        "type": "workflow_status",
        "agent": "orchestrator",
        "patient": "all",
        "status": "complete",
        "message": "Clinical handover workflow complete"
    })
    
    return full_state


async def run_replan(current_state: dict, patient_id: str, 
                     instruction: str, broadcast_fn=None) -> dict:
    """
    Re-execute workflow for a specific patient based on doctor feedback.
    """
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    
    if broadcast_fn:
        set_ws_broadcast(broadcast_fn)
    
    from tools.mcp_server import replan_workflow
    
    _broadcast_sync({
        "type": "replan_status",
        "agent": "orchestrator",
        "patient": patient_id,
        "status": "replanning",
        "message": f"Doctor feedback received: {instruction}"
    })
    
    # Get current patient result
    patient_state = {
        "patient_id": patient_id,
        "severity": current_state.get("sbar_results", {}).get(patient_id, {}).get("severity", "MEDIUM"),
        "current_sbar": current_state.get("sbar_results", {}).get(patient_id, {})
    }
    
    # Replan via MCP tool (run in thread to prevent blocking WebSocket broadcasts)
    replan_result = await asyncio.to_thread(replan_workflow, patient_state, instruction)
    
    _broadcast_sync({
        "type": "replan_status",
        "agent": "orchestrator",
        "patient": patient_id,
        "status": "running",
        "message": f"Replanning: {replan_result.get('reason', 'Processing feedback...')}"
    })
    
    # Re-execute affected agents
    agents_to_rerun = replan_result.get("re_evaluate_agents", ["synthesis"])
    patients_data = current_state.get("patients_data", [])
    patient = next((p for p in patients_data if p.get("patient_id") == patient_id), {})
    
    risk_results = dict(current_state.get("risk_results", {}))
    missing_results = dict(current_state.get("missing_results", {}))
    sbar_results = dict(current_state.get("sbar_results", {}))
    
    # Adjust severity based on feedback
    adjusted_severity = replan_result.get("adjusted_severity", "MEDIUM")
    
    if "risk" in agents_to_rerun:
        from agents.risk_agent import RiskFlagAgent
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "risk",
            "patient": patient_id,
            "status": "running",
            "message": f"Re-evaluating risk with doctor feedback..."
        })
        
        risk_agent = RiskFlagAgent()
        risk_result = await asyncio.to_thread(risk_agent._assess_risk, patient)
        
        # Apply doctor's severity adjustment
        risk_result["severity"] = adjusted_severity
        risk_result["doctor_feedback"] = instruction
        risk_result["adjusted"] = True
        
        risk_results[patient_id] = risk_result
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "risk",
            "patient": patient_id,
            "status": "complete",
            "message": f"Risk re-assessed: {adjusted_severity} (adjusted per doctor feedback)",
            "result": {"severity": adjusted_severity, "flags": risk_result.get("flags", [])}
        })
    
    if "missing" in agents_to_rerun:
        from agents.missing_agent import MissingInfoAgent
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "missing",
            "patient": patient_id,
            "status": "running",
            "message": "Re-checking missing information..."
        })
        
        missing_agent = MissingInfoAgent()
        missing_result = await asyncio.to_thread(missing_agent._check_missing, patient)
        missing_results[patient_id] = missing_result
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "missing",
            "patient": patient_id,
            "status": "complete",
            "message": f"Missing info re-checked: {missing_result.get('total_missing', 0)} items"
        })
    
    if "synthesis" in agents_to_rerun:
        from agents.synthesis import SynthesisAgent
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "synthesis",
            "patient": patient_id,
            "status": "running",
            "message": "Regenerating SBAR brief..."
        })
        
        synth_agent = SynthesisAgent()
        
        # Update risk severity for synthesis
        risk_for_synth = risk_results.get(patient_id, {})
        risk_for_synth["severity"] = adjusted_severity
        
        sbar_result = await asyncio.to_thread(synth_agent._synthesize, {
            "patient": patient,
            "risk": risk_for_synth,
            "missing": missing_results.get(patient_id, {}),
            "feedback": instruction
        })
        
        # Apply adjusted color
        if adjusted_severity == "LOW":
            sbar_result["color"] = "GREEN"
            sbar_result["severity"] = "LOW"
        elif adjusted_severity == "MEDIUM":
            sbar_result["color"] = "AMBER"
            sbar_result["severity"] = "MEDIUM"
        else:
            sbar_result["color"] = "RED"
            sbar_result["severity"] = "HIGH"
        
        sbar_result["doctor_feedback"] = instruction
        sbar_result["replanned"] = True
        sbar_results[patient_id] = sbar_result
        
        _broadcast_sync({
            "type": "agent_status",
            "agent": "synthesis",
            "patient": patient_id,
            "patient_name": sbar_result.get("patient_name") or patient.get("name"),
            "status": "complete",
            "message": f"SBAR brief updated — now {sbar_result.get('color', 'GREEN')}",
            "result": {
                "color": sbar_result.get("color"),
                "severity": sbar_result.get("severity"),
                "patient_name": sbar_result.get("patient_name") or patient.get("name"),
                "sbar": sbar_result.get("sbar", {}),
                "replanned": True,
                "doctor_feedback": instruction
            }
        })
    
    _broadcast_sync({
        "type": "replan_status",
        "agent": "orchestrator",
        "patient": patient_id,
        "status": "complete",
        "message": f"Replan complete. Assessment adjusted to {adjusted_severity}."
    })
    
    return {
        "risk_results": risk_results,
        "missing_results": missing_results,
        "sbar_results": sbar_results
    }
