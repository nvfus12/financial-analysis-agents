from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g. FPT, VNM, AAPL")
    market: str = Field("VN", description="Market identifier: 'VN' or 'US'")
    analysis_mode: str = Field("full", description="Analysis mode: 'full', 'technical', or 'fundamental'")
    pdf_path: Optional[str] = Field(None, description="Optional path to uploaded financial PDF report")
    report_language: str = Field("vi", description="Report output language: 'vi' or 'en'")

class AnalysisResponse(BaseModel):
    ticker: str
    market: str
    analysis_mode: str
    final_recommendation: str
    final_report_markdown: str
    fundamental_insights: Optional[str] = None
    technical_insights: Optional[str] = None
    sentiment_insights: Optional[str] = None
    technical_signals: Dict[str, Any] = Field(default_factory=dict)
    critic_passed: bool = True
    reflection_count: int = 0
    logs: List[str] = Field(default_factory=list)

class HistoryItemResponse(BaseModel):
    id: int
    ticker: str
    market: str
    analysis_mode: str
    recommendation: str
    created_at: str
    report_markdown: str

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
