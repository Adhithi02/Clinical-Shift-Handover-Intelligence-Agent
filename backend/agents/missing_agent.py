"""
Missing Info Agent — A2A Server (Port 5003)
Reasons about what clinical data SHOULD be present but ISN'T,
and assesses the clinical significance of each gap.
"""
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_a2a import A2AServer, skill, agent

logger = logging.getLogger(__name__)


@agent(
    name="MissingInfoAgent",
    description="Analyzes patient clinical data for missing or incomplete information, assesses clinical significance of data gaps, and recommends documentation actions.",
    version="1.0.0"
)
class MissingInfoAgent(A2AServer):
    """
    The Missing Info Agent reasons about what SHOULD be present
    in a patient's clinical record but ISN'T, considering the
    patient's specific clinical context.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.port = 5003
    
    @skill(
        name="check_missing",
        description="Identify missing clinical information and assess its significance",
        tags=["documentation", "completeness", "quality"]
    )
    def handle_task(self, task):
        """Process incoming missing info check task."""
        try:
            if hasattr(task, 'message') and task.message:
                content = task.message.content if hasattr(task.message, 'content') else str(task.message)
            else:
                content = str(task)
            
            try:
                patient_data = json.loads(content) if isinstance(content, str) else content
            except (json.JSONDecodeError, TypeError):
                patient_data = {}
            
            result = self._check_missing(patient_data)
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Missing Info Agent error: {e}")
            return json.dumps({
                "missing_fields": [{"field": "Error", "significance": "LOW", "reason": str(e)}]
            })
    
    def _check_missing(self, patient: dict) -> dict:
        """Comprehensive missing information analysis."""
        from utils.llm import is_simulation_mode
        from tools.mcp_server import check_missing_fields
        
        # Step 1: Use MCP tool for structured field checking
        missing_fields = check_missing_fields(patient)
        
        # Step 2: Context-aware analysis
        admission = patient.get('admission_reason', '').lower()
        procedures = patient.get('procedures', [])
        
        # Post-surgical context
        if procedures or 'surgery' in admission or 'post-op' in admission:
            surgical_missing = self._check_surgical_context(patient)
            missing_fields.extend(surgical_missing)
        
        # Cardiac context
        if any(kw in admission for kw in ['chest pain', 'acs', 'cardiac', 'heart', 'mi']):
            cardiac_missing = self._check_cardiac_context(patient)
            missing_fields.extend(cardiac_missing)
        
        # Infection context
        if any(kw in admission for kw in ['infection', 'uti', 'sepsis', 'pneumonia']):
            infection_missing = self._check_infection_context(patient)
            missing_fields.extend(infection_missing)
        
        # Step 3: LLM enhancement if available
        if not is_simulation_mode():
            llm_missing = self._llm_check(patient, missing_fields)
            if llm_missing:
                missing_fields.extend(llm_missing)
        
        # Deduplicate
        seen = set()
        unique_missing = []
        for mf in missing_fields:
            field_key = mf.get('field', '').lower()
            if field_key not in seen:
                seen.add(field_key)
                unique_missing.append(mf)
        
        # Sort by significance
        sig_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        unique_missing.sort(key=lambda x: sig_order.get(x.get('significance', 'LOW'), 2))
        
        result = {
            "patient_id": patient.get("patient_id", ""),
            "patient_name": patient.get("name", "Unknown"),
            "missing_fields": unique_missing,
            "total_missing": len(unique_missing),
            "high_significance_count": sum(1 for m in unique_missing if m.get('significance') == 'HIGH'),
            "completeness_score": self._calculate_completeness(patient, unique_missing)
        }
        
        logger.info(f"Missing info check for {result['patient_name']}: {result['total_missing']} items ({result['high_significance_count']} high significance)")
        return result
    
    def _check_surgical_context(self, patient: dict) -> list:
        """Check for missing info specific to post-surgical patients."""
        missing = []
        
        pain = patient.get('pain_score', {})
        vitals = patient.get('vitals', [])
        clinical_notes = patient.get('clinical_notes', '').lower()
        
        # Wound/surgical site documentation
        if 'dressing' not in clinical_notes and 'wound' not in clinical_notes and 'site' not in clinical_notes:
            missing.append({
                "field": "Surgical site assessment",
                "significance": "MEDIUM",
                "reason": "No surgical site or dressing assessment documented for post-surgical patient"
            })
        
        # Drain output (if applicable)
        if 'drain' in clinical_notes and 'output' not in clinical_notes:
            missing.append({
                "field": "Drain output measurement",
                "significance": "MEDIUM",
                "reason": "Drain mentioned but output volume not documented"
            })
        
        # Mobilization assessment
        if 'mobili' not in clinical_notes and 'physio' not in clinical_notes:
            missing.append({
                "field": "Post-operative mobilization status",
                "significance": "LOW",
                "reason": "No post-operative mobilization or physiotherapy assessment documented"
            })
        
        # DVT prophylaxis check
        meds = patient.get('medications', [])
        med_names = ' '.join([m.get('name', '').lower() for m in meds])
        if 'enoxaparin' not in med_names and 'heparin' not in med_names and 'prophylaxis' not in clinical_notes:
            missing.append({
                "field": "DVT prophylaxis documentation",
                "significance": "HIGH",
                "reason": "No anticoagulant prophylaxis documented for post-surgical patient — DVT risk"
            })
        
        return missing
    
    def _check_cardiac_context(self, patient: dict) -> list:
        """Check for missing info specific to cardiac patients."""
        missing = []
        
        investigations = patient.get('investigations', [])
        inv_text = ' '.join(str(i) for i in investigations).lower()
        clinical_notes = patient.get('clinical_notes', '').lower()
        
        # ECG documentation
        if 'ecg' not in inv_text and 'ecg' not in clinical_notes:
            missing.append({
                "field": "ECG documentation",
                "significance": "HIGH",
                "reason": "No ECG documented for cardiac patient — essential for ACS workup"
            })
        
        # Serial troponins
        if 'troponin' in inv_text:
            if 'not documented' in inv_text or 'not recorded' in inv_text:
                missing.append({
                    "field": "Repeat troponin result",
                    "significance": "HIGH",
                    "reason": "Serial troponin monitoring incomplete — repeat result not documented. Critical for ACS diagnosis."
                })
        
        # Cardiac monitoring
        if 'monitor' not in clinical_notes and 'telemetry' not in clinical_notes:
            missing.append({
                "field": "Cardiac monitoring status",
                "significance": "MEDIUM",
                "reason": "Cardiac monitoring status not documented"
            })
        
        # Cardiology review
        if 'cardio' not in clinical_notes and 'consultant' not in clinical_notes:
            missing.append({
                "field": "Cardiology review/consultation",
                "significance": "MEDIUM",
                "reason": "No specialist cardiology review documented"
            })
        
        return missing
    
    def _check_infection_context(self, patient: dict) -> list:
        """Check for missing info specific to infection patients."""
        missing = []
        
        investigations = patient.get('investigations', [])
        inv_text = ' '.join(str(i) for i in investigations).lower()
        
        # Culture results
        if 'culture' not in inv_text:
            missing.append({
                "field": "Culture results",
                "significance": "MEDIUM",
                "reason": "No culture results documented for patient with infection"
            })
        
        # Antibiotic sensitivity
        if 'sensitive' not in inv_text and 'sensitivity' not in inv_text:
            missing.append({
                "field": "Antibiotic sensitivity report",
                "significance": "MEDIUM",
                "reason": "Antibiotic sensitivity not documented — important for targeted therapy"
            })
        
        return missing
    
    def _llm_check(self, patient: dict, current_missing: list) -> list:
        """Use LLM to identify additional missing information."""
        from utils.llm import call_llm
        
        system_prompt = """You are a clinical documentation specialist. Review this patient's data 
        and identify any ADDITIONAL missing clinical information not already flagged.
        Consider the patient's specific clinical context.
        
        Return JSON:
        {
            "additional_missing": [
                {"field": "field name", "significance": "HIGH|MEDIUM|LOW", "reason": "why this is needed"}
            ]
        }"""
        
        user_prompt = f"""Patient: {patient.get('name')}, Age: {patient.get('age')}
        Admission: {patient.get('admission_reason')}
        Already flagged missing: {json.dumps([m.get('field') for m in current_missing])}
        Available data: vitals ({len(patient.get('vitals',[]))} readings), 
        meds ({len(patient.get('medications',[]))}), 
        investigations ({len(patient.get('investigations',[]))})"""
        
        result = call_llm(system_prompt, user_prompt)
        return result.get('additional_missing', []) if result else []
    
    def _calculate_completeness(self, patient: dict, missing: list) -> float:
        """Calculate a completeness score (0-100) for the patient record."""
        total_expected = 10  # baseline expected fields
        high_missing = sum(1 for m in missing if m.get('significance') == 'HIGH')
        med_missing = sum(1 for m in missing if m.get('significance') == 'MEDIUM')
        low_missing = sum(1 for m in missing if m.get('significance') == 'LOW')
        
        # Weighted deduction
        score = 100 - (high_missing * 15) - (med_missing * 8) - (low_missing * 3)
        return max(0, min(100, round(score, 1)))


def run_missing_server(port: int = 5003):
    """Run the Missing Info Agent as an A2A server."""
    agent = MissingInfoAgent()
    logger.info(f"Starting Missing Info Agent on port {port}")
    agent.start(port=port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_missing_server()
