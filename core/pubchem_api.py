import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PubChemAPI:
    """
    Interface for the PubChem PUG REST API with robust rate limiting and error handling.
    Respects the 5 requests per second limit.
    """
    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 0.25  # 1/4 second to be safe (max 4 req/s to stay comfortably under 5)

    def _wait_for_rate_limit(self):
        """Ensures we don't exceed the rate limit."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_request(self, endpoint, params=None, method="GET", data=None):
        """
        Internal method to make HTTP requests with retry logic for 429 and 503 errors.
        """
        url = f"{self.BASE_URL}{endpoint}"
        retries = 0
        max_retries = 5
        backoff_factor = 2

        while retries < max_retries:
            self._wait_for_rate_limit()
            try:
                if method == "GET":
                    response = requests.get(url, params=params)
                elif method == "POST":
                    response = requests.post(url, data=data, params=params)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # Check for rate limiting or service unavailable
                if response.status_code in [429, 503]:
                    wait_time = backoff_factor ** retries
                    logger.warning(f"Received {response.status_code}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                    continue
                
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if retries == max_retries - 1:
                    raise
                wait_time = backoff_factor ** retries
                time.sleep(wait_time)
                retries += 1

    def get_compound_by_name(self, name):
        """Retrieves compound data by name."""
        endpoint = f"/compound/name/{name}/JSON"
        response = self._make_request(endpoint)
        return response.json()

    def get_compound_cids(self, name):
        """Retrieves CIDs for a given compound name."""
        endpoint = f"/compound/name/{name}/cids/JSON"
        response = self._make_request(endpoint)
        return response.json()

    def get_assay_summaries(self, cid):
        """Retrieves assay summaries for a given CID."""
        endpoint = f"/compound/cid/{cid}/assaysummary/JSON"
        response = self._make_request(endpoint)
        return response.json()

if __name__ == "__main__":
    # Example usage
    api = PubChemAPI()
    try:
        data = api.get_compound_by_name("aspirin")
        print("Successfully retrieved data for aspirin")
        cids = api.get_compound_cids("aspirin")
        print(f"CIDs: {cids}")
    except Exception as e:
        print(f"Failed to retrieve data: {e}")
