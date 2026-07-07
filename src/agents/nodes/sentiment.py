import logging
from typing import Dict, Any, List
from src.domain.models.state import AgentState
from src.infrastructure.database.cache_repo import get_cached_news, save_news_cache
from src.infrastructure.adapters.cafef_scraper import CafeFScraper
from src.infrastructure.adapters.yfinance_adapter import YFinanceAdapter
from src.infrastructure.adapters.finbert_adapter import FinBERTAdapter
from src.infrastructure.adapters.gemini_adapter import GeminiAdapter
from src.infrastructure.config import Config
from src.agents.prompts import SENTIMENT_SYSTEM_INSTRUCTION, SENTIMENT_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

def sentiment_node(state: AgentState) -> Dict[str, Any]:
    """
    Sentiment Analyst Node.
    Fetches ticker news (with caching), scores sentiment using FinBERT,
    calculates stats, and evaluates market sentiment using Gemini LLM.
    """
    ticker = state.get("ticker", "").strip().upper()
    market = state.get("market", "VN").strip().upper()
    logs = state.get("logs", [])
    
    logs.append(f"[Sentiment Node] Starting news sentiment analysis for {ticker} (Market: {market}).")
    
    # 1. Fetch News and analyze sentiment (check SQLite cache first)
    articles = get_cached_news(ticker, max_age_hours=24.0)
    
    if not articles:
        logs.append(f"[Sentiment Node] Cache miss or stale news for {ticker}. Fetching news...")
        if market == "US":
            provider = YFinanceAdapter()
        else:
            provider = CafeFScraper()
            
        raw_news = provider.fetch_latest_news(ticker, limit=10)
        
        if raw_news:
            logs.append(f"[Sentiment Node] Scraped {len(raw_news)} headlines. Scoring sentiment via FinBERT...")
            analyzer = FinBERTAdapter()
            titles = [art["title"] for art in raw_news]
            
            try:
                scores = analyzer.analyze_sentiment(titles)
            except Exception as e:
                logger.error(f"Sentiment scoring failed: {e}")
                scores = [{"label": "neutral", "score": 0.0} for _ in titles]
            
            # Fuse scraped data with sentiment scores
            articles = []
            for art, score in zip(raw_news, scores):
                fused = dict(art)
                fused["sentiment_label"] = score["label"]
                fused["sentiment_score"] = score["score"]
                articles.append(fused)
                
            save_news_cache(ticker, articles)
            logs.append("[Sentiment Node] News sentiment calculated and saved to cache.")
        else:
            logs.append("[Sentiment Node] Warning: No news articles fetched.")
            articles = []
    else:
        logs.append("[Sentiment Node] Loaded news with sentiment scores from SQLite cache.")

    if not articles:
        return {
            "logs": logs,
            "sentiment_insights": "Sentiment analysis unavailable: No news articles found."
        }

    # 2. Calculate Sentiment statistics
    total_score = 0.0
    pos_count = neg_count = neu_count = 0
    formatted_news = []
    
    for idx, art in enumerate(articles):
        score = art["sentiment_score"]
        label = art["sentiment_label"]
        total_score += score
        
        if label == "positive":
            pos_count += 1
        elif label == "negative":
            neg_count += 1
        else:
            neu_count += 1
            
        formatted_news.append(
            f"{idx+1}. {art['title']}\n"
            f"   Source: {art['source']} | Label: {label.upper()} (Score: {score:.2f})\n"
            f"   Snippet: {art.get('content_snippet', 'None')}"
        )
        
    avg_score = total_score / len(articles)
    news_context = "\n\n".join(formatted_news)
    
    sentiment_summary = (
        f"Average News Sentiment Score: {avg_score:.2f} (Scale: -1.0 to 1.0)\n"
        f"Distribution: {pos_count} Positive, {neg_count} Negative, {neu_count} Neutral"
    )
    
    logs.append(f"[Sentiment Node] Compiled stats: Avg={avg_score:.2f} (Pos:{pos_count}, Neg:{neg_count}).")

    # 3. LLM Analysis
    try:
        adapter = GeminiAdapter(model_name=Config.LLM_MODEL_NAME_FLASH)
        prompt = SENTIMENT_PROMPT_TEMPLATE.format(
            ticker=ticker,
            news_context=f"{sentiment_summary}\n\n{news_context}"
        )
        
        lang = state.get("report_language", "vi")
        lang_directive = "\n\nCRITICAL: You must write the entire output analysis in Vietnamese." if lang == "vi" else "\n\nCRITICAL: You must write the entire output analysis in English."
        prompt += lang_directive
        
        insights = adapter.generate_text(
            system_instruction=SENTIMENT_SYSTEM_INSTRUCTION,
            prompt=prompt
        )
        
        logs.append("[Sentiment Node] Successfully generated sentiment insights.")
        
        # Save scraped news in state list
        return {
            "logs": logs,
            "scraped_news": articles,
            "sentiment_insights": insights
        }
    except Exception as e:
        logger.error(f"Sentiment LLM generation failed: {e}")
        logs.append(f"[Sentiment Node] LLM failed: {e}")
        return {
            "logs": logs,
            "sentiment_insights": f"Sentiment analysis failed due to system error: {e}"
        }
