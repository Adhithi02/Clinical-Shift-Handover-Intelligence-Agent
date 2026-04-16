"""
Synthesis Agent — A2A Server (Port 5004)
Takes outputs from Risk + Missing Info agents (or directly from Planner)
and produces the final SBAR handover brief.
"""
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_a2a import A2AServer, skill, agent

logger = logging.getLogger(__name__)


@agent(
    name="SynthesisAgent",
    description="Synthesizes outputs from risk and missing info agents into a structured SBAR handover brief with color-coded severity.",
    version="1.0.0"
)
class SynthesisAgent(A2AServer):
    """
    The Synthesis Agent takes all available outputs and produces
    the final SBAR handover brief for the incoming doctor.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.port = 5004
    
    @skill(
        name="synthesize_sbar",
        description="Generate SBAR handover brief from agent outputs",
        tags=["sbar", "handover", "synthesis"]
    )
    def handle_task(self, task):
        """Process incoming synthesis task."""
        try:
            if hasattr(task, 'message') and task.message:
                content = task.message.content if hasattr(task.message, 'content') else str(task.message)
            else:
                content = str(task)
            
            try:
                input_data = json.loads(content) if isinstance(content, str) else content
            except (json.JSONDecodeError, TypeError):
                input_data = {}
            
            result = self._synthesize(input_data)
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Synthesis Agent error: {e}")
            return json.dumps({
                "error": str(e),
                "sbar": {
                    "situation": "Error generating SBAR brief",
                    "background": "",
                    "assessment": str(e),
                    "recommendation": "Review patient data manually"
                },
                "color": "AMBER"
            })
    
    def _synthesize(self, input_data: dict) -> dict:
        """Generate the SBAR brief from all agent outputs."""
        from utils.llm import call_llm_text, is_simulation_mode
        from tools.mcp_server import format_sbar
        
        patient = input_data.get('patient', {})
        risk = input_data.get('risk', {})
        missing = input_data.get('missing', {})
        
        # Step 1: Use MCP tool for base SBAR formatting
        sbar_result = format_sbar({
            'patient': patient,
            'risk': risk,
            'missing': missing
        })
        
        # Step 2: Enhance with LLM narrative if available
        if not is_simulation_mode():
            sbar_result = self._llm_enhance(sbar_result, patient, risk, missing, input_data.get('feedback'))
        
        logger.info(f"Synthesized SBAR for {patient.get('name', 'Unknown')} — severity: {sbar_result.get('color', 'N/A')}")
        return sbar_result
    
    def _llm_enhance(self, sbar: dict, patient: dict, risk: dict, missing: dict, feedback: str = None) -> dict:
        """Enhance SBAR sections with LLM-generated narrative."""
        from utils.llm import call_llm_text
        
        try:
            system_prompt = """You are a senior clinical nurse writing a concise SBAR handover brief.
            Write in clear, professional clinical language. Be specific and actionable.
            Keep each section concise (2-3 sentences max)."""
            
            # Enhance Situation
            user_prompt = f"""Write a brief SITUATION statement for SBAR handover:
            Patient: {patient.get('name')}, {patient.get('age')}yo
            Admitted for: {patient.get('admission_reason')}
            Latest vitals: {patient.get('vitals', [{}])[-1] if patient.get('vitals') else 'N/A'}
            Risk level: {risk.get('severity', 'LOW')}
            Doctor Feedback: {feedback if feedback else 'None'}
            
            Write 1-2 sentences only. If feedback is present, acknowledge the clinician's direction. balance metrics with doctor's clinical judgment. """
            
            enhanced_situation = call_llm_text(system_prompt, user_prompt)
            if enhanced_situation and len(enhanced_situation) > 10:
                sbar['sbar']['situation'] = enhanced_situation
            
            # Enhance Recommendation
            user_prompt = f"""Write specific RECOMMENDATIONS for the incoming doctor:
            Risk flags: {json.dumps(risk.get('flags', []))}
            Missing info: {json.dumps([m.get('field') for m in missing.get('missing_fields', [])])}
            Severity: {risk.get('severity', 'LOW')}
            Doctor Feedback: {feedback if feedback else 'None'}
            
            Write 2-3 specific, actionable bullet points. If feedback provided, ensure recommendations align with the doctor's assessment."""
            
            enhanced_rec = call_llm_text(system_prompt, user_prompt)
            if enhanced_rec and len(enhanced_rec) > 10:
                sbar['sbar']['recommendation'] = enhanced_rec
                
        except Exception as e:
            logger.warning(f"LLM enhancement failed, using base SBAR: {e}")
        
        return sbar


def run_synthesis_server(port: int = 5004):
    """Run the Synthesis Agent as an A2A server."""
    synth = SynthesisAgent()
    logger.info(f"Starting Synthesis Agent on port {port}")
    synth.start(port=port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_synthesis_server()
