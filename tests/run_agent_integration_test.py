import os
import sys
import uuid
import logging
from dotenv import load_dotenv

# Ensure root dir is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agent_integration_test")

def main():
    load_dotenv()
    
    ticker = "FPT"
    mode = "technical"  # Quick technical mode test to avoid rate limits or pdf uploads
    
    logger.info(f"--- Launching LangGraph test run for ticker '{ticker}' (Mode: {mode}) ---")
    
    # 1. Check keys
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_keys = os.getenv("GEMINI_API_KEYS", "").strip()
    nine_router_key = os.getenv("NINE_ROUTER_API_KEY", "").strip()
    
    has_gemini = (gemini_key and gemini_key != "your_gemini_api_key_here") or (gemini_keys and "your_gemini_api_key_here" not in gemini_keys)
    has_9router = (nine_router_key and "sk-" in nine_router_key)
    
    if not has_gemini and not has_9router:
        logger.error("Error: Neither GEMINI_API_KEYS nor NINE_ROUTER_API_KEY is configured in .env file. Please populate them first.")
        sys.exit(1)
        
    try:
        from src.agents.graph import build_graph
        graph = build_graph()
        
        # 2. Prepare graph state inputs
        config = {"configurable": {"thread_id": f"test-{uuid.uuid4().hex[:6]}"}}
        initial_state = {
            "ticker": ticker,
            "analysis_mode": mode,
            "pdf_path": "",
            "logs": ["Test session started."],
            "raw_financials": {},
            "technical_signals": {},
            "scraped_news": []
        }
        
        logger.info("Executing graph nodes...")
        final_state = graph.invoke(initial_state, config=config)
        
        logger.info("--- GRAPH RUN LOGS ---")
        for log in final_state.get("logs", []):
            print(log)
            
        logger.info("--- SYNTHESIS REPORT OUTPUT ---")
        report = final_state.get("final_report_markdown", "")
        print(report[:1500]) # Print first 1500 characters
        
        logger.info("Integration test complete.")
    except Exception as e:
        logger.exception(f"Graph execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
