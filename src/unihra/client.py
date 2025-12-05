import json
import requests
from typing import List, Generator, Dict, Any, Literal, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Optional dependency: tqdm (for progress bars)
try:
    from tqdm.auto import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from .exceptions import (
    UnihraError, UnihraApiError, UnihraConnectionError, 
    UnihraValidationError, UnihraDependencyError, raise_for_error_code
)

BASE_URL = "https://unihra.ru"
ACTION_MAP = {
    "Добавить": "add",
    "Увеличить": "increase",
    "Уменьшить": "decrease",
    "Ок": "ok"
}

class UnihraClient:
    """
    Official Python Client for Unihra API.
    
    Features:
    - Automatic SSE stream handling.
    - Response normalization (converts API keys to snake_case).
    - Smart retries for network stability.
    - Pandas and Excel export integration (Multi-sheet support).
    - Visual progress bars for Jupyter/Console.
    """

    def __init__(self, api_key: str, base_url: str = BASE_URL, max_retries: int = 0):
        """
        Initialize the client.

        :param api_key: Your API key.
        :param base_url: Base URL for the API.
        :param max_retries: Number of retries for failed requests (429/50x). 
                            Default is 0 (fail fast). Set to 3-5 for production.
        """
        self.base_url = base_url.rstrip('/')
        self.api_v1 = f"{self.base_url}/api/v1"
        self.session = requests.Session()
        
        # Standard headers
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "UnihraPythonSDK/1.2.0"
        })

        # Configure Smart Retries (Exponential Backoff)
        if max_retries > 0:
            retry_strategy = Retry(
                total=max_retries,
                backoff_factor=2,  # Wait 2s, 4s, 8s...
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST", "GET"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)

    def health(self) -> Dict[str, Any]:
        """Check API service availability."""
        try:
            resp = self.session.get(f"{self.api_v1}/health")
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise UnihraConnectionError(f"Health check failed: {e}")

    def analyze(
        self, 
        own_page: str, 
        competitors: List[str], 
        lang: Literal['ru', 'en'] = 'ru',
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Run a full SEO analysis (Synchronous).
        Blocks execution until the task is complete.

        :param own_page: URL of the target page.
        :param competitors: List of competitor URLs.
        :param lang: Language code ('ru' or 'en').
        :param verbose: If True, displays a progress bar (requires 'tqdm').
        :return: Dictionary containing the analysis result with normalized keys.
        """
        last_event = {}
        
        # Setup Progress Bar
        pbar = None
        if verbose:
            if TQDM_AVAILABLE:
                # 0 to 100%
                pbar = tqdm(total=100, desc="Analyzing SEO", unit="%")
            else:
                print("Note: Install 'tqdm' to see a visual progress bar.")

        try:
            for event in self.analyze_stream(own_page, competitors, lang):
                last_event = event
                
                # Update Progress Bar
                if pbar:
                    state = event.get("state")
                    progress = event.get("progress", 0)
                    
                    if isinstance(progress, (int, float)):
                        pbar.n = int(progress)
                        pbar.refresh()
                    
                    if state == "PROCESSING":
                        pbar.set_description(f"Processing ({progress}%)")
                    elif state == "SUCCESS":
                        pbar.set_description("Completed ✅")
                        pbar.n = 100
                        pbar.refresh()

                if event.get("state") == "SUCCESS":
                    return event.get("result", {})
                    
        except Exception as e:
            if pbar: 
                pbar.set_description("Failed ❌")
                pbar.close()
            raise e
        finally:
            if pbar: 
                pbar.close()
        
        return last_event

    def analyze_stream(
        self, 
        own_page: str, 
        competitors: List[str], 
        lang: str = 'ru'
    ) -> Generator[Dict, None, None]:
        """
        Generator method for real-time updates.
        Yields SSE events as dictionaries.
        
        Automatically normalizes API keys (e.g. 'Block Comparison' -> 'block_comparison').
        """
        # 1. Validation
        if not competitors:
            raise UnihraValidationError("Competitor list cannot be empty.")

        payload = {
            "own_page": own_page, 
            "competitor_urls": competitors, 
            "lang": lang
        }

        try:
            # 2. Create Task
            resp = self.session.post(f"{self.api_v1}/process", json=payload)
            
            if resp.status_code == 401:
                raise UnihraApiError("Invalid API Key or unauthorized access", code=401)
            resp.raise_for_status()
            
            task_id = resp.json().get("task_id")
            if not task_id:
                raise UnihraApiError("API response missing 'task_id'")

            # 3. Stream Results
            stream_url = f"{self.api_v1}/process/status/{task_id}"
            
            with self.session.get(stream_url, stream=True) as s_resp:
                s_resp.raise_for_status()
                
                for line in s_resp.iter_lines():
                    if not line: 
                        continue
                    
                    if line.startswith(b'data: '):
                        try:
                            # Decode SSE JSON
                            decoded_line = line[6:].decode('utf-8')
                            data = json.loads(decoded_line)
                            state = data.get("state")
                            
                            # --- ERROR HANDLING ---
                            if state == "FAILURE":
                                # Handle nested error object: {"error": {"code": 1003}}
                                error_obj = data.get("error")
                                if isinstance(error_obj, dict):
                                    code = error_obj.get("code", 9999)
                                    msg = error_obj.get("message", "Unknown error")
                                else:
                                    # Handle flat structure
                                    code = data.get("error_code", 9999)
                                    msg = data.get("message", "Unknown error")

                                raise_for_error_code(code, msg, data)
                            
                            if state == "SUCCESS":
                                raw_result = data.get("result", {})
                                normalized_result = self._normalize_keys(raw_result)
                                if lang == 'en':
                                    final_result = self._translate_action_values(normalized_result)
                                else:
                                    final_result = normalized_result

                                data["result"] = final_result
                                yield data
                                break
                            
                            yield data
                                
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.RetryError:
            raise UnihraConnectionError("Max retries exceeded. The service might be temporarily unavailable.")
        except requests.exceptions.RequestException as e:
            raise UnihraConnectionError(f"Network error: {e}")

    def _normalize_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper to convert API keys to Pythonic snake_case.
        Example: 'Block Comparison' -> 'block_comparison'
        """
        new_data = {}
        for key, value in data.items():
            new_key = key.lower().replace(" ", "_")
            new_data[new_key] = value
        return new_data

    def _translate_action_values(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Translates 'action_needed' values from Russian to English."""
        if "block_comparison" in result and isinstance(result["block_comparison"], list):
            for item in result["block_comparison"]:
                if "action_needed" in item:
                    russian_action = item["action_needed"]
                    # Use .get() to safely handle unknown values from API
                    item["action_needed"] = ACTION_MAP.get(russian_action, russian_action)
        return result

    def get_dataframe(self, result: Dict[str, Any], section: str = "block_comparison"):
        """
        Convert a specific result section to a Pandas DataFrame.
        
        :param result: The dictionary returned by .analyze()
        :param section: 'block_comparison', 'ngrams_analysis', etc.
        :return: pandas.DataFrame
        """
        try:
            import pandas as pd
        except ImportError:
            raise UnihraDependencyError("Pandas is not installed. Run: pip install pandas")

        # Normalize section name just in case user passes "Block Comparison"
        normalized_section = section.lower().replace(" ", "_")
        data = result.get(normalized_section, [])
        return pd.DataFrame(data)

    def save_report(self, result: Dict[str, Any], filename: str = "report.xlsx"):
        """
        Save the full analysis result to a file.
        Includes Block Comparison, N-Grams, and DrMaxs.
        """
        try:
            import pandas as pd
        except ImportError:
            raise UnihraDependencyError("Pandas is required. Run: pip install pandas openpyxl")

        df_blocks = pd.DataFrame(result.get("block_comparison", []))
        ngrams_data = result.get("ngrams_analysis") or result.get("n-grams_analysis") or []
        df_ngrams = pd.DataFrame(ngrams_data)
        drmaxs_data = result.get("drmaxs", {})

        if filename.endswith(".csv"):
            df_blocks.to_csv(filename, index=False, encoding='utf-8-sig')
        else:
            try:
                import openpyxl
            except ImportError:
                raise UnihraDependencyError("Library 'openpyxl' is required for Excel export.")

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                if not df_blocks.empty:
                    df_blocks.to_excel(writer, sheet_name="Word Analysis", index=False)
                if not df_ngrams.empty:
                    df_ngrams.to_excel(writer, sheet_name="N-Grams", index=False)
                if drmaxs_data and isinstance(drmaxs_data, dict):
                    for subkey, subdata in drmaxs_data.items():
                        if subdata and isinstance(subdata, list):
                            df_dr = pd.DataFrame(subdata)
                            safe_name = subkey.replace("_", " ").title()
                            sheet_name = f"DrMaxs {safe_name}"[:31]
                            df_dr.to_excel(writer, sheet_name=sheet_name, index=False)