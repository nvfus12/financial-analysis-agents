from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class NewsArticle:
    """Domain model representing a scraped news article."""
    title: str
    url: str
    source: str
    content_snippet: Optional[str] = None
    published_at: Optional[str] = None

@dataclass(frozen=True)
class SentimentResult:
    """Domain model representing the sentiment analysis output."""
    label: str   # 'positive' | 'negative' | 'neutral'
    score: float # Mapped numerical value between [-1.0, 1.0]
