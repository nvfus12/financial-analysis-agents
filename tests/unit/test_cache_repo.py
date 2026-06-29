import os
import sqlite3
import pytest
from datetime import datetime, timedelta

# Override Database path to a test database BEFORE importing adapters
os.environ["DATABASE_URL"] = "data/test_finanalyst.db"

from src.infrastructure.config import Config
from src.infrastructure.database.migrations import run_migrations
from src.infrastructure.database.cache_repo import (
    save_stock_data_cache,
    get_cached_stock_data,
    save_news_cache,
    get_cached_news,
    save_analysis_report,
    get_analysis_history,
    get_analysis_report_by_id,
    delete_analysis_report
)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Initializes the test database migrations and handles clean up."""
    # Ensure test migrations run
    run_migrations()
    yield
    # Cleanup test database file after all tests finish
    db_path = Config.get_db_path()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            # Remove helper journal files if sqlite left them
            if os.path.exists(db_path + "-wal"):
                os.remove(db_path + "-wal")
            if os.path.exists(db_path + "-shm"):
                os.remove(db_path + "-shm")
        except Exception:
            pass

def test_stock_data_cache():
    ticker = "TEST_STOCK"
    data = {"ratios": {"pe": 10.0, "roe": 15.0}}
    
    # Save cache with 1 hour TTL
    save_stock_data_cache(ticker, "ratios", data, ttl_hours=1.0)
    
    # Retrieve cache
    cached = get_cached_stock_data(ticker, "ratios")
    assert cached is not None
    assert cached["ratios"]["pe"] == 10.0
    
    # Test expiration (save with negative TTL)
    save_stock_data_cache(ticker, "ratios", data, ttl_hours=-1.0)
    expired = get_cached_stock_data(ticker, "ratios")
    assert expired is None

def test_news_cache():
    ticker = "TEST_NEWS"
    articles = [
        {
            "title": "Test Title 1",
            "url": "https://test.com/1",
            "source": "cafef",
            "content_snippet": "Snippet 1",
            "sentiment_label": "positive",
            "sentiment_score": 0.8
        },
        {
            "title": "Test Title 2",
            "url": "https://test.com/2",
            "source": "vietstock",
            "content_snippet": "Snippet 2",
            "sentiment_label": "neutral",
            "sentiment_score": 0.0
        }
    ]
    
    save_news_cache(ticker, articles)
    
    # Retrieve
    cached = get_cached_news(ticker, max_age_hours=1.0)
    assert len(cached) == 2
    assert cached[0]["title"] == "Test Title 1"
    assert cached[0]["sentiment_label"] == "positive"
    assert cached[0]["sentiment_score"] == 0.8

def test_analysis_history():
    ticker = "TEST_HIST"
    markdown = "# Financial analysis report of TEST_HIST"
    
    save_analysis_report(ticker, "full", "BUY", markdown)
    
    # Check history list
    history = get_analysis_history(limit=5)
    assert len(history) >= 1
    
    latest = history[0]
    assert latest["ticker"] == ticker
    assert latest["recommendation"] == "BUY"
    
    # Check full report by ID
    report = get_analysis_report_by_id(latest["id"])
    assert report is not None
    assert report["report_markdown"] == markdown
    assert report["analysis_mode"] == "full"

    # Test Deletion
    del_success = delete_analysis_report(latest["id"])
    assert del_success is True

    # Report should now be gone
    deleted_report = get_analysis_report_by_id(latest["id"])
    assert deleted_report is None
