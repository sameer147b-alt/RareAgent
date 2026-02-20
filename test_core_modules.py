import sys
import os

# Ensure core modules can be imported
sys.path.append(os.getcwd())

from core.pubchem_api import PubChemAPI
from core.ncbi_entrez import NCBIEntrezAPI
from core.uniprot_api import UniProtAPI
from orchestrator import semantic_compression

def test_pubchem():
    print("\n--- Testing PubChem API ---")
    api = PubChemAPI()
    try:
        data = api.get_compound_by_name("aspirin")
        cid = data['PC_Compounds'][0]['id']['id']['cid']
        print(f"Success: Retrieved Aspirin CID: {cid}")
    except Exception as e:
        print(f"PubChem Test Failed: {e}")

def test_ncbi():
    print("\n--- Testing NCBI Entrez API ---")
    api = NCBIEntrezAPI(email="test@example.com")
    try:
        # Search minimal to be fast
        search = api.search_pubmed("drug repurposing[Title]", retmax=5)
        count = search['esearchresult']['count']
        print(f"Success: Found {count} articles")
        
        # Test basic fetch
        ids = search['esearchresult']['idlist']
        if ids:
            details = api.fetch_details(ids[:2])
            print(f"Success: Fetched details for {len(details)} chunks")
    except Exception as e:
        print(f"NCBI Test Failed: {e}")

def test_uniprot():
    print("\n--- Testing UniProt API ---")
    api = UniProtAPI()
    try:
        # Search minimal
        results = api.get_uniprot_data("gene:TP53 AND organism_id:9606")
        print(f"Success: Found {len(results)} entries for TP53")
    except Exception as e:
        print(f"UniProt Test Failed: {e}")

def test_orchestrator_helper():
    print("\n--- Testing Orchestrator Helper ---")
    data = {"key": "value", "list": [1, 2, 3]}
    compressed = semantic_compression(data)
    print(f"Success: Compressed data: {compressed}")

if __name__ == "__main__":
    test_pubchem()
    test_ncbi()
    test_uniprot()
    test_orchestrator_helper()
