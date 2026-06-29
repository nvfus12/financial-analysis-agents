import os
import sys
import uuid
import logging
from dotenv import load_dotenv

# Ensure root dir is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("full_system_test")

def main():
    load_dotenv()
    
    ticker = "FPT"
    mode = "full"
    pdf_filename = "c0b4f8b7_1778843190.pdf"
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), pdf_filename)
    
    logger.info(f"--- Launching FULL Multi-Agent LangGraph System Test ---")
    logger.info(f"Ticker: {ticker}")
    logger.info(f"Mode: {mode}")
    logger.info(f"PDF Path: {pdf_path} (Exists: {os.path.exists(pdf_path)})")
    
    if not os.path.exists(pdf_path):
        logger.error(f"Error: PDF report file '{pdf_filename}' not found in workspace root.")
        sys.exit(1)
        
    try:
        from src.agents.graph import build_graph
        graph = build_graph()
        
        # Prepare graph state inputs
        config = {"configurable": {"thread_id": f"full-test-{uuid.uuid4().hex[:6]}"}}
        initial_state = {
            "ticker": ticker,
            "analysis_mode": mode,
            "pdf_path": pdf_path,
            "logs": ["Full system test started."],
            "raw_financials": {},
            "technical_signals": {},
            "scraped_news": []
        }
        
        logger.info("Executing full multi-agent graph nodes...")
        final_state = graph.invoke(initial_state, config=config)
        
        logger.info("--- GRAPH RUN LOGS ---")
        for log in final_state.get("logs", []):
            print(log)
            
        logger.info("--- FINAL CIO INVESTMENT SYNTHESIS REPORT ---")
        report = final_state.get("final_report_markdown", "")
        print(report[:3000]) # Print first 3000 characters of the final report
        
        # Verify output saved in DB
        from src.infrastructure.database.cache_repo import get_analysis_history
        history = get_analysis_history()
        logger.info(f"Saved analysis runs in DB: {len(history)}")
        if history:
            logger.info(f"Latest DB Run: Ticker={history[0]['ticker']}, Rec={history[0]['recommendation']}, Date={history[0]['created_at']}")
            
        logger.info("Full system test completed successfully.")
    except Exception as e:
        logger.exception(f"Full system execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
