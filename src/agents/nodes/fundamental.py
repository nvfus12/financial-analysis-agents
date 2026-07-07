import os
import hashlib
import logging
from typing import Dict, Any
from src.domain.models.state import AgentState
from src.infrastructure.database.cache_repo import get_cached_stock_data, save_stock_data_cache
from src.infrastructure.adapters.vnstock_adapter import VnStockAdapter
from src.infrastructure.adapters.yfinance_adapter import YFinanceAdapter
from src.infrastructure.adapters.llamaparse_adapter import LlamaParseAdapter
from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
from src.infrastructure.adapters.gemini_adapter import GeminiAdapter
from src.infrastructure.config import Config
from src.agents.prompts import FUNDAMENTAL_SYSTEM_INSTRUCTION, FUNDAMENTAL_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

def fundamental_node(state: AgentState) -> Dict[str, Any]:
    """
    Fundamental Analyst Node.
    Fetches financial ratios (with caching), parses and indexes uploaded PDF reports
    (if not already indexed), retrieves relevant context using ChromaDB,
    and analyzes financial health via Gemini LLM.
    """
    ticker = state.get("ticker", "").strip().upper()
    market = state.get("market", "VN").strip().upper()
    pdf_path = state.get("pdf_path", "")
    logs = state.get("logs", [])
    
    logs.append(f"[Fundamental Node] Starting fundamental analysis for {ticker} (Market: {market}).")
    
    # 1. Fetch Financial Ratios (check database cache first)
    ratios = get_cached_stock_data(ticker, "ratios")
    if not ratios:
        logs.append(f"[Fundamental Node] Cache miss for {ticker} ratios. Fetching data from provider...")
        if market == "US":
            client = YFinanceAdapter()
        else:
            client = VnStockAdapter()
            
        ratios = client.get_financial_ratios(ticker)
        if ratios:
            save_stock_data_cache(ticker, "ratios", ratios)
            logs.append(f"[Fundamental Node] Ratios fetched and cached.")
        else:
            logs.append(f"[Fundamental Node] Warning: Could not fetch ratios for {ticker}.")
            ratios = {}
    else:
        logs.append(f"[Fundamental Node] Loaded ratios from SQLite cache.")

    # 2. PDF RAG Indexing & Retrieval
    pdf_context = "No PDF financial report uploaded."
    if pdf_path and os.path.exists(pdf_path):
        try:
            # Generate file hash to manage unique collections in ChromaDB
            with open(pdf_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()[:8]
            collection_name = f"report_{ticker.lower()}_{file_hash}"
            
            vdb = ChromaDBAdapter()
            
            # Check if collection has already been indexed by querying for a generic term
            check_res = vdb.query(collection_name, "tổng tài sản nợ doanh thu", limit=1)
            if not check_res:
                logs.append(f"[Fundamental Node] Collection '{collection_name}' not found. Parsing PDF via LlamaParse...")
                parser = LlamaParseAdapter()
                chunks = parser.parse_pdf(pdf_path)
                
                # Format to ChromaDB import document structure
                documents = []
                for idx, chunk in enumerate(chunks):
                    documents.append({
                        "id": f"{ticker.lower()}_{file_hash}_{idx}",
                        "text": chunk["text"],
                        "metadata": chunk["metadata"]
                    })
                vdb.index_documents(collection_name, documents)
                logs.append(f"[Fundamental Node] Indexed {len(documents)} PDF chunks into collection '{collection_name}'.")
            else:
                logs.append(f"[Fundamental Node] PDF collection '{collection_name}' already exists in ChromaDB.")

            # Perform semantic search query to gather context for fundamental report
            query_str = f"Báo cáo tài chính kết quả kinh doanh doanh thu lợi nhuận nợ của {ticker}"
            search_results = vdb.query(collection_name, query_str, limit=4)
            
            formatted_chunks = []
            for idx, res in enumerate(search_results):
                page = res["metadata"].get("page_number", "Unknown")
                formatted_chunks.append(f"--- Chunk {idx+1} (Page {page}) ---\n{res['text']}")
            pdf_context = "\n\n".join(formatted_chunks)
            logs.append(f"[Fundamental Node] Retrieved {len(search_results)} relevant chunks from Vector DB.")
            
        except Exception as e:
            logger.error(f"Fundamental Node RAG failed: {e}")
            logs.append(f"[Fundamental Node] RAG pipeline error: {e}. Proceeding without PDF context.")
            pdf_context = f"Error reading PDF: {e}"

    # 3. LLM Analysis
    try:
        adapter = GeminiAdapter(model_name=Config.LLM_MODEL_NAME_FLASH)
        ratios_str = json_str = ""
        if ratios:
            ratios_str = ", ".join([f"{k.upper()}: {v}" for k, v in ratios.items() if v is not None])
            
        prompt = FUNDAMENTAL_PROMPT_TEMPLATE.format(
            ticker=ticker,
            ratios=ratios_str if ratios_str else "Not Available",
            pdf_context=pdf_context
        )
        
        lang = state.get("report_language", "vi")
        lang_directive = "\n\nCRITICAL: You must write the entire output analysis in Vietnamese." if lang == "vi" else "\n\nCRITICAL: You must write the entire output analysis in English."
        prompt += lang_directive
        
        insights = adapter.generate_text(
            system_instruction=FUNDAMENTAL_SYSTEM_INSTRUCTION,
            prompt=prompt
        )
        
        logs.append("[Fundamental Node] Successfully generated financial insights.")
        
        # Save ratios in raw_financials state dict
        raw_financials = state.get("raw_financials", {})
        raw_financials.update(ratios)
        
        return {
            "logs": logs,
            "raw_financials": raw_financials,
            "fundamental_insights": insights
        }
    except Exception as e:
        logger.error(f"Fundamental LLM generation failed: {e}")
        logs.append(f"[Fundamental Node] LLM failed: {e}")
        return {
            "logs": logs,
            "fundamental_insights": f"Fundamental analysis failed due to system error: {e}"
        }
