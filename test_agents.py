import sys
import os

sys.path.append(os.getcwd())

from agents.explorer import ExplorerAgent
from agents.validator import ValidatorAgent

def test_agents():
    print("\n--- Testing Explorer Agent ---")
    explorer = ExplorerAgent()
    state = {"current_disease": "Cystic Fibrosis"}
    
    updates = explorer.run(state)
    targets = updates.get("genetic_targets", [])
    print(f"Explorer found {len(targets)} targets.")
    if targets:
        print(f"Top target: {targets[0]['gene_name']} ({targets[0]['uniprot_id']})")
        # Ensure CFTR is in there for CF
        found_cftr = any(t['gene_name'] == 'CFTR' for t in targets)
        print(f"CFTR found: {found_cftr}")

    print("\n--- Testing Validator Agent ---")
    validator = ValidatorAgent()
    
    # Mock some hypotheses
    state_v = {
        "current_disease": "Cystic Fibrosis",
        "hypotheses": [
            # Real One (Ivacaftor targets CFTR, CFTR is linked to CF)
            {"drug_name": "Ivacaftor", "target_gene": "CFTR", "mechanism": "Potentiator"},
            # Bad Drug
            {"drug_name": "NonExistentDrugXYZ", "target_gene": "CFTR", "mechanism": "Magic"},
            # Bad Link (Aspirin -> BRCA1 is fine, but BRCA1 is not linked to CF in UniProt comments usually)
            {"drug_name": "Aspirin", "target_gene": "BRCA1", "mechanism": "Inhibition"}
        ]
    }
    
    updates_v = validator.run(state_v)
    for h in updates_v["hypotheses"]:
        status = h["validation"]["overall_status"]
        reason = h["validation"]["reason"]
        print(f"Hypothesis: {h['drug_name']} -> {h['target_gene']} | Status: {status} | Reason: {reason}")

if __name__ == "__main__":
    test_agents()
