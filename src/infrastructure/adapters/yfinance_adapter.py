import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf

from src.domain.ports.stock_provider import StockDataProvider
from src.domain.ports.news_provider import NewsProvider

logger = logging.getLogger(__name__)

class YFinanceAdapter(StockDataProvider, NewsProvider):
    """
    Adapter implementing both StockDataProvider and NewsProvider interfaces
    using the yfinance library for US market coverage.
    """

    def get_historical_prices(self, ticker: str, days: int) -> pd.DataFrame:
        ticker = ticker.upper()
        logger.info(f"Fetching US historical prices for {ticker} using yfinance (period: {days} days)...")
        try:
            # Download price data
            # days is given, so let's format it for yfinance (e.g. '365d')
            period_str = f"{days}d"
            df = yf.download(ticker, period=period_str, progress=False)
            
            if df is None or df.empty:
                logger.warning(f"No price history found for {ticker} via yfinance.")
                return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
                
            # Flatten multi-index columns if they exist (yfinance 0.2.x download output changes)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            # Rename columns to lowercase standard format
            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })
            
            # Ensure time index is datetime
            df.index = pd.to_datetime(df.index)
            df.index.name = "time"
            
            # Keep only required columns
            core_cols = ["open", "high", "low", "close", "volume"]
            df = df[core_cols]
            
            # Clean up types
            for col in ["open", "high", "low", "close"]:
                df[col] = df[col].astype(float)
            df["volume"] = df["volume"].astype(float)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching US prices for {ticker} via yfinance: {e}")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    def get_financial_ratios(self, ticker: str) -> Dict[str, Any]:
        ticker = ticker.upper()
        logger.info(f"Fetching US financial ratios for {ticker} using yfinance...")
        try:
            t = yf.Ticker(ticker)
            info = t.info
            
            if not info:
                logger.warning(f"No info returned for {ticker} via yfinance.")
                return {}
                
            # Extract and scale ratios. 
            # vnstock outputs ratios as percentages (e.g. ROE = 15.6) 
            # while yfinance outputs them as decimals (e.g. returnOnEquity = 0.156).
            # We scale yfinance's decimal ratios by 100 for consistency in prompt analysis.
            
            def scale_percentage(val: Any) -> Any:
                if val is None or str(val).strip() in ["", "-", "None"]:
                    return None
                try:
                    return float(val) * 100.0
                except (ValueError, TypeError):
                    return None
                    
            def get_float(val: Any) -> Any:
                if val is None or str(val).strip() in ["", "-", "None"]:
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            ratios = {
                "pe": get_float(info.get("trailingPE")),
                "pb": get_float(info.get("priceToBook")),
                "roe": scale_percentage(info.get("returnOnEquity")),
                "roa": scale_percentage(info.get("returnOnAssets")),
                "eps": get_float(info.get("trailingEps")),
                "gross_margin": scale_percentage(info.get("grossMargins")),
                "net_margin": scale_percentage(info.get("profitMargins")),
                "debt_to_equity": get_float(info.get("debtToEquity"))  # yfinance info debtToEquity is already scaled (e.g. 140.0 means 140%)
            }
            return ratios
        except Exception as e:
            logger.error(f"Error fetching US financial ratios for {ticker} via yfinance: {e}")
            return {}

    def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        ticker = ticker.upper()
        logger.info(f"Fetching US company profile for {ticker} using yfinance...")
        try:
            t = yf.Ticker(ticker)
            info = t.info
            
            if not info:
                logger.warning(f"No profile metadata found for {ticker} via yfinance.")
                return {
                    "ticker": ticker,
                    "name": ticker,
                    "industry": "Unknown",
                    "description": "No description available.",
                    "capital_size": 0.0
                }
                
            profile = {
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "industry": info.get("industry", "Unknown"),
                "description": info.get("longBusinessSummary", "No description available."),
                "capital_size": float(info.get("marketCap", 0.0)) / 1e9  # Convert market cap to Billions USD
            }
            return profile
        except Exception as e:
            logger.error(f"Error fetching US company profile for {ticker} via yfinance: {e}")
            return {
                "ticker": ticker,
                "name": ticker,
                "industry": "Unknown",
                "description": "No description available.",
                "capital_size": 0.0
            }

    def fetch_latest_news(self, ticker: str, limit: int = 15) -> List[Dict[str, Any]]:
        ticker = ticker.upper()
        logger.info(f"Fetching US news headlines for {ticker} using yfinance news feed...")
        try:
            t = yf.Ticker(ticker)
            news_items = t.news
            
            if not news_items:
                logger.warning(f"No news returned for {ticker} via yfinance. Using fallback mock news.")
                return self._get_fallback_news(ticker, limit)
                
            articles = []
            for item in news_items[:limit]:
                # Extract publish time
                published_time = item.get("providerPublishTime", 0)
                if published_time:
                    try:
                        published_at = datetime.fromtimestamp(published_time).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        published_at = "N/A"
                else:
                    published_at = "N/A"
                    
                articles.append({
                    "title": item.get("title", "US Financial Headline"),
                    "url": item.get("link", "https://finance.yahoo.com"),
                    "source": item.get("publisher", "Yahoo Finance"),
                    "content_snippet": item.get("title", ""),  # yfinance doesn't usually have content snippet, so we use title or empty
                    "published_at": published_at
                })
                
            return articles
        except Exception as e:
            logger.warning(f"Failed to fetch yfinance news for {ticker} due to: {e}. Falling back to mock news.")
            return self._get_fallback_news(ticker, limit)

    def _get_fallback_news(self, ticker: str, limit: int) -> List[Dict[str, Any]]:
        """Generates mock financial news articles for the stock ticker on scraper/API failure."""
        logger.info(f"Generating US mock news database for {ticker}...")
        templates = [
            {
                "title": f"{ticker} stock climbs as earnings beat Wall Street expectations",
                "content_snippet": f"Driven by strong performance in its cloud and services divisions, {ticker} continues to attract major institutional flows this week.",
                "source": "Yahoo Finance (Mock)"
            },
            {
                "title": f"{ticker} announces cash dividend hike of 15% for next quarter",
                "content_snippet": f"The board of directors of {ticker} approved a dividend increase, citing a healthy balance sheet and strong free cash flow generation.",
                "source": "MarketWatch (Mock)"
            },
            {
                "title": f"Technical Analysis: {ticker} breakout confirmed above 50-day moving average",
                "content_snippet": f"The price chart of {ticker} shows a clean breakout above resistance, signaling strong accumulation from retail and institutional traders.",
                "source": "SeekingAlpha (Mock)"
            },
            {
                "title": f"Tech sector experiences profit-taking pressure; {ticker} consolidates",
                "content_snippet": f"Macro headwinds and treasury yield shifts trigger a minor correction in high-growth tech stocks, leaving {ticker} trading sideways.",
                "source": "Bloomberg (Mock)"
            },
            {
                "title": f"{ticker} CEO buys 50,000 shares in open-market insider transaction",
                "content_snippet": f"According to SEC filings, the chief executive purchased a block of stock for long-term investment, boosting market confidence.",
                "source": "CNBC (Mock)"
            }
        ]
        
        fallback_list = []
        for i in range(min(limit, len(templates))):
            art = templates[i]
            fallback_list.append({
                "title": art["title"],
                "url": f"https://finance.yahoo.com/mock-news/{ticker.lower()}-{i}",
                "source": art["source"],
                "content_snippet": art["content_snippet"],
                "published_at": "Today"
            })
        return fallback_list
