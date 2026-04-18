"""
Ollama LLM client wrapper with simulation fallback.
When Ollama is running with llama3.2, uses real LLM inference.
When Ollama is unavailable, falls back to rule-based simulation.
"""
import json
import logging
import time

logger = logging.getLogger(__name__)

# Track Ollama availability globally
_ollama_available = None


def check_ollama():
    """Check if Ollama is running and accessible."""
    global _ollama_available
    try:
        import ollama
        ollama.list()
        _ollama_available = True
        logger.info("[OK] Ollama is available - using LLM mode")
    except Exception as e:
        _ollama_available = False
        logger.warning(f"[X] Ollama not available ({e}) - using simulation mode")
    return _ollama_available


def call_llm(system_prompt: str, user_prompt: str, model: str = "llama3.2",
             max_retries: int = 3, temperature: float = 0.0) -> dict:
    """
    Call Ollama LLM with structured JSON output.
    Falls back to simulation if Ollama is unavailable.
    
    Args:
        system_prompt: System role instructions
        user_prompt: User message with data
        model: Ollama model name
        max_retries: Number of retry attempts
        temperature: LLM temperature (0 for deterministic)
    
    Returns:
        Parsed JSON dict from LLM response
    """
    global _ollama_available
    
    # Check availability on first call
    if _ollama_available is None:
        check_ollama()
    
    if not _ollama_available:
        return _simulate_response(system_prompt, user_prompt)
    
    # Real Ollama call
    import ollama
    
    for attempt in range(max_retries):
        try:
            response = ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                format="json",
                options={"temperature": temperature}
            )
            
            content = response.message.content.strip()
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned invalid JSON (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logger.error("Max retries reached, falling back to simulation")
                return _simulate_response(system_prompt, user_prompt)
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Ollama error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                _ollama_available = False
                logger.warning("Ollama became unavailable, switching to simulation mode")
                return _simulate_response(system_prompt, user_prompt)
            time.sleep(2)
    
    return _simulate_response(system_prompt, user_prompt)


def call_llm_text(system_prompt: str, user_prompt: str, model: str = "llama3.2") -> str:
    """
    Call Ollama LLM for free-text response (used for SBAR narrative).
    Falls back to simulation if Ollama is unavailable.
    """
    global _ollama_available
    
    if _ollama_available is None:
        check_ollama()
    
    if not _ollama_available:
        return _simulate_text_response(system_prompt, user_prompt)
    
    import ollama
    
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            options={"temperature": 0.1}
        )
        return response.message.content.strip()
    except Exception as e:
        logger.error(f"Ollama text call failed: {e}")
        _ollama_available = False
        return _simulate_text_response(system_prompt, user_prompt)


def _simulate_response(system_prompt: str, user_prompt: str) -> dict:
    """
    Rule-based simulation when Ollama is not available.
    Analyzes prompts to determine context and return appropriate mock responses.
    """
    prompt_lower = (system_prompt + " " + user_prompt).lower()
    
    # Planner routing decision
    if "route" in prompt_lower and "patient" in prompt_lower:
        return _simulate_planner(user_prompt)
    
    # Risk assessment
    if "risk" in prompt_lower and ("severity" in prompt_lower or "flag" in prompt_lower):
        return _simulate_risk(user_prompt)
    
    # Missing info analysis
    if "missing" in prompt_lower and ("field" in prompt_lower or "absent" in prompt_lower):
        return _simulate_missing(user_prompt)
    
    # SBAR synthesis
    if "sbar" in prompt_lower or "synthesis" in prompt_lower:
        return _simulate_sbar(user_prompt)
    
    # Replan
    if "replan" in prompt_lower or "feedback" in prompt_lower:
        return _simulate_replan(user_prompt)
    
    # Default
    return {"status": "simulated", "message": "Simulation mode active"}


