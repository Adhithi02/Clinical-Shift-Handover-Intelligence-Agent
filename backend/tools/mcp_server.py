"""
FastMCP server exposing clinical tools via the Model Context Protocol.
Tools: extract_pdf_text, detect_vital_trend, check_missing_fields, format_sbar, replan_workflow
"""
import json
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

try:
    from fastmcp import FastMCP
    mcp = FastMCP("ClinicalHandoverTools")
except Exception as e:
    logger.warning(f"FastMCP initialization failed ({e}). Proceeding without MCP server transport.")
    class DummyMCP:
        def tool(self):
            return lambda func: func
        def run(self, **kwargs):
            pass
    mcp = DummyMCP()

@mcp.tool()
def extract_pdf_text(file_path: str) -> dict:
    """
    Extract structured patient data from a clinical report PDF.
    Returns a dictionary with patient demographics, vitals, medications, 
    pain scores, procedures, investigations, and missing data flags.
    """
    from utils.pdf_parser import extract_patient_data
    result = extract_patient_data(file_path)
    # Remove raw_text to keep response size manageable
    result.pop('raw_text', None)
    return result


@mcp.tool()
def detect_vital_trend(vitals_list: list) -> dict:
    """
    Analyze sequential vital sign readings for trends.
    Detects declining, improving, or stable patterns in BP, HR, SpO2.
    
    Input: List of vital sign dicts with keys: time, bp, hr, temp, spo2
    Returns: trend analysis with direction, severity, and details.
    """
    if not vitals_list or len(vitals_list) < 2:
        return {
            "trend": "insufficient_data",
            "details": "Need at least 2 readings for trend analysis",
            "severity": "LOW"
        }
    
    analysis = {
        "bp_trend": _analyze_bp_trend(vitals_list),
        "hr_trend": _analyze_hr_trend(vitals_list),
        "spo2_trend": _analyze_spo2_trend(vitals_list),
        "overall_severity": "LOW",
        "alerts": []
    }
    
    # Determine overall severity
    severities = [
        analysis["bp_trend"].get("severity", "LOW"),
        analysis["hr_trend"].get("severity", "LOW"),
        analysis["spo2_trend"].get("severity", "LOW")
    ]
    
    if "HIGH" in severities:
        analysis["overall_severity"] = "HIGH"
    elif "MEDIUM" in severities:
        analysis["overall_severity"] = "MEDIUM"
    
    # Collect alerts
    for trend_key in ["bp_trend", "hr_trend", "spo2_trend"]:
        trend = analysis[trend_key]
        if trend.get("severity") in ("HIGH", "MEDIUM"):
            analysis["alerts"].append(trend.get("detail", ""))
    
    return analysis


def _parse_systolic(bp_str: str) -> int:
    """Parse systolic BP from string like '138/88'."""
    try:
        return int(bp_str.split('/')[0])
    except (ValueError, IndexError):
        return 0


def _parse_diastolic(bp_str: str) -> int:
    """Parse diastolic BP from string like '138/88'."""
    try:
        return int(bp_str.split('/')[1])
    except (ValueError, IndexError):
        return 0


def _analyze_bp_trend(vitals: list) -> dict:
    """Analyze blood pressure trend."""
    systolics = []
    for v in vitals:
        bp = v.get('bp', '')
        s = _parse_systolic(bp)
        if s > 0:
            systolics.append(s)
    
    if len(systolics) < 2:
        return {"direction": "unknown", "severity": "LOW", "detail": "Insufficient BP data"}
    
    # Check for consecutive decline
    consecutive_drops = 0
    for i in range(1, len(systolics)):
        if systolics[i] < systolics[i-1]:
            consecutive_drops += 1
        else:
            consecutive_drops = 0
    
    total_change = systolics[-1] - systolics[0]
    
    if consecutive_drops >= 3 or (consecutive_drops >= 2 and abs(total_change) > 20):
        return {
            "direction": "declining",
            "severity": "HIGH",
            "values": systolics,
            "total_change": total_change,
            "consecutive_drops": consecutive_drops,
            "detail": f"Systolic BP declining: {systolics[0]}→{systolics[-1]} mmHg ({consecutive_drops} consecutive drops, Δ{total_change})"
        }
    elif consecutive_drops >= 2:
        return {
            "direction": "declining",
            "severity": "MEDIUM",
            "values": systolics,
            "total_change": total_change,
            "detail": f"Systolic BP trending down: {systolics[0]}→{systolics[-1]} mmHg"
        }
    elif abs(total_change) <= 10:
        return {
            "direction": "stable",
            "severity": "LOW",
            "values": systolics,
            "detail": f"BP stable: {systolics[0]}→{systolics[-1]} mmHg"
        }
    else:
        direction = "improving" if total_change > 0 else "declining"
        return {
            "direction": direction,
            "severity": "LOW",
            "values": systolics,
            "detail": f"BP {direction}: {systolics[0]}→{systolics[-1]} mmHg"
        }


