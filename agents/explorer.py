from typing import Dict, Any, List
import logging
import random
from core.ncbi_entrez import NCBIEntrezAPI
from core.uniprot_api import UniProtAPI
# Assuming RareAgentState is importable from orchestrator or a common types file
# For now, we'll redefine or import it if we separate it. 
# Ideally, we should have a `core/types.py` or similar, but I'll import from orchestrator
from core.types import RareAgentState

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExplorerAgent:
    """
    Explorer Agent: Gathers multi-omics data for a given orphan disease.
    Implements 'Guilt-by-Association' logic to identify targets.
    """
    def __init__(self):
        self.ncbi_api = NCBIEntrezAPI()
        self.uniprot_api = UniProtAPI()

    def run(self, state: RareAgentState) -> Dict[str, Any]:
        """
        Executes the Explorer Agent workflow.
        Returns a dictionary with state updates.
        """
        disease_name = state.get("current_disease")
        if not disease_name:
            logger.error("No disease specified in state.")
            return {"evidence": [], "genetic_targets": []}

        logger.info(f"Explorer Agent started for disease: {disease_name}")

        # 1. Search PubMed for the disease to get context (and potentially key genes mentioned in titles/abstracts)
        # For this version, we'll focus on getting UIDs to establish "evidence" foundation.
        logger.info("Step 1: Gathering literature evidence...")
        try:
            search_res = self.ncbi_api.search_pubmed(f"{disease_name}[Title/Abstract]", retmax=50) # Limit for demo
            uids = search_res.get("esearchresult", {}).get("idlist", [])
            evidence = [{"source": "PubMed", "id": uid, "note": f"Linked to {disease_name}"} for uid in uids]
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            evidence = []

        # 2. Identify associated targets (Guilt-by-Association) using UniProt
        # We search UniProt for proteins associated with the disease name.
        # This mocks the "guilt" part by finding proteins that *are* the disease mechanism or closely related.
        logger.info("Step 2: Identifying associated targets (Guilt-by-Association)...")
        genetic_targets = []
        try:
            # Query UniProt for human proteins related to the disease
            query = f'(cc_disease:"{disease_name}") AND organism_id:9606 AND reviewed:true'
            proteins = self.uniprot_api.get_uniprot_data(query, format="json")
            
            for prot in proteins:
                # Extract Gene Name and Primary Accession
                primary_accession = prot.get("primaryAccession")
                genes = prot.get("genes", [])
                gene_name = genes[0].get("geneName", {}).get("value") if genes else "Unknown"
                
                # Extract Disease Comments (Phenotypes/Mechanism)
                comments = prot.get("comments", [])
                disease_comment = next((c for c in comments if c.get("commentType") == "DISEASE"), None)
                phenotype = disease_comment.get("note", {}).get("text") if disease_comment else "No specific phenotype description."

                target_info = {
                    "gene_name": gene_name,
                    "uniprot_id": primary_accession,
                    "protein_name": prot.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value"),
                    "phenotype_association": phenotype
                }
                genetic_targets.append(target_info)
                
        except Exception as e:
             logger.error(f"UniProt search failed: {e}")

        logger.info(f"Found {len(genetic_targets)} potential genetic targets.")
        
        # Shuffle targets to ensure the Proponent sees a randomized priority list on every run
        if genetic_targets:
            random.shuffle(genetic_targets)

        # Update State
        # In a real LangGraph, we'd append or merge. Here we return the updates.
        return {
            "evidence": evidence, # Append logic would be handled by the graph reducer usually
            "genetic_targets": genetic_targets, # New field for state
            # We don't generate hypotheses yet; that's for the Proponent agent (future).
        }

if __name__ == "__main__":
    # Test Run
    agent = ExplorerAgent()
    mock_state = {"current_disease": "Cystic Fibrosis"}
    updates = agent.run(mock_state)
    print(f"Updates keys: {updates.keys()}")
    print(f"Targets found: {len(updates.get('genetic_targets', []))}")
    if updates.get('genetic_targets'):
        print(f"Sample Target: {updates['genetic_targets'][0]}")
