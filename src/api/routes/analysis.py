import os
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from src.api.schemas import AnalysisResponse
from src.domain.services.validation_service import ValidationService
from src.agents.graph import build_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# Compile LangGraph engine instance
graph = build_graph()

os.makedirs("data/uploads", exist_ok=True)

@router.post("/analyze", response_model=AnalysisResponse)
async def run_analysis(
    ticker: str = Form(...),
    market: str = Form("VN"),
    analysis_mode: str = Form("full"),
    report_language: str = Form("vi"),
    pdf_file: Optional[UploadFile] = File(None)
):
    """
    Executes the multi-agent reasoning graph for the given ticker.
    Supports VN and US markets, RAG PDF context with ValidationService, and Smart Reflection Audit.
    """
    clean_ticker = ticker.strip().upper()
    
    # 🟢 1. Validate Stock Ticker Format
    is_valid_ticker, ticker_err = ValidationService.validate_ticker(clean_ticker, market)
    if not is_valid_ticker:
        raise HTTPException(status_code=400, detail=ticker_err)

    # 🟢 2. Save and Validate PDF File if uploaded
    pdf_temp_path = ""
    if pdf_file is not None and pdf_file.filename:
        filename = f"{clean_ticker}_{uuid.uuid4().hex[:6]}.pdf"
        pdf_temp_path = os.path.join("data/uploads", filename)
        
        contents = await pdf_file.read()
        with open(pdf_temp_path, "wb") as f:
            f.write(contents)
            
        is_valid_pdf, pdf_err = ValidationService.validate_pdf(pdf_temp_path)
        if not is_valid_pdf:
            # Clean up invalid PDF file
            if os.path.exists(pdf_temp_path):
                os.remove(pdf_temp_path)
            raise HTTPException(status_code=400, detail=pdf_err)
            
        logger.info(f"Validated PDF file {pdf_file.filename} saved to {pdf_temp_path}")

    # 🟢 3. Execute LangGraph Engine
    session_id = str(uuid.uuid4())
    initial_state = {
        "ticker": clean_ticker,
        "market": market.strip().upper(),
        "analysis_mode": analysis_mode.strip().lower(),
        "pdf_path": pdf_temp_path,
        "report_language": report_language.strip().lower(),
        "logs": []
    }
    
    try:
        logger.info(f"Triggering multi-agent graph analysis for {clean_ticker} (Session ID: {session_id})...")
        final_state = graph.invoke(initial_state, config={"configurable": {"thread_id": session_id}})
        
        return AnalysisResponse(
            ticker=final_state.get("ticker", clean_ticker),
            market=final_state.get("market", market),
            analysis_mode=final_state.get("analysis_mode", analysis_mode),
            final_recommendation=final_state.get("final_recommendation", "HOLD"),
            final_report_markdown=final_state.get("final_report_markdown", "# Error\nNo report generated."),
            fundamental_insights=final_state.get("fundamental_insights"),
            technical_insights=final_state.get("technical_insights"),
            sentiment_insights=final_state.get("sentiment_insights"),
            technical_signals=final_state.get("technical_signals", {}),
            critic_passed=final_state.get("critic_passed", True),
            reflection_count=final_state.get("reflection_count", 0),
            logs=final_state.get("logs", [])
        )
    except Exception as e:
        logger.error(f"Multi-agent graph invocation failed for {clean_ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis engine execution failed: {str(e)}")
