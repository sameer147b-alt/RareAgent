from typing import Dict, Any, List
import dspy
import logging
from core.types import RareAgentState

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- DSPy Signatures ---

class ClinicalCritique(dspy.Signature):
    """
    Act as an aggressive clinical auditor. Review the proposed drug repurposing hypothesis.
    Look for pharmacological RED FLAGS, specifically Dose-Limiting Toxicities (DLTs), 
    severe off-target effects (e.g., hERG inhibition), and Phase II clinical trial failures.
    """
    drug_name = dspy.InputField(desc="The name of the proposed drug.")
    target_gene = dspy.InputField(desc="The target gene.")
    mechanism = dspy.InputField(desc="The proposed mechanism.")
    rationale = dspy.InputField(desc="The proponent's rationale.")
    
    critique = dspy.OutputField(desc="A detailed clinical critique of the hypothesis.")
    safety_concerns = dspy.OutputField(desc="Specific safety risks (DLTs, off-targets).")
    verdict = dspy.OutputField(desc="Final verdict: 'SAFE' or 'RISKY' or 'REJECT'.")

# --- Skeptic Agent ---

class SkepticAgent:
    """
    Skeptic Agent: Provides adversarial critique using LLM reasoning.
    """
    def __init__(self):
        self.critique_program = dspy.ChainOfThought(ClinicalCritique)

    def run(self, state: RareAgentState) -> Dict[str, Any]:
        """
        Executes the Skeptic Agent workflow.
        Critiques the *latest* hypothesis added by the Proponent.
        """
        hypotheses = state.get("hypotheses", [])
        debate_history = state.get("debate_history", [])
        
        if not hypotheses:
            logger.warning("No hypotheses to critique.")
            return {"hypotheses": [], "debate_history": debate_history}

        # Get the latest hypothesis
        latest_hypothesis = hypotheses[-1]
        drug_name = latest_hypothesis.get("drug_name")
        
        # Avoid critiquing if already critiqued (simple check)
        if latest_hypothesis.get("skeptic_verdict"):
             logger.info(f"Hypothesis for {drug_name} already critiqued.")
             return {"hypotheses": hypotheses, "debate_history": debate_history}

        logger.info(f"Skeptic Agent critiquing: {drug_name}...")

        try:
            # Generate Critique
            prediction = self.critique_program(
                drug_name=drug_name,
                target_gene=latest_hypothesis.get("target_gene", "Unknown"),
                mechanism=latest_hypothesis.get("mechanism", "Unknown"),
                rationale=latest_hypothesis.get("rationale", "Unknown")
            )

            critique_entry = (
                f"### Skeptic Critique: {drug_name}\n"
                f"**Verdict**: {prediction.verdict}\n"
                f"**Safety Concerns**: {prediction.safety_concerns}\n"
                f"**Analysis**: {prediction.critique}\n"
            )

            # Update Hypothesis with critique data
            latest_hypothesis["skeptic_critique"] = prediction.critique
            latest_hypothesis["skeptic_safety"] = prediction.safety_concerns
            latest_hypothesis["skeptic_verdict"] = prediction.verdict

            # Update State
            updated_history = debate_history + [critique_entry]
            
            # We return updated hypotheses list (with the modified last item) and history
            return {
                "hypotheses": hypotheses, 
                "debate_history": updated_history
            }

        except Exception as e:
            logger.error(f"Skeptic Agent failed: {e}")
            return {}

if __name__ == "__main__":
    # Test Run (Requires configured LM)
    try:
        import os
        from dotenv import load_dotenv

        load_dotenv()
        
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            print("WARNING: GROQ_API_KEY not found! Please check your .env file.")
            raise ValueError("GROQ_API_KEY environment variable not set")
        lm = dspy.LM(model='groq/llama-3.3-70b-versatile', api_key=api_key)
        dspy.settings.configure(lm=lm)
        
        agent = SkepticAgent()
        state = {
            "debate_history": [],
            "hypotheses": [
                {"drug_name": "Metformin", "target_gene": "AMPK", "mechanism": "Activator", "rationale": "Good logic."}
            ]
        }
        updates = agent.run(state)
        print(updates.get("debate_history")[0])
    except Exception as e:
        print(f"Test failed: {e}")
