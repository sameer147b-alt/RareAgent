from typing import Dict, Any, List
import dspy
import logging
from core.types import RareAgentState

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- DSPy Signatures ---

class GenerateHypothesis(dspy.Signature):
    """
    Synthesize disease and target data to propose a novel drug repurposing hypothesis.
    Suggest an EXISTING APPROVED drug that modulates the identified target to treat the disease.
    """
    disease_name = dspy.InputField(desc="The name of the orphan disease.")
    genetic_targets = dspy.InputField(desc="List of identified genetic targets and phenotypes.")
    existing_hypotheses = dspy.InputField(desc="List of already proposed drugs to avoid duplicates.")
    excluded_drugs = dspy.InputField(desc="A list of drugs that have already been evaluated. You MUST NOT propose any drug on this list.", default="")
    last_rejection_reason = dspy.InputField(desc="If your previous hypothesis was REJECTED, this is the exact reason. You MUST read this and correct your next hypothesis to avoid this error.", default="")
    
    drug_name = dspy.OutputField(desc="Name of the proposed existing approved drug.")
    target_gene = dspy.OutputField(desc="The exact, primary gene symbol or UniProt ID only. No explanations, no parentheses, no extra text.")
    mechanism = dspy.OutputField(desc="Mechanism of action (e.g., Inhibitor, Agonist, Chaperone).")
    rationale = dspy.OutputField(desc="Scientific rationale for why this drug would work for this disease context.")

# --- Proponent Agent ---

class ProponentAgent:
    """
    Proponent Agent: Generates drug repurposing hypotheses using LLM reasoning.
    """
    def __init__(self):
        self.generate_program = dspy.ChainOfThought(GenerateHypothesis)

    def run(self, state: RareAgentState) -> Dict[str, Any]:
        """
        Executes the Proponent Agent workflow.
        """
        disease_name = state.get("current_disease")
        targets = state.get("genetic_targets", [])
        current_hypotheses = state.get("hypotheses", [])
        evaluated_drugs = state.get("evaluated_drugs", [])
        
        existing_drugs = [h.get("drug_name") for h in current_hypotheses]

        logger.info(f"Proponent Agent generating hypothesis for {disease_name}...")
        
        if not targets:
            logger.warning("No genetic targets found. Cannot generate specific hypothesis.")
            return {"hypotheses": current_hypotheses}

        # Convert targets to a prompt-friendly string
        targets_str = "\n".join([f"- {t.get('gene_name')} ({t.get('uniprot_id')}): {t.get('phenotype_association')}" for t in targets[:5]]) # Limit to top 5 for context window

        try:
            # Check for rejection feedback
            last_rejection_reason = state.get("last_rejection_reason")
            rejection_prompt = ""
            if last_rejection_reason:
                rejection_prompt = f"CRITICAL: Your previous hypothesis was REJECTED by the deterministic database for the following reason: '{last_rejection_reason}'. You MUST read this error and adjust your next target or rationale to completely avoid making this same mistake. Strictly select a valid target."
                logger.info("Proponent Agent applying self-correction from previous rejection.")

            # Generate Hypothesis
            # In a real app, dspy.settings.lm would be configured globally with the API key.
            # Here we assume it's set or will be mocked in tests.
            prediction = self.generate_program(
                disease_name=disease_name,
                genetic_targets=targets_str,
                existing_hypotheses=", ".join(existing_drugs) if existing_drugs else "None",
                last_rejection_reason=rejection_prompt,
                excluded_drugs=", ".join(evaluated_drugs) if evaluated_drugs else "None"
            )

            new_hypothesis = {
                "drug_name": prediction.drug_name,
                "target_gene": prediction.target_gene,
                "mechanism": prediction.mechanism,
                "rationale": prediction.rationale,
                "source": "ProponentAgent",
                "status": "PROPOSED"
            }
            
            logger.info(f"Proposed: {new_hypothesis['drug_name']} targeting {new_hypothesis['target_gene']}")
            
            # Append to state and taboo list
            updated_hypotheses = current_hypotheses + [new_hypothesis]
            updated_evaluated_drugs = evaluated_drugs + [prediction.drug_name]
            
            return {
                "hypotheses": updated_hypotheses,
                "evaluated_drugs": updated_evaluated_drugs
            }

        except Exception as e:
            logger.error(f"Proponent Agent failed: {e}")
            return {"hypotheses": current_hypotheses}

if __name__ == "__main__":
    # Test Run (Requires configured LM)
    # Using a Mock/Dummy LM for demonstration if not configured
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
        
        agent = ProponentAgent()
        state = {
            "current_disease": "Test Disease",
            "genetic_targets": [{"gene_name": "AMPK", "uniprot_id": "P12345", "phenotype_association": "Metabolic defect"}],
            "hypotheses": []
        }
        updates = agent.run(state)
        print(updates)
    except Exception as e:
        print(f"Test failed: {e}")
