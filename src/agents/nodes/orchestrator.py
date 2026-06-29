import json
import logging
from typing import Dict, Any
from src.domain.models.state import AgentState
from src.infrastructure.adapters.gemini_adapter import GeminiAdapter
from src.infrastructure.config import Config
from src.agents.prompts import ORCHESTRATOR_SYSTEM_INSTRUCTION, ORCHESTRATOR_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """
    Lead Coordinator Node.
    Validates input stock ticker and schedules specialist analysis nodes.
    """
    ticker = state.get("ticker", "").strip().upper()
    mode = state.get("analysis_mode", "full").lower()
    pdf_path = state.get("pdf_path", "")
    
    logs = state.get("logs", [])
    logs.append(f"[Orchestrator] Planning investment analysis for ticker '{ticker}' (Mode: {mode}).")
    
    if not ticker:
        logs.append("[Orchestrator] Input validation failed: Ticker is empty.")
        return {
            "logs": logs,
            "final_report_markdown": "# Error\nStock ticker is missing or empty."
        }
        
    try:
        adapter = GeminiAdapter(model_name=Config.LLM_MODEL_NAME_FLASH)
        pdf_uploaded = "Yes" if pdf_path else "No"
        
        prompt = ORCHESTRATOR_PROMPT_TEMPLATE.format(
            ticker=ticker,
            mode=mode,
            pdf_uploaded=pdf_uploaded
        )
        
        lang = state.get("report_language", "vi")
        lang_directive = "\n\nCRITICAL: You must write the 'strategy' field output in Vietnamese." if lang == "vi" else "\n\nCRITICAL: You must write the 'strategy' field output in English."
        prompt += lang_directive
        
        res_text = adapter.generate_text(
            system_instruction=ORCHESTRATOR_SYSTEM_INSTRUCTION,
            prompt=prompt
        )
        
        # Clean markdown code fences if output is wrapped
        clean_text = res_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        plan = json.loads(clean_text)
        
        val_error = plan.get("validation_error")
        if val_error:
            logs.append(f"[Orchestrator] Input validation error: {val_error}")
            return {
                "logs": logs,
                "final_report_markdown": f"# Input Validation Error\n{val_error}"
            }
            
        planned_nodes = plan.get("planned_nodes", [])
        strategy_notes = plan.get("strategy_notes", "")
        
        logs.append(f"[Orchestrator] Scheduled sub-agents: {planned_nodes}. Strategy: {strategy_notes}")
        
        # Initialize raw_financials dictionary with planning metadata
        raw_financials = state.get("raw_financials", {})
        raw_financials["planned_nodes"] = planned_nodes
        raw_financials["strategy_notes"] = strategy_notes
        
        return {
            "ticker": ticker,
            "logs": logs,
            "raw_financials": raw_financials
        }
        
    except Exception as e:
        logger.error(f"Orchestrator node failed: {e}")
        # Rule-based fallback planning
        planned_nodes = ["fundamental", "technical", "sentiment"]
        if mode == "fundamental":
            planned_nodes = ["fundamental", "sentiment"]
        elif mode == "technical":
            planned_nodes = ["technical"]
            
        logs.append(f"[Orchestrator] Planning LLM failed: {e}. Falling back to default list: {planned_nodes}")
        
        raw_financials = state.get("raw_financials", {})
        raw_financials["planned_nodes"] = planned_nodes
        raw_financials["strategy_notes"] = "Fallback default planning."
        
        return {
            "ticker": ticker,
            "logs": logs,
            "raw_financials": raw_financials
        }
