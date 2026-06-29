from abc import ABC, abstractmethod
from typing import List, Dict, Any

class SentimentAnalyzer(ABC):
    """Port interface for natural language sentiment analysis (e.g. using FinBERT)."""

    @abstractmethod
    def analyze_sentiment(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyzes the sentiment of a list of text snippets.
        Returns a list of dictionaries containing:
        - 'label': 'positive' | 'negative' | 'neutral'
        - 'score': float (the model confidence or mapped sentiment score)
        """
        pass
