from abc import ABC, abstractmethod
from typing import List, Dict, Any

class NewsProvider(ABC):
    """Port interface for fetching market and company news."""

    @abstractmethod
    def fetch_latest_news(self, ticker: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Fetches news articles related to the given stock ticker.
        Returns a list of dictionaries with keys: title, url, source, published_at, content_snippet.
        """
        pass
