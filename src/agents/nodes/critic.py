import json
import logging
import re
from typing import Dict, Any
from src.domain.models.state import AgentState
from src.infrastructure.adapters.gemini_adapter import GeminiAdapter
from src.infrastructure.config import Config
from src.agents.prompts import CRITIC_SYSTEM_INSTRUCTION, CRITIC_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

def critic_node(state: AgentState) -> Dict[str, Any]:
    """
    Independent Auditor / Reviewer Node.
    Audits specialist reports and CIO synthesis memo against raw factual evidence.
    Identifies the exact failing node if factual or logical inconsistencies exist.
    """
    ticker = state.get("ticker", "").upper()
    market = state.get("market", "VN").upper()
    logs = state.get("logs", [])
    
    current_count = state.get("reflection_count", 0)
    logs.append(f"[Critic Node] Starting audit for {ticker} (Reflection attempt #{current_count + 1}).")
    
    report = state.get("final_report_markdown", "")
    ratios = state.get("raw_financials", {})
    tech_signals = state.get("technical_signals", {})
    news = state.get("scraped_news", [])
    
    fundamental_draft = state.get("fundamental_insights", "N/A")
    technical_draft = state.get("technical_insights", "N/A")
    sentiment_draft = state.get("sentiment_insights", "N/A")

    try:
        adapter = GeminiAdapter(model_name=Config.LLM_MODEL_NAME_FLASH)
        prompt = CRITIC_PROMPT_TEMPLATE.format(
            ticker=ticker,
            market=market,
            raw_ratios=json.dumps(ratios, ensure_ascii=False),
            raw_technical_signals=json.dumps(tech_signals, ensure_ascii=False),
            raw_news=json.dumps(news, ensure_ascii=False),
            fundamental_insights=fundamental_draft,
            technical_insights=technical_draft,
            sentiment_insights=sentiment_draft,
            final_report_markdown=report
        )
        
        lang = state.get("report_language", "vi")
        lang_directive = "\n\nCRITICAL: You must write the 'feedback' field in Vietnamese." if lang == "vi" else "\n\nCRITICAL: You must write the 'feedback' field in English."
        prompt += lang_directive
        
        res_text = adapter.generate_text(
            system_instruction=CRITIC_SYSTEM_INSTRUCTION,
            prompt=prompt
        )
        
        clean_text = res_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        json_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
        if json_match:
            audit_result = json.loads(json_match.group(0))
        else:
            audit_result = {"passed": True, "score": 8.5, "failed_node": "synthesis", "feedback": ""}
            
        passed = bool(audit_result.get("passed", True))
        score = float(audit_result.get("score", 10.0))
        failed_node = str(audit_result.get("failed_node", "synthesis")).lower().strip()
        feedback = str(audit_result.get("feedback", "")) if not passed else ""
        
        # Sanitize failed_node to valid nodes
        valid_nodes = ["fundamental", "technical", "sentiment", "synthesis"]
        if failed_node not in valid_nodes:
            failed_node = "synthesis"
            
        logs.append(f"[Critic Node] Audit result: Passed={passed}, Score={score}/10, Target={failed_node}.")
        if not passed:
            logs.append(f"[Critic Node] Failure feedback: {feedback}")
            
        return {
            "logs": logs,
            "critic_passed": passed,
            "failed_node": failed_node,
            "critic_feedback": feedback,
            "reflection_count": current_count + 1
        }
        
    except Exception as e:
        logger.error(f"Critic node execution failed: {e}. Defaulting to passed=True.")
        logs.append(f"[Critic Node] Audit bypassed due to error: {e}")
        return {
            "logs": logs,
            "critic_passed": True,
            "failed_node": "synthesis",
            "critic_feedback": "",
            "reflection_count": current_count + 1
        }