def _analyze_hr_trend(vitals: list) -> dict:
    """Analyze heart rate trend."""
    hrs = []
    for v in vitals:
        try:
            hr = int(v.get('hr', 0))
            if hr > 0:
                hrs.append(hr)
        except (ValueError, TypeError):
            continue
    
    if len(hrs) < 2:
        return {"direction": "unknown", "severity": "LOW", "detail": "Insufficient HR data"}
    
    change = hrs[-1] - hrs[0]
    
    if hrs[-1] > 100:
        return {
            "direction": "tachycardic",
            "severity": "HIGH",
            "values": hrs,
            "detail": f"Heart rate elevated: {hrs[-1]} bpm (tachycardia)"
        }
    elif change > 15:
        return {
            "direction": "increasing",
            "severity": "MEDIUM",
            "values": hrs,
            "detail": f"HR increasing: {hrs[0]}→{hrs[-1]} bpm (possible compensatory response)"
        }
    else:
        return {
            "direction": "stable",
            "severity": "LOW",
            "values": hrs,
            "detail": f"HR stable: {hrs[0]}→{hrs[-1]} bpm"
        }


def _analyze_spo2_trend(vitals: list) -> dict:
    """Analyze SpO2 trend."""
    spo2s = []
    for v in vitals:
        try:
            val = int(v.get('spo2', 0))
            if val > 0:
                spo2s.append(val)
        except (ValueError, TypeError):
            continue
    
    if len(spo2s) < 2:
        return {"direction": "unknown", "severity": "LOW", "detail": "Insufficient SpO2 data"}
    
    if spo2s[-1] < 92:
        return {
            "direction": "critical",
            "severity": "HIGH",
            "values": spo2s,
            "detail": f"SpO2 critically low: {spo2s[-1]}%"
        }
    elif spo2s[-1] < 95 and spo2s[0] >= 95:
        return {
            "direction": "declining",
            "severity": "MEDIUM",
            "values": spo2s,
            "detail": f"SpO2 declining: {spo2s[0]}→{spo2s[-1]}%"
        }
    else:
        return {
            "direction": "stable",
            "severity": "LOW",
            "values": spo2s,
            "detail": f"SpO2 stable: {spo2s[0]}→{spo2s[-1]}%"
        }


@mcp.tool()
def check_missing_fields(patient_dict: dict) -> list:
    """
    Check patient data for missing or incomplete clinical fields.
    Compares against expected fields for the patient's clinical context.
    
    Returns: list of dicts with field name, significance, and reason.
    """
    missing = []
    
    # Required fields for all patients
    required_fields = {
        'patient_id': 'Patient identification',
        'name': 'Patient name',
        'age': 'Patient age',
        'admission_reason': 'Admission reason',
        'admitting_doctor': 'Admitting doctor',
    }
    
    for field, desc in required_fields.items():
        if not patient_dict.get(field):
            missing.append({
                "field": desc,
                "significance": "MEDIUM",
                "reason": f"{desc} not documented in clinical report"
            })
    
    # Check vitals
    vitals = patient_dict.get('vitals', [])
    if not vitals:
        missing.append({
            "field": "Vital signs",
            "significance": "HIGH",
            "reason": "No vital signs recorded in report"
        })
    
    # Check medications
    meds = patient_dict.get('medications', [])
    if not meds:
        missing.append({
            "field": "Medication list",
            "significance": "MEDIUM",
            "reason": "No medications documented"
        })
    
    # Check pain score
    pain = patient_dict.get('pain_score', {})
    if isinstance(pain, dict):
        if not pain.get('scores'):
            missing.append({
                "field": "Pain assessment",
                "significance": "MEDIUM",
                "reason": "No pain score recorded"
            })
        
        if pain.get('missing_post_op'):
            missing.append({
                "field": "Post-operative pain score",
                "significance": "HIGH",
                "reason": "Post-operative pain assessment not documented. Critical for post-surgical pain management evaluation."
            })
    
    # Check for procedure-related expectations
    procedures = patient_dict.get('procedures', [])
    admission = patient_dict.get('admission_reason', '').lower()
    
    if procedures or 'surgery' in admission or 'post-op' in admission:
        # Post-surgical patients need more monitoring
        if len(vitals) < 4:
            missing.append({
                "field": "Post-operative vital sign frequency",
                "significance": "MEDIUM",
                "reason": "Post-surgical patients typically require more frequent vital sign monitoring"
            })
    
    # Check for cardiac-specific fields
    if 'chest pain' in admission or 'acs' in admission or 'cardiac' in admission:
        investigations = patient_dict.get('investigations', [])
        inv_text = ' '.join(investigations).lower() if investigations else ''
        
        if 'troponin' not in inv_text:
            missing.append({
                "field": "Troponin levels",
                "significance": "HIGH",
                "reason": "Cardiac patient without documented troponin results — essential for ACS workup"
            })
    
    # Check explicit missing flags from PDF parsing
    for flag in patient_dict.get('missing_flags', []):
        # Avoid duplicates
        if not any(m['field'].lower() in flag.lower() or flag.lower() in m['reason'].lower() 
                   for m in missing):
            missing.append({
                "field": flag,
                "significance": "HIGH",
                "reason": flag
            })
    
    return missing


