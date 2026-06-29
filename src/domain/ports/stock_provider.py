from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd

class StockDataProvider(ABC):
    """Port interface for fetching stock data from external sources."""
    
    @abstractmethod
    def get_historical_prices(self, ticker: str, days: int) -> pd.DataFrame:
        """
        Fetches historical price bars for the given ticker.
        Returns a pandas DataFrame with datetime index and columns: open, high, low, close, volume.
        """
        pass

    @abstractmethod
    def get_financial_ratios(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches core valuation and profitability ratios (P/E, P/B, ROE, ROA, EPS, etc.).
        Returns a dictionary.
        """
        pass

    @abstractmethod
    def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches basic company metadata (industry, description, capital size).
        Returns a dictionary.
        """
        pass
