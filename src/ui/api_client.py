import os
import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

# Base API URL (can be overridden via environment variable API_BASE_URL)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def check_backend_health() -> bool:
    """
    Checks if FastAPI backend server is online and responding.
    Fast 0.5s timeout prevents Streamlit UI from lagging when server is off.
    """
    try:
        res = requests.get(f"{API_BASE_URL}/health", timeout=0.5)
        return res.status_code == 200
    except Exception:
        return False

def run_analysis_api(
    ticker: str,
    market: str = "VN",
    analysis_mode: str = "full",
    pdf_path: Optional[str] = None,
    report_language: str = "vi"
) -> Dict[str, Any]:
    """
    Sends HTTP POST request to FastAPI backend /api/v1/analyze endpoint.
    """
    url = f"{API_BASE_URL}/api/v1/analyze"
    payload = {
        "ticker": ticker,
        "market": market,
        "analysis_mode": analysis_mode,
        "pdf_path": pdf_path or "",
        "report_language": report_language
    }
    
    try:
        logger.info(f"Sending REST API request to {url} for ticker {ticker}...")
        # 120s timeout to allow full multi-agent reflection workflow
        res = requests.post(url, json=payload, timeout=120)
        
        if res.status_code == 200:
            return res.json()
        else:
            detail = res.json().get("detail", res.text) if res.content else f"HTTP {res.status_code}"
            raise RuntimeError(f"API Request Failed ({res.status_code}): {detail}")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to FastAPI Backend at {API_BASE_URL}. "
            f"Please ensure the backend server is running using: 'uvicorn src.api.main:app --port 8000'"
        )
    except Exception as e:
        logger.error(f"Error calling Analysis API: {e}")
        raise e

def get_history_api(limit: int = 15) -> List[Dict[str, Any]]:
    """
    Sends HTTP GET request to FastAPI backend /api/v1/history endpoint.
    """
    url = f"{API_BASE_URL}/api/v1/history"
    try:
        res = requests.get(url, params={"limit": limit}, timeout=5)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception as e:
        logger.warning(f"Error fetching history from REST API: {e}")
        return []

def get_history_detail_api(history_id: int) -> Optional[Dict[str, Any]]:
    """
    Sends HTTP GET request to FastAPI backend /api/v1/history/{id} endpoint.
    """
    url = f"{API_BASE_URL}/api/v1/history/{history_id}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        logger.warning(f"Error fetching history detail from REST API: {e}")
        return None

def delete_history_api(history_id: int) -> bool:
    """
    Sends HTTP DELETE request to FastAPI backend /api/v1/history/{id} endpoint.
    """
    url = f"{API_BASE_URL}/api/v1/history/{history_id}"
    try:
        res = requests.delete(url, timeout=5)
        return res.status_code == 200
    except Exception as e:
        logger.warning(f"Error deleting history item via REST API: {e}")
        return False