@mcp.tool()
def format_sbar(agent_outputs: dict) -> dict:
    """
    Format agent outputs into a structured SBAR brief.
    
    Input dict should contain:
        - patient: patient data dict
        - risk: risk assessment (optional)
        - missing: missing info (optional)
    
    Returns: SBAR formatted dict with situation, background, assessment, recommendation, color.
    """
    patient = agent_outputs.get('patient', {})
    risk = agent_outputs.get('risk', {})
    missing = agent_outputs.get('missing', {})
    
    name = patient.get('name', 'Unknown Patient')
    age = patient.get('age', 'N/A')
    patient_id = patient.get('patient_id', 'N/A')
    admission = patient.get('admission_reason', 'Not specified')
    
    # Determine severity color
    severity = risk.get('severity', 'LOW')
    missing_fields = missing.get('missing_fields', [])
    high_missing = [m for m in missing_fields if m.get('significance') == 'HIGH']
    
    if severity == 'HIGH' or len(high_missing) >= 2:
        color = 'RED'
    elif severity == 'MEDIUM' or len(high_missing) >= 1:
        color = 'AMBER'
    else:
        color = 'GREEN'
    
    # Build SBAR
    # Situation
    vitals = patient.get('vitals', [])
    latest_vital = vitals[-1] if vitals else {}
    situation = (
        f"{name}, {age}yo, {patient_id}. "
        f"Admitted for: {admission}. "
    )
    if latest_vital:
        situation += f"Latest vitals — BP {latest_vital.get('bp', 'N/A')}, HR {latest_vital.get('hr', 'N/A')}, SpO2 {latest_vital.get('spo2', 'N/A')}%."
    
    # Background
    meds = patient.get('medications', [])
    med_list = ', '.join([f"{m.get('name', '')} {m.get('dose', '')}".strip() for m in meds]) if meds else 'None documented'
    
    procedures = patient.get('procedures', [])
    proc_text = '; '.join(procedures) if procedures else 'None'
    
    background = (
        f"Procedures: {proc_text}. "
        f"Current medications: {med_list}. "
    )
    
    investigations = patient.get('investigations', [])
    if investigations:
        background += f"Investigations: {'; '.join(investigations[:3])}."
    
    # Assessment
    assessment_parts = []
    
    if risk.get('flags'):
        assessment_parts.append(f"Risk level: {severity}.")
        for flag in risk['flags']:
            assessment_parts.append(f"⚠ {flag}")
    
    if missing_fields:
        assessment_parts.append(f"Missing information ({len(missing_fields)} items):")
        for mf in missing_fields:
            sig = mf.get('significance', 'LOW')
            assessment_parts.append(f"  • [{sig}] {mf.get('field', 'Unknown')}: {mf.get('reason', '')}")
    
    if not assessment_parts:
        assessment_parts.append("No significant risk flags or missing information identified. Patient stable.")
    
    assessment = ' '.join(assessment_parts)
    
    # Recommendation
    recommendations = []
    
    if severity == 'HIGH':
        recommendations.append("URGENT: Immediate medical review required.")
    
    if risk.get('flags'):
        for flag in risk['flags']:
            if 'bp' in flag.lower() or 'blood pressure' in flag.lower():
                recommendations.append("Monitor BP every 30 minutes. Consider fluid resuscitation if decline continues.")
            if 'troponin' in flag.lower():
                recommendations.append("Obtain repeat troponin STAT. Ensure serial cardiac markers are being tracked.")
            if 'spo2' in flag.lower() or 'oxygen' in flag.lower():
                recommendations.append("Monitor SpO2 continuously. Consider supplemental O2 if <94%.")
    
    if high_missing:
        for mf in high_missing:
            field = mf.get('field', '')
            if 'pain' in field.lower():
                recommendations.append("Perform and document post-operative pain assessment immediately.")
            elif 'troponin' in field.lower():
                recommendations.append("Chase and document repeat troponin result.")
            else:
                recommendations.append(f"Document: {field}.")
    
    if not recommendations:
        recommendations.append("Continue current management plan. Routine observations.")
    
    # Pain info
    pain = patient.get('pain_score', {})
    pain_text = ""
    if isinstance(pain, dict) and pain.get('scores'):
        latest_pain = pain['scores'][-1]
        pain_text = f"Pain: {latest_pain.get('score', 'N/A')}/10"
        if latest_pain.get('time'):
            pain_text += f" at {latest_pain['time']}"
    
    clinical_notes = patient.get('clinical_notes', '')
    
    return {
        "patient_id": patient_id,
        "patient_name": name,
        "color": color,
        "severity": severity,
        "sbar": {
            "situation": situation,
            "background": background,
            "assessment": assessment,
            "recommendation": ' '.join(recommendations)
        },
        "pain": pain_text,
        "clinical_notes": clinical_notes[:300] if clinical_notes else "",
        "flags_count": len(risk.get('flags', [])),
        "missing_count": len(missing_fields)
    }


