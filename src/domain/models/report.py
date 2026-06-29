from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class Recommendation(str, Enum):
    """Enumeration representing stock investment recommendations."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass(frozen=True)
class AnalysisReport:
    """Domain model representing a compiled stock analysis report."""
    ticker: str
    analysis_mode: str              # 'full' | 'technical' | 'fundamental'
    recommendation: Recommendation
    report_markdown: str            # Fully generated analysis report body
    created_at: datetime
