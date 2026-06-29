from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CompanyProfile:
    """Domain representation of basic company metadata."""
    ticker: str
    name: str
    industry: str
    description: str
    capital_size: float  # In Billions VND

@dataclass(frozen=True)
class FinancialRatio:
    """Domain representation of core financial metrics and ratios."""
    pe: Optional[float] = None
    pb: Optional[float] = None
    roe: Optional[float] = None          # Return on Equity (as decimal, e.g. 0.15)
    roa: Optional[float] = None          # Return on Assets
    eps: Optional[float] = None          # Earnings Per Share
    debt_to_equity: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
