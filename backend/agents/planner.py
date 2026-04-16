"""
Planner Agent — A2A Server (Port 5001)
Reads patient PDFs, analyzes severity using LLM, and dynamically routes 
each patient to appropriate agents (Risk, Missing Info, or directly to Synthesis).
"""
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState

logger = logging.getLogger(__name__)


@agent(
    name="PlannerAgent",
    description="Reads patient clinical reports, analyzes severity, and dynamically routes each patient to appropriate specialist agents based on clinical findings.",
    version="1.0.0"
)
class PlannerAgent(A2AServer):
    """
    The Planner Agent is the entry point of the clinical handover workflow.
    It reads all uploaded PDFs, extracts patient data, reasons about severity,
    and creates a dynamic task graph routing each patient differently.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.port = 5001
    
    @skill(
        name="plan_workflow",
        description="Analyze patient PDFs and create a dynamic routing plan for each patient",
        tags=["planning", "triage", "routing"]
    )
    def handle_task(self, task):
        """Process incoming planning task."""
        try:
            # Extract the message content
            if hasattr(task, 'message') and task.message:
                if hasattr(task.message, 'content'):
                    content = task.message.content
                else:
                    content = str(task.message)
            else:
                content = str(task)
            
            # Try to parse as JSON
            try:
                request_data = json.loads(content) if isinstance(content, str) else content
            except (json.JSONDecodeError, TypeError):
                request_data = {"file_paths": [], "raw": content}
            
            file_paths = request_data.get('file_paths', [])
            patients_data = request_data.get('patients_data', [])
            
            # Extract patient data from PDFs if file paths provided
            if file_paths and not patients_data:
                from tools.mcp_server import extract_pdf_text
                patients_data = []
                for fp in file_paths:
                    try:
                        patient = extract_pdf_text(fp)
                        patients_data.append(patient)
                    except Exception as e:
                        logger.error(f"Error extracting {fp}: {e}")
            
            # Plan routing for each patient
            task_graph = self._plan_routing(patients_data)
            
            return json.dumps(task_graph)
            
        except Exception as e:
            logger.error(f"Planner error: {e}")
            return json.dumps({"error": str(e), "task_graph": []})
    
    def _plan_routing(self, patients_data: list) -> dict:
        """
        Analyze each patient and decide routing.
        Uses LLM when available, falls back to rule-based logic.
        """
        from utils.llm import call_llm, is_simulation_mode
        
        task_graph = []
        
        for patient in patients_data:
            if not patient or patient.get('error'):
                continue
            
            patient_id = patient.get('patient_id', 'UNKNOWN')
            name = patient.get('name', 'Unknown')
            
            if not is_simulation_mode():
                # Use LLM for routing decision
                routing = self._llm_route(patient)
            else:
                # Rule-based routing
                routing = self._rule_based_route(patient)
            
            task_graph.append({
                "patient_id": patient_id,
                "name": name,
                "route": routing["route"],
                "reason": routing["reason"],
                "priority": routing["priority"],
                "agents_to_invoke": routing["agents_to_invoke"]
            })
            
            logger.info(f"Routed {name} ({patient_id}) → {routing['route']} (priority: {routing['priority']})")
        
        return {"task_graph": task_graph, "patients_data": patients_data}
    
    def _llm_route(self, patient: dict) -> dict:
        """Use LLM to decide routing for a patient."""
        from utils.llm import call_llm
        
        # Create a summary of patient data for LLM
        patient_summary = {
            "name": patient.get("name"),
            "age": patient.get("age"),
            "admission_reason": patient.get("admission_reason"),
            "vitals_count": len(patient.get("vitals", [])),
            "vitals": patient.get("vitals", []),
            "medications": [m.get("name", "") for m in patient.get("medications", [])],
            "pain_score": patient.get("pain_score"),
            "procedures": patient.get("procedures", []),
            "missing_flags": patient.get("missing_flags", []),
            "investigations": patient.get("investigations", [])
        }
        
        system_prompt = """You are a clinical triage planner. Analyze this patient and decide the routing.