@mcp.tool()
def replan_workflow(current_state: dict, doctor_instruction: str) -> dict:
    """
    Re-generate the task graph incorporating doctor feedback.
    Modifies the current workflow based on the doctor's correction.
    
    Args:
        current_state: Current state of all patients and their assessments
        doctor_instruction: Doctor's correction or feedback text
    
    Returns: Updated task graph with modified routing
    """
    from utils.llm import call_llm
    
    instruction_lower = doctor_instruction.lower()
    patient_id = current_state.get('patient_id', '')
    
    # Use LLM to replan (or simulation)
    system_prompt = """You are a clinical workflow planner. A doctor has provided feedback 
    on a patient assessment. Based on this feedback, determine:
    1. Whether the risk level should be adjusted
    2. Which agents need to re-evaluate
    3. The updated routing

    Return JSON with:
    {
        "adjusted_severity": "HIGH|MEDIUM|LOW",
        "re_evaluate_agents": ["list of agents to re-run"],
        "reason": "explanation of adjustment",
        "new_route": "risk|missing|synthesis"
    }"""
    
    user_prompt = f"""Patient ID: {patient_id}
    Current assessment: {json.dumps(current_state, indent=2)}
    Doctor feedback: {doctor_instruction}"""
    
    result = call_llm(system_prompt, user_prompt)
    
    # If simulation mode or LLM fails, use rule-based replan
    if not result or 'adjusted_severity' not in result:
        result = _rule_based_replan(current_state, doctor_instruction)
    
    result['patient_id'] = patient_id
    result['feedback_applied'] = doctor_instruction
    
    return result


def _rule_based_replan(current_state: dict, instruction: str) -> dict:
    """Rule-based replan when LLM is unavailable."""
    instruction_lower = instruction.lower()
    
    current_severity = current_state.get('severity', 'MEDIUM')
    
    # Detect instruction intent
    if any(word in instruction_lower for word in ['low bp', 'naturally low', 'baseline low', 'normal for']):
        return {
            "adjusted_severity": "LOW",
            "re_evaluate_agents": ["risk", "synthesis"],
            "reason": "Doctor clarified that the observed values are within patient's normal baseline.",
            "new_route": "synthesis"
        }
    elif any(word in instruction_lower for word in ['concerning', 'worried', 'escalate', 'urgent']):
        return {
            "adjusted_severity": "HIGH",
            "re_evaluate_agents": ["risk", "synthesis"],
            "reason": "Doctor expressed heightened concern. Escalating assessment.",
            "new_route": "risk"
        }
    elif any(word in instruction_lower for word in ['recheck', 'verify', 'confirm', 'missing']):
        return {
            "adjusted_severity": current_severity,
            "re_evaluate_agents": ["missing", "synthesis"],
            "reason": "Doctor requested verification of data completeness.",
            "new_route": "missing"
        }
    elif any(word in instruction_lower for word in ['stable', 'fine', 'ok', 'discharge', 'good']):
        return {
            "adjusted_severity": "LOW",
            "re_evaluate_agents": ["synthesis"],
            "reason": "Doctor confirmed patient is stable. Updating assessment.",
            "new_route": "synthesis"
        }
    else:
        return {
            "adjusted_severity": current_severity,
            "re_evaluate_agents": ["risk", "missing", "synthesis"],
            "reason": f"Doctor feedback: {instruction}. Re-evaluating all assessments.",
            "new_route": "risk"
        }


def run_mcp_server(port: int = 5005):
    """Run the MCP server."""
    import uvicorn
    logger.info(f"Starting MCP server on port {port}")
    mcp.run(transport="sse", port=port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_mcp_server()
