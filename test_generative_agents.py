import sys
import os
import dspy

sys.path.append(os.getcwd())

from agents.proponent import ProponentAgent
from agents.skeptic import SkepticAgent

def test_generative_agents():
    print("\n--- Testing Generative Agents with Mock LM ---")
    
    # Mock LM Responses
    # 1. Response for Proponent
    proponent_response = {
        "drug_name": "Rapamycin", 
        "target_gene": "mTOR", 
        "mechanism": "Inhibitor", 
        "rationale": "Inhibits mTOR pathway which is overactive in this disease."
    }
    # 2. Response for Skeptic
    skeptic_response = {
        "critique": "Rapamycin has significant immunosuppressive side effects.", 
        "safety_concerns": "Immunosuppression, interstitial lung disease.", 
        "verdict": "RISKY"
    }
    
    # Configure dspy with Groq LM
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        print("WARNING: GROQ_API_KEY not found! Please check your .env file.")
        raise ValueError("GROQ_API_KEY environment variable not set")
    lm = dspy.LM(model='groq/llama-3.3-70b-versatile', api_key=api_key)
    dspy.settings.configure(lm=lm)

    # 1. Test Proponent
    print("Run Proponent...")
    proponent = ProponentAgent()
    state = {
        "current_disease": "Tuberous Sclerosis",
        "genetic_targets": [{"gene_name": "mTOR", "uniprot_id": "P42345", "phenotype_association": "Overactivation"}],
        "hypotheses": [],
        "debate_history": []
    }
    
    updates_p = proponent.run(state)
    hypotheses = updates_p.get("hypotheses", [])
    
    if hypotheses:
        print(f"Proponent generated: {hypotheses[0]['drug_name']}")
        state["hypotheses"] = hypotheses # Update mock state
    else:
        print("Proponent generated nothing.")

    # 2. Test Skeptic
    print("\nRun Skeptic...")
    skeptic = SkepticAgent()
    
    updates_s = skeptic.run(state)
    history = updates_s.get("debate_history", [])
    hypotheses_s = updates_s.get("hypotheses", [])
    
    if history:
        print("Skeptic Critique added to history:")
        print(history[0])
    
    if hypotheses_s:
         print(f"Hypothesis Verdict: {hypotheses_s[0].get('skeptic_verdict')}")

if __name__ == "__main__":
    try:
        test_generative_agents()
    except Exception as e:
        print(f"Test failed: {e}")