def _simulate_planner(prompt: str) -> dict:
    """Simulate planner routing based on patient data keywords."""
    prompt_lower = prompt.lower()
    
    patients = []
    
    # Detect Patient A patterns (missing data)
    if "arun" in prompt_lower or "pat-a" in prompt_lower or "knee replacement" in prompt_lower:
        patients.append({
            "patient_id": "PAT-A-2024-0471",
            "name": "Arun Mehta",
            "route": "missing",
            "reason": "Post-operative pain score not documented after surgery at 14:00. Last recorded at 09:00 pre-op.",
            "priority": "MEDIUM"
        })
    
    # Detect Patient B patterns (declining vitals)
    if "priya" in prompt_lower or "pat-b" in prompt_lower or "chest pain" in prompt_lower:
        patients.append({
            "patient_id": "PAT-B-2024-0892",
            "name": "Priya Sharma",
            "route": "risk",
            "reason": "4 consecutive declining BP readings (138→131→122→114 systolic). Cardiac patient with borderline troponin. Missing repeat troponin result.",
            "priority": "HIGH"
        })
    
    # Detect Patient C patterns (stable)
    if "ravi" in prompt_lower or "pat-c" in prompt_lower or "uti" in prompt_lower:
        patients.append({
            "patient_id": "PAT-C-2024-1203",
            "name": "Ravi Kumar",
            "route": "synthesis",
            "reason": "Stable vitals, all clinical fields complete, responding well to treatment, discharge candidate.",
            "priority": "LOW"
        })
    
    # If no specific patient detected, return a generic routing
    if not patients:
        patients.append({
            "patient_id": "UNKNOWN",
            "name": "Unknown Patient",
            "route": "missing",
            "reason": "Unable to parse patient data, routing to missing info check.",
            "priority": "MEDIUM"
        })
    
    return {"task_graph": patients}


def _simulate_risk(prompt: str) -> dict:
    """Simulate risk assessment."""
    prompt_lower = prompt.lower()
    
    flags = []
    severity = "LOW"
    
    if "declining" in prompt_lower or "drop" in prompt_lower or "138" in prompt_lower:
        flags.append("Consecutive systolic BP decline: 138→131→122→114 mmHg over 6 hours")
        severity = "HIGH"
    
    if "troponin" in prompt_lower and ("missing" in prompt_lower or "not documented" in prompt_lower):
        flags.append("Repeat troponin result not documented — critical for ACS rule-out")
        severity = "HIGH"
    
    if "chest pain" in prompt_lower or "acs" in prompt_lower:
        flags.append("Active cardiac monitoring required for ACS workup")
    
    if "spo2" in prompt_lower and ("94" in prompt_lower or "decline" in prompt_lower):
        flags.append("SpO2 marginal decline from 96% to 94% — monitor respiratory status")
    
    if "heart rate" in prompt_lower and ("92" in prompt_lower or "increase" in prompt_lower):
        flags.append("Compensatory tachycardia noted (HR 88→92) alongside BP decline")

    if not flags:
        flags.append("No specific risk flags identified in available data")
    
    return {
        "severity": severity,
        "flags": flags,
        "reasons": [f"Risk flag detected: {f}" for f in flags],
        "recommendation": "Immediate medical review recommended" if severity == "HIGH" else "Continue routine monitoring"
    }


def _simulate_missing(prompt: str) -> dict:
    """Simulate missing info detection."""
    prompt_lower = prompt.lower()
    
    missing_fields = []
    
    if "pain" in prompt_lower and ("missing" in prompt_lower or "09:00" in prompt_lower):
        missing_fields.append({
            "field": "Post-operative pain score",
            "significance": "HIGH",
            "reason": "No pain assessment after knee replacement at 14:00. Last recorded at 09:00 pre-operatively. Post-op pain management cannot be evaluated."
        })
    
    if "troponin" in prompt_lower and ("not documented" in prompt_lower or "missing" in prompt_lower):
        missing_fields.append({
            "field": "Repeat troponin result (12:00)",
            "significance": "HIGH",
            "reason": "Serial troponin monitoring is essential for ACS rule-out. 6-hour repeat troponin not documented."
        })
    
    if "medication reconciliation" in prompt_lower and "missing" in prompt_lower:
        missing_fields.append({
            "field": "Medication reconciliation note",
            "significance": "MEDIUM",
            "reason": "No medication reconciliation documented post-admission."
        })
    
    if not missing_fields:
        missing_fields.append({
            "field": "General clinical documentation",
            "significance": "LOW",
            "reason": "Minor documentation gaps detected."
        })
    
    return {"missing_fields": missing_fields}


def _simulate_sbar(prompt: str) -> dict:
    """Simulate SBAR generation — handled mostly by format_sbar tool."""
    return {
        "status": "simulated",
        "note": "SBAR generated via rule-based synthesis"
    }


def _simulate_replan(prompt: str) -> dict:
    """Simulate replan workflow."""
    return {
        "replanned": True,
        "note": "Workflow replanned based on doctor feedback (simulation mode)"
    }


def _simulate_text_response(system_prompt: str, user_prompt: str) -> str:
    """Simulate free-text LLM response for narrative generation."""
    return "Clinical assessment generated in simulation mode. Enable Ollama with llama3.2 for AI-powered narrative generation."


def is_simulation_mode() -> bool:
    """Check if running in simulation mode."""
    global _ollama_available
    if _ollama_available is None:
        check_ollama()
    return not _ollama_available
