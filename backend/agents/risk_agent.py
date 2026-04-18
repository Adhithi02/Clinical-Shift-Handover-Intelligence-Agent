"""
Risk Flag Agent — A2A Server (Port 5002)
Detects declining vital trends, post-procedure monitoring windows,
drug interaction flags, and returns severity levels.
"""
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_a2a import A2AServer, skill, agent

logger = logging.getLogger(__name__)


@agent(
    name="RiskFlagAgent",
    description="Analyzes patient data for clinical risk flags including declining vital trends, post-procedure monitoring gaps, and drug interaction concerns.",
    version="1.0.0"
)
class RiskFlagAgent(A2AServer):
    """
    The Risk Flag Agent receives structured patient data and performs
    deep risk analysis using vital trend detection and LLM reasoning.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.port = 5002
    
    @skill(
        name="assess_risk",
        description="Perform comprehensive risk assessment on patient data",
        tags=["risk", "vitals", "safety"]
    )
    def handle_task(self, task):
        """Process incoming risk assessment task."""
        try:
            if hasattr(task, 'message') and task.message:
                content = task.message.content if hasattr(task.message, 'content') else str(task.message)
            else:
                content = str(task)
            
            try:
                patient_data = json.loads(content) if isinstance(content, str) else content
            except (json.JSONDecodeError, TypeError):
                patient_data = {}
            
            result = self._assess_risk(patient_data)
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Risk Agent error: {e}")
            return json.dumps({
                "severity": "MEDIUM",
                "flags": [f"Risk assessment error: {str(e)}"],
                "reasons": [str(e)]
            })
    
    def _assess_risk(self, patient: dict) -> dict:
        """Perform comprehensive risk assessment."""
        from utils.llm import call_llm, is_simulation_mode
        from tools.mcp_server import detect_vital_trend
        
        vitals = patient.get('vitals', [])
        medications = patient.get('medications', [])
        admission = patient.get('admission_reason', '')
        procedures = patient.get('procedures', [])
        investigations = patient.get('investigations', [])
        name = patient.get('name', 'Unknown')
        
        # Step 1: Vital trend analysis via MCP tool
        trend_analysis = detect_vital_trend(vitals) if vitals else {
            "overall_severity": "LOW",
            "alerts": [],
            "bp_trend": {"direction": "unknown"},
            "hr_trend": {"direction": "unknown"},
            "spo2_trend": {"direction": "unknown"}
        }
        
        # Step 2: Rule-based risk detection
        flags = []
        reasons = []
        severity = trend_analysis.get("overall_severity", "LOW")
        
        # BP trend flags
        bp_trend = trend_analysis.get("bp_trend", {})
        if bp_trend.get("severity") in ("HIGH", "MEDIUM"):
            flags.append(bp_trend.get("detail", "BP trend concern"))
            reasons.append(f"Blood pressure analysis: {bp_trend.get('detail', 'Abnormal trend')}")
        
        # HR trend flags
        hr_trend = trend_analysis.get("hr_trend", {})
        if hr_trend.get("severity") in ("HIGH", "MEDIUM"):
            flags.append(hr_trend.get("detail", "HR trend concern"))
            reasons.append(f"Heart rate analysis: {hr_trend.get('detail', 'Abnormal trend')}")
        
        # SpO2 trend flags
        spo2_trend = trend_analysis.get("spo2_trend", {})
        if spo2_trend.get("severity") in ("HIGH", "MEDIUM"):
            flags.append(spo2_trend.get("detail", "SpO2 trend concern"))
            reasons.append(f"Oxygen saturation: {spo2_trend.get('detail', 'Abnormal trend')}")
        
        # Drug interaction checks
        drug_interactions = self._check_drug_interactions(medications)
        if drug_interactions:
            flags.extend(drug_interactions)
            reasons.extend([f"Drug interaction: {d}" for d in drug_interactions])
            if severity == "LOW":
                severity = "MEDIUM"
        
        # Post-procedure monitoring check
        if procedures:
            proc_flags = self._check_post_procedure(patient)
            if proc_flags:
                flags.extend(proc_flags)
                reasons.extend(proc_flags)
        
        # Cardiac-specific checks
        if any(kw in admission.lower() for kw in ['chest pain', 'acs', 'cardiac', 'mi']):
            cardiac_flags = self._check_cardiac(patient)
            if cardiac_flags:
                flags.extend(cardiac_flags)
                reasons.extend(cardiac_flags)
                severity = "HIGH"
        
        # Step 3: LLM enhancement if available
        if not is_simulation_mode() and (flags or vitals):
            llm_assessment = self._llm_assess(patient, flags, trend_analysis)
            if llm_assessment:
                # Merge LLM insights
                if llm_assessment.get('additional_flags'):
                    flags.extend(llm_assessment['additional_flags'])
                if llm_assessment.get('severity') == 'HIGH':
                    severity = 'HIGH'
        
        result = {
            "patient_id": patient.get("patient_id", ""),
            "patient_name": name,
            "severity": severity,
            "flags": flags if flags else ["No significant risk flags identified"],
            "reasons": reasons if reasons else ["Patient appears clinically stable"],
            "trend_analysis": {
                "bp": bp_trend.get("direction", "unknown"),
                "hr": hr_trend.get("direction", "unknown"),
                "spo2": spo2_trend.get("direction", "unknown")
            },
            "recommendation": self._get_recommendation(severity, flags)
        }
        
        logger.info(f"Risk assessment for {name}: {severity} with {len(flags)} flags")
        return result
    
    def _check_drug_interactions(self, medications: list) -> list:
        """Check for potential drug interactions."""
        interactions = []
        med_names = [m.get('name', '').lower() for m in medications]
        
        # Common interaction checks
        if 'aspirin' in ' '.join(med_names) and 'enoxaparin' in ' '.join(med_names):
            interactions.append("Aspirin + Enoxaparin: Increased bleeding risk — monitor for signs of bleeding")
        
        if 'metoprolol' in ' '.join(med_names):
            # Beta-blocker with potential BP concerns
            interactions.append("Metoprolol (beta-blocker): Monitor for excessive bradycardia and hypotension")
        
        if any('nsaid' in m or 'ibuprofen' in m or 'diclofenac' in m for m in med_names):
            if any('enoxaparin' in m or 'aspirin' in m for m in med_names):
                interactions.append("NSAID with anticoagulant/antiplatelet: Elevated bleeding risk")
        
        return interactions
    
    def _check_post_procedure(self, patient: dict) -> list:
        """Check post-procedure monitoring adequacy."""
        flags = []
        vitals = patient.get('vitals', [])
        procedures = patient.get('procedures', [])
        
        if procedures and len(vitals) < 4:
            flags.append("Post-procedure patient with infrequent vital sign monitoring")
        
        pain = patient.get('pain_score', {})
        if isinstance(pain, dict) and pain.get('missing_post_op'):
            flags.append("Post-operative pain assessment not documented — critical for recovery monitoring")
        
        return flags
    
    def _check_cardiac(self, patient: dict) -> list:
        """Cardiac-specific risk checks."""
        flags = []
        investigations = patient.get('investigations', [])
        inv_text = ' '.join(str(i) for i in investigations).lower()
        
        if 'not documented' in inv_text:
            flags.append("Missing cardiac investigation results — critical for ACS workup")
        
        vitals = patient.get('vitals', [])
        if vitals:
            latest = vitals[-1]
            try:
                spo2 = int(latest.get('spo2', 99))
                if spo2 < 95:
                    flags.append(f"SpO2 {spo2}% in cardiac patient — monitor respiratory status")
            except (ValueError, TypeError):
                pass
        
        return flags
    
    def _llm_assess(self, patient: dict, current_flags: list, trend: dict) -> dict:
        """Use LLM for additional risk assessment."""
        from utils.llm import call_llm
        
        system_prompt = """You are a clinical risk assessment specialist. Review the patient data 
        and existing risk flags. Identify any ADDITIONAL risks not already flagged.
        
        Return JSON:
        {
            "additional_flags": ["list of new risk flags not already identified"],
            "severity": "HIGH|MEDIUM|LOW",
            "clinical_reasoning": "brief explanation"
        }"""
        
        user_prompt = f"""Patient: {patient.get('name')}
        Admission: {patient.get('admission_reason')}
        Current flags: {json.dumps(current_flags)}
        Vital trend: {json.dumps(trend)}
        Medications: {json.dumps([m.get('name','') for m in patient.get('medications',[])])}"""
        
        return call_llm(system_prompt, user_prompt)
    
    def _get_recommendation(self, severity: str, flags: list) -> str:
        """Generate recommendation based on severity."""
        if severity == "HIGH":
            return "URGENT: Immediate medical review required. Consider escalation to senior clinician."
        elif severity == "MEDIUM":
            return "Close monitoring recommended. Review within 1 hour. Inform covering doctor."
        else:
            return "Continue routine monitoring as per care plan."


def run_risk_server(port: int = 5002):
    """Run the Risk Flag Agent as an A2A server."""
    risk = RiskFlagAgent()
    logger.info(f"Starting Risk Flag Agent on port {port}")
    risk.start(port=port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_risk_server()
