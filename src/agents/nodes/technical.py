import json
import logging
from typing import Dict, Any
import pandas as pd
from src.domain.models.state import AgentState
from src.domain.services.financial_calc import calculate_rsi, calculate_macd
from src.infrastructure.database.cache_repo import get_cached_stock_data, save_stock_data_cache
from src.infrastructure.adapters.vnstock_adapter import VnStockAdapter
from src.infrastructure.adapters.yfinance_adapter import YFinanceAdapter
from src.infrastructure.adapters.gemini_adapter import GeminiAdapter
from src.infrastructure.config import Config
from src.agents.prompts import TECHNICAL_SYSTEM_INSTRUCTION, TECHNICAL_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

def technical_node(state: AgentState) -> Dict[str, Any]:
    """
    Technical Analyst Node.
    Fetches price history (with caching), computes technical indicators (RSI, MACD, MA),
    and evaluates price action trends using Gemini LLM.
    """
    ticker = state.get("ticker", "").strip().upper()
    market = state.get("market", "VN").strip().upper()
    logs = state.get("logs", [])
    
    logs.append(f"[Technical Node] Starting technical analysis for {ticker} (Market: {market}).")
    
    # 1. Fetch Price History (check database cache first)
    prices_raw = get_cached_stock_data(ticker, "prices")
    df = None
    
    if prices_raw:
        try:
            # Reconstruct pandas DataFrame from cached JSON
            df = pd.read_json(json.dumps(prices_raw), orient="index")
            # Set datetime index
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)
            logs.append(f"[Technical Node] Price history loaded from SQLite cache ({len(df)} bars).")
        except Exception as e:
            logger.error(f"Error parsing cached price history: {e}")
            df = None

    if df is None or df.empty:
        logs.append(f"[Technical Node] Cache miss for {ticker} prices. Fetching data from provider...")
        if market == "US":
            client = YFinanceAdapter()
        else:
            client = VnStockAdapter()
            
        df = client.get_historical_prices(ticker, days=365)
        
        if not df.empty:
            # Convert DataFrame to JSON serializable dict for caching
            # We orient='index' and convert datetime index to string keys
            cache_data = df.to_dict(orient="index")
            # Convert keys to ISO string formatted keys for JSON compatibility
            serializable_cache = {k.isoformat(): v for k, v in cache_data.items()}
            save_stock_data_cache(ticker, "prices", serializable_cache, ttl_hours=2.0) # Price cache expires in 2 hours
            logs.append(f"[Technical Node] Price history fetched and cached.")
        else:
            logs.append(f"[Technical Node] Error: No price data available.")
            return {
                "logs": logs,
                "technical_insights": "Technical analysis failed: No price data available."
            }

    # 2. Compute Technical Indicators
    try:
        close_series = df["close"].sort_index()
        
        # Calculate moving averages
        ma20 = close_series.rolling(window=20).mean()
        ma50 = close_series.rolling(window=50).mean()
        
        # Calculate RSI and MACD
        rsi = calculate_rsi(close_series, period=14)
        macd_line, signal_line, macd_hist = calculate_macd(close_series)
        
        # Get latest values
        curr_price = float(close_series.iloc[-1])
        curr_rsi = float(rsi.iloc[-1])
        curr_macd_line = float(macd_line.iloc[-1])
        curr_macd_sig = float(signal_line.iloc[-1])
        curr_macd_hist = float(macd_hist.iloc[-1])
        
        curr_ma20 = float(ma20.iloc[-1]) if not pd.isna(ma20.iloc[-1]) else curr_price
        curr_ma50 = float(ma50.iloc[-1]) if not pd.isna(ma50.iloc[-1]) else curr_price
        
        # Determine simple crossover states
        ma_trend = "Bullish (Above MA20 and MA50)" if curr_price > curr_ma20 and curr_price > curr_ma50 \
                   else "Bearish (Below MA20 and MA50)" if curr_price < curr_ma20 and curr_price < curr_ma50 \
                   else "Neutral (Mixed MA consolidation)"
                   
        macd_trend = "Bullish Crossover (MACD Line > Signal Line)" if curr_macd_line > curr_macd_sig \
                     else "Bearish Crossover (MACD Line < Signal Line)"
                     
        rsi_state = "Overbought (>70)" if curr_rsi > 70 \
                    else "Oversold (<30)" if curr_rsi < 30 \
                    else "Neutral (30-70)"
                    
        currency_label = "USD" if market == "US" else "VND"
        technical_stats = (
            f"- Current Close Price: {curr_price:,.2f} {currency_label}\n"
            f"- 20-day Simple Moving Average (MA20): {curr_ma20:,.2f} {currency_label}\n"
            f"- 50-day Simple Moving Average (MA50): {curr_ma50:,.2f} {currency_label}\n"
            f"- Moving Average Trend: {ma_trend}\n"
            f"- Relative Strength Index (RSI 14): {curr_rsi:.2f} ({rsi_state})\n"
            f"- MACD Line: {curr_macd_line:.2f}, Signal Line: {curr_macd_sig:.2f}, Hist: {curr_macd_hist:.2f}\n"
            f"- MACD Trend: {macd_trend}"
        )
        
        logger.debug(f"Computed indicators: RSI={curr_rsi}, MACD={curr_macd_line}")
        
    except Exception as e:
        logger.error(f"Error computing indicators: {e}")
        logs.append(f"[Technical Node] Error calculating technical signals: {e}")
        return {
            "logs": logs,
            "technical_insights": f"Failed to compute technical indicators: {e}"
        }

    # 3. LLM Analysis
    try:
        adapter = GeminiAdapter(model_name=Config.LLM_MODEL_NAME_FLASH)
        prompt = TECHNICAL_PROMPT_TEMPLATE.format(
            ticker=ticker,
            technical_stats=technical_stats
        )
        
        lang = state.get("report_language", "vi")
        lang_directive = "\n\nCRITICAL: You must write the entire output analysis in Vietnamese." if lang == "vi" else "\n\nCRITICAL: You must write the entire output analysis in English."
        prompt += lang_directive
        
        insights = adapter.generate_text(
            system_instruction=TECHNICAL_SYSTEM_INSTRUCTION,
            prompt=prompt
        )
        
        logs.append("[Technical Node] Successfully generated technical insights.")
        
        # Save technical stats in technical_signals state dict
        technical_signals = state.get("technical_signals", {})
        technical_signals.update({
            "current_price": curr_price,
            "rsi": curr_rsi,
            "macd_line": curr_macd_line,
            "macd_sig": curr_macd_sig,
            "ma20": curr_ma20,
            "ma50": curr_ma50,
            "trend_summary": ma_trend
        })
        
        return {
            "logs": logs,
            "technical_signals": technical_signals,
            "technical_insights": insights
        }
    except Exception as e:
        logger.error(f"Technical LLM generation failed: {e}")
        logs.append(f"[Technical Node] LLM failed: {e}")
        return {
            "logs": logs,
            "technical_insights": f"Technical analysis failed due to system error: {e}"
        }
