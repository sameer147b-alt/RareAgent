import requests
import time
import logging
from xml.etree import ElementTree

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NCBIEntrezAPI:
    """
    Interface for NCBI E-utilities (PubMed) with History Server and pagination support.
    """
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email="email@example.com", tool="OtherAgent"):
        self.params = {
            "db": "pubmed",
            "email": email,
            "tool": tool,
            "retmode": "json" 
        }

    def search_pubmed(self, term, retmax=1000):
        """
        Searches PubMed for a term and returns UIDs.
        Uses ESearch.
        """
        endpoint = f"{self.BASE_URL}/esearch.fcgi"
        params = self.params.copy()
        params.update({
            "term": term,
            "usehistory": "y",
            "retmax": retmax
        })
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    def fetch_details(self, uids_or_history, retmax=500):
        """
        Fetches full details for a list of UIDs or a history object.
        Uses EFetch with pagination.
        Handles the 10k record limit using retstart/retmax.
        """
        endpoint = f"{self.BASE_URL}/efetch.fcgi"
        
        # Determine if we are using a list of UIDs or history parameters
        request_params = self.params.copy()
        request_params["retmode"] = "xml"  # EFetch often returns XML better for full records
        
        count = 0 
        web_env = None
        query_key = None

        if isinstance(uids_or_history, dict) and "esearchresult" in uids_or_history:
             # It's a history object from search_pubmed
            res = uids_or_history["esearchresult"]
            if "webenv" in res and "querykey" in res:
                web_env = res["webenv"]
                query_key = res["querykey"]
                count = int(res["count"])
                request_params.update({
                    "WebEnv": web_env,
                    "query_key": query_key
                })
            else:
                 # Just a list of IDs in the search result
                 uids = res.get("idlist", [])
                 count = len(uids)
                 request_params["id"] = ",".join(uids)

        elif isinstance(uids_or_history, list):
             # List of UIDs
             count = len(uids_or_history)
             request_params["id"] = ",".join(uids_or_history)
             
             # If too many UIDs for GET, we should ideally use POST (not implemented for simplicity here unless needed)
             # But for pagination context, usually we use History.

        # Pagination loop
        results = []
        for retstart in range(0, count, retmax):
            logger.info(f"Fetching records {retstart} to {min(retstart + retmax, count)} of {count}...")
            
            chunk_params = request_params.copy()
            chunk_params.update({
                "retstart": retstart,
                "retmax": retmax
            })
            
            try:
                response = requests.get(endpoint, params=chunk_params)
                response.raise_for_status()
                # For now, just appending raw text/xml content. A real parser would process XML.
                results.append(response.text)
                
                # Respect potential rate limits (3 requests/sec without API key, 10 w/ key)
                time.sleep(0.34) 
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching chunk {retstart}: {e}")
                continue

        return results

if __name__ == "__main__":
    api = NCBIEntrezAPI()
    try:
        search_res = api.search_pubmed("cystic fibrosis[Title]", retmax=100)
        print(f"Found {search_res['esearchresult']['count']} articles.")
        
        # Fetching details using the search result (history)
        details = api.fetch_details(search_res, retmax=50) 
        print(f"Retrieved {len(details)} chunks of data.")
    except Exception as e:
        print(f"Error: {e}")
