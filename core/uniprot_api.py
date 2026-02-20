import requests
import time
import logging
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UniProtAPI:
    """
    Interface for UniProt REST API.
    Supports ID Mapping and Cursor-based Pagination.
    """
    API_URL = "https://rest.uniprot.org"

    def __init__(self):
        self.session = requests.Session()
        # Retry strategy could be added to session adapters here

    def _get_next_link(self, headers):
        """Parses the 'link' header to find the next page URL."""
        if "link" in headers:
            links = headers["link"]
            for link in links.split(","):
                if 'rel="next"' in link:
                    # Angle brackets might be around the URL
                    return link[link.index("<") + 1 : link.index(">")]
        return None

    def get_uniprot_data(self, query, format="json"):
        """
        Retrieves UniProt data based on a query with cursor-based pagination.
        """
        endpoint = "/uniprotkb/search"
        params = {
            "query": query,
            "format": format,
            "size": 500 # Page size
        }
        
        url = f"{self.API_URL}{endpoint}"
        all_results = []
        
        while url:
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                # Check format to determine how to append
                if format == "json":
                    data = response.json()
                    if "results" in data:
                        all_results.extend(data["results"])
                else:
                    all_results.append(response.text)

                # Get next link for pagination
                url = self._get_next_link(response.headers)
                params = {} # Params are usually part of the next link URL, so we clear them to avoid duplication
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching UniProt data: {e}")
                break
                
        return all_results

    def map_ids(self, from_db, to_db, ids):
        """
        Submits an ID Mapping job to UniProt.
        """
        endpoint = "/idmapping/run"
        data = {
            "from": from_db,
            "to": to_db,
            "ids": ",".join(ids)
        }
        
        try:
            response = self.session.post(f"{self.API_URL}{endpoint}", data=data)
            response.raise_for_status()
            return response.json()["jobId"]
        except requests.exceptions.RequestException as e:
            logger.error(f"ID Mapping submission failed: {e}")
            raise

    def get_id_mapping_results(self, job_id):
        """
        Polls for ID Mapping job status and retrieves results when ready.
        """
        status_endpoint = f"/idmapping/status/{job_id}"
        results_endpoint = f"/idmapping/results/{job_id}" # Stream endpoint might be better for large sets
        
        while True:
            try:
                response = self.session.get(f"{self.API_URL}{status_endpoint}")
                response.raise_for_status()
                status_data = response.json()
                
                if "jobStatus" in status_data:
                    if status_data["jobStatus"] == "RUNNING" or status_data["jobStatus"] == "NEW":
                        logger.info(f"Job {job_id} is running...")
                        time.sleep(2)
                        continue
                    elif status_data["jobStatus"] == "FINISHED":
                        logger.info(f"Job {job_id} finished. Fetching results...")
                        break
                    elif status_data["jobStatus"] == "FAILED":
                        raise Exception(f"Job {job_id} failed.")
                else:
                     logger.warning("Unknown status response.")
                     break
                     
            except requests.exceptions.RequestException as e:
                 logger.error(f"Error checking job status: {e}")
                 raise

        # Fetch results with pagination handling
        # Results endpoint also supports pagination
        url = f"{self.API_URL}{results_endpoint}"
        all_results = []
        
        while url:
            try:
                response = self.session.get(url) # Params often in next link
                response.raise_for_status()
                data = response.json()
                
                if "results" in data:
                    all_results.extend(data["results"])
                
                url = self._get_next_link(response.headers)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching mapping results: {e}")
                break
                
        return all_results

if __name__ == "__main__":
    api = UniProtAPI()
    # Example: Search for BRCA1
    results = api.get_uniprot_data("gene:BRCA1 AND organism_id:9606")
    print(f"Found {len(results)} entries for BRCA1.")
    
    # Example: ID Mapping (UniProtKB AC -> Gene Name)
    try:
        job = api.map_ids("UniProtKB_AC-ID", "Gene_Name", ["P12345", "P04637"])
        print(f"Job ID: {job}")
        mapped = api.get_id_mapping_results(job)
        print("Mapped Results:", mapped)
    except Exception as e:
        print(f"Mapping failed: {e}")
