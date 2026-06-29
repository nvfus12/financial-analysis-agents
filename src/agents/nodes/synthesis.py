import re
import logging
from typing import Dict, Any
from src.domain.models.state import AgentState
from src.domain.models.report import Recommendation
from src.infrastructure.database.cache_repo import save_analysis_report
from src.infrastructure.adapters.gemini_adapter import GeminiAdapter
from src.infrastructure.config import Config
from src.agents.prompts import SYNTHESIS_SYSTEM_INSTRUCTION, SYNTHESIS_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

def synthesis_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesis Analyst Node (CIO).
    Combines insights from Fundamental, Technical, and Sentiment Analysts,
    uses Gemini 1.5 Pro to synthesize them into a final investment recommendation,
    and persists the output report.
    """
    ticker = state.get("ticker", "").strip().upper()
    mode = state.get("analysis_mode", "full")
    logs = state.get("logs", [])
    
    logs.append(f"[Synthesis Node] Starting final CIO synthesis report for {ticker}.")
    
    # 1. Gather intermediate insights
    fund_insights = state.get("fundamental_insights", "No fundamental analysis conducted.")
    tech_insights = state.get("technical_insights", "No technical analysis conducted.")
    sent_insights = state.get("sentiment_insights", "No sentiment analysis conducted.")
    
    # Get current price
    tech_signals = state.get("technical_signals", {})
    curr_price = tech_signals.get("current_price", 0.0)
    price_str = f"{curr_price:,.2f} VND" if curr_price > 0 else "Not Available"

    # 2. Call Gemini 1.5 Pro for Synthesis (Deep Reasoning)
    try:
        # Use pro model for final summary & recommendation
        adapter = GeminiAdapter(model_name=Config.LLM_MODEL_NAME_PRO)
        
        prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
            ticker=ticker,
            current_price=price_str,
            fundamental_insights=fund_insights,
            technical_insights=tech_insights,
            sentiment_insights=sent_insights
        )
        
        lang = state.get("report_language", "vi")
        lang_directive = "\n\nCRITICAL: You must write the entire output analysis and final report in Vietnamese. Keep the format EXACTLY like specified, but write all text descriptions in Vietnamese." if lang == "vi" else "\n\nCRITICAL: You must write the entire output analysis and final report in English. Keep the format EXACTLY like specified, but write all text descriptions in English."
        prompt += lang_directive
        
        report_markdown = adapter.generate_text(
            system_instruction=SYNTHESIS_SYSTEM_INSTRUCTION,
            prompt=prompt,
            temperature=0.3 # Slightly higher temperature for qualitative summary
        )
        
        # 3. Extract recommendation (BUY, SELL, HOLD) using regex
        recommendation = Recommendation.HOLD # Default fallback
        
        # Look for pattern: Recommendation: BUY or similar in the text
        match = re.search(r"Recommendation:\s*\**\s*(BUY|SELL|HOLD)", report_markdown, re.IGNORECASE)
        if match:
            recommendation = Recommendation(match.group(1).upper())
            logs.append(f"[Synthesis Node] Decoded recommendation: {recommendation.value}")
        else:
            # Fallback regex lookups
            if "BUY" in report_markdown.upper()[:1000]: # Check in top section
                recommendation = Recommendation.BUY
            elif "SELL" in report_markdown.upper()[:1000]:
                recommendation = Recommendation.SELL
            logs.append(f"[Synthesis Node] Recommendation tag not matched. Defaulting from content scanning to: {recommendation.value}")

        # 4. Save report in SQLite analysis_history
        save_analysis_report(ticker, mode, recommendation.value, report_markdown)
        logs.append("[Synthesis Node] Analysis report saved to history database.")
        
        return {
            "logs": logs,
            "final_recommendation": recommendation.value,
            "final_report_markdown": report_markdown
        }
    except Exception as e:
        logger.error(f"Synthesis node failed: {e}")
        logs.append(f"[Synthesis Node] CIO Synthesis failed: {e}")
        return {
            "logs": logs,
            "final_recommendation": "HOLD",
            "final_report_markdown": f"# Analysis Failed\nAn error occurred while compiling the final report: {e}"
        }