Routes available:
- "risk": Patient has declining vitals, concerning trends, or critical flags. 
- "missing": Patient has missing clinical data (labs, docs).
- "synthesis": Final state. Mandatory for all routes.

RULES: 
1. If patient has "chest pain", "ACS", or "cardiac" symptoms AND any vital drop, ALWAYS include "risk" in agents_to_invoke.
2. If any data is marked "NOT DOCUMENTED", ALWAYS include "missing" in agents_to_invoke.

Return JSON:
{
    "route": "risk|missing|synthesis", 
    "reason": "brief explanation",
    "priority": "HIGH|MEDIUM|LOW",
    "agents_to_invoke": ["risk", "missing", "synthesis"] // USE THESE EXACT TOKENS ONLY
}"""
        
        result = call_llm(system_prompt, json.dumps(patient_summary))
        
        # Validate and ensure required fields
        if not result.get("route"):
            result["route"] = "synthesis"
        if not result.get("agents_to_invoke"):
            result["agents_to_invoke"] = [result["route"], "synthesis"] if result["route"] != "synthesis" else ["synthesis"]
        if not result.get("priority"):
            result["priority"] = "MEDIUM"
        if not result.get("reason"):
            result["reason"] = "LLM routing decision"
        
        return result
    
    def _rule_based_route(self, patient: dict) -> dict:
        """Rule-based routing fallback when LLM is unavailable."""
        vitals = patient.get("vitals", [])
        missing_flags = patient.get("missing_flags", [])
        pain = patient.get("pain_score", {})
        admission = patient.get("admission_reason", "").lower()
        
        has_risk = False
        has_missing = False
        risk_reasons = []
        missing_reasons = []
        priority = "LOW"
        
        # Check for vital sign trends
        if len(vitals) >= 3:
            from tools.mcp_server import detect_vital_trend
            trend = detect_vital_trend(vitals)
            if trend.get("overall_severity") in ("HIGH", "MEDIUM"):
                has_risk = True
                risk_reasons.extend(trend.get("alerts", ["Vital sign trend concern"]))
                if trend.get("overall_severity") == "HIGH":
                    priority = "HIGH"
                else:
                    priority = "MEDIUM"
        
        # Check for cardiac patient indicators
        if any(kw in admission for kw in ['chest pain', 'acs', 'cardiac', 'heart']):
            investigations = patient.get('investigations', [])
            inv_text = ' '.join(str(i) for i in investigations).lower()
            if 'not documented' in inv_text or 'troponin' in ' '.join(missing_flags).lower():
                has_risk = True
                has_missing = True
                risk_reasons.append("Cardiac patient with incomplete workup")
                missing_reasons.append("Missing cardiac investigation results")
                priority = "HIGH"
        
        # Check for missing data
        if missing_flags:
            has_missing = True
            missing_reasons.extend(missing_flags)
            if priority == "LOW":
                priority = "MEDIUM"
        
        if isinstance(pain, dict) and pain.get("missing_post_op"):
            has_missing = True
            missing_reasons.append("Post-operative pain assessment missing")
            if priority == "LOW":
                priority = "MEDIUM"
        
        # Determine route and agents
        if has_risk and has_missing:
            route = "risk"  # Primary route
            agents = ["risk", "missing", "synthesis"]
            reason = "; ".join(risk_reasons + missing_reasons)
        elif has_risk:
            route = "risk"
            agents = ["risk", "synthesis"]
            reason = "; ".join(risk_reasons)
        elif has_missing:
            route = "missing"
            agents = ["missing", "synthesis"]
            reason = "; ".join(missing_reasons)
        else:
            route = "synthesis"
            agents = ["synthesis"]
            reason = "Patient stable with complete clinical data"
        
        return {
            "route": route,
            "reason": reason,
            "priority": priority,
            "agents_to_invoke": agents
        }


def run_planner_server(port: int = 5001):
    """Run the Planner Agent as an A2A server."""
    planner = PlannerAgent()
    logger.info(f"Starting Planner Agent on port {port}")
    planner.start(port=port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_planner_server()
