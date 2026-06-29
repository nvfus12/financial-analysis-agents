import logging
from src.infrastructure.database.connection import get_connection

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Creates the database tables (stock_data_cache, news_cache, analysis_history)
    if they do not already exist.
    """
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS stock_data_cache (
            ticker      TEXT NOT NULL,
            data_type   TEXT NOT NULL,  -- 'prices' | 'ratios' | 'profile'
            data_json   TEXT NOT NULL,  -- Full JSON payload
            fetched_at  TEXT NOT NULL,  -- ISO 8601 timestamp
            expires_at  TEXT NOT NULL,  -- Cache expiration ISO 8601 timestamp
            PRIMARY KEY (ticker, data_type)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS news_cache (
            id              TEXT PRIMARY KEY,  -- SHA256 of URL
            ticker          TEXT NOT NULL,
            title           TEXT NOT NULL,
            url             TEXT NOT NULL,
            source          TEXT NOT NULL,     -- 'cafef' | 'vietstock'
            content_snippet TEXT,
            sentiment_label TEXT NOT NULL,     -- 'positive' | 'negative' | 'neutral'
            sentiment_score REAL NOT NULL,     -- [-1.0, 1.0]
            published_at    TEXT,
            fetched_at      TEXT NOT NULL,
            UNIQUE(url)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS analysis_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker          TEXT NOT NULL,
            analysis_mode   TEXT NOT NULL,     -- 'full' | 'technical' | 'fundamental'
            recommendation  TEXT NOT NULL,     -- 'BUY' | 'SELL' | 'HOLD'
            report_markdown TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    ]
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for ddl in ddl_statements:
            cursor.execute(ddl)
        conn.commit()
        logger.info("SQLite migrations completed successfully.")
    except Exception as e:
        logger.error(f"Error running database migrations: {e}")
        raise e
    finally:
        conn.close()
