import pytest
import pandas as pd
from src.infrastructure.adapters.yfinance_adapter import YFinanceAdapter

def test_yfinance_historical_prices():
    adapter = YFinanceAdapter()
    ticker = "MSFT"
    df = adapter.get_historical_prices(ticker, days=10)
    
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns
        assert df.index.name == "time"
        assert len(df) > 0
        assert isinstance(df["close"].iloc[-1], float)

def test_yfinance_financial_ratios():
    adapter = YFinanceAdapter()
    ticker = "MSFT"
    ratios = adapter.get_financial_ratios(ticker)
    
    assert isinstance(ratios, dict)
    # yfinance output might be empty under network issues, but if it returns info:
    if ratios:
        assert "pe" in ratios
        assert "pb" in ratios
        assert "roe" in ratios
        assert "eps" in ratios

def test_yfinance_company_profile():
    adapter = YFinanceAdapter()
    ticker = "MSFT"
    profile = adapter.get_company_profile(ticker)
    
    assert isinstance(profile, dict)
    assert profile["ticker"] == "MSFT"
    assert "Microsoft" in profile["name"]
    assert profile["capital_size"] > 0.0

def test_yfinance_fetch_latest_news():
    adapter = YFinanceAdapter()
    ticker = "MSFT"
    news = adapter.fetch_latest_news(ticker, limit=5)
    
    assert isinstance(news, list)
    assert len(news) > 0
    assert "title" in news[0]
    assert "url" in news[0]
    assert "source" in news[0]
