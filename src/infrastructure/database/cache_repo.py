import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from src.infrastructure.database.connection import get_connection

logger = logging.getLogger(__name__)

def _get_now_iso() -> str:
    return datetime.utcnow().isoformat()

# --- Stock Cache operations ---

def get_cached_stock_data(ticker: str, data_type: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves cached stock data if it exists and has not expired.
    Returns None if cache is missing or expired.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT data_json, expires_at 
            FROM stock_data_cache 
            WHERE ticker = ? AND data_type = ?
            """,
            (ticker.upper(), data_type.lower())
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        expires_at_str = row["expires_at"]
        expires_at = datetime.fromisoformat(expires_at_str)
        
        if datetime.utcnow() > expires_at:
            logger.debug(f"Cache expired for stock {ticker} ({data_type})")
            return None
            
        return json.loads(row["data_json"])
    except Exception as e:
        logger.error(f"Error reading stock cache for {ticker} ({data_type}): {e}")
        return None
    finally:
        conn.close()

def save_stock_data_cache(ticker: str, data_type: str, data: Dict[str, Any], ttl_hours: float = 4.0):
    """
    Saves stock data to the cache table with an expiration timestamp.
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=ttl_hours)
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO stock_data_cache (ticker, data_type, data_json, fetched_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ticker.upper(),
                data_type.lower(),
                json.dumps(data),
                now.isoformat(),
                expires_at.isoformat()
            )
        )
        conn.commit()
        logger.debug(f"Stock cache written for {ticker} ({data_type}). Expires in {ttl_hours}h.")
    except Exception as e:
        logger.error(f"Error saving stock cache for {ticker} ({data_type}): {e}")
    finally:
        conn.close()


# --- News Cache operations ---

def get_cached_news(ticker: str, max_age_hours: float = 24.0) -> List[Dict[str, Any]]:
    """
    Retrieves cached news articles for a ticker if they were fetched within max_age_hours.
    """
    conn = get_connection()
    threshold = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, ticker, title, url, source, content_snippet, sentiment_label, sentiment_score, published_at, fetched_at
            FROM news_cache
            WHERE ticker = ? AND fetched_at >= ?
            ORDER BY published_at DESC
            """,
            (ticker.upper(), threshold)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error reading news cache for {ticker}: {e}")
        return []
    finally:
        conn.close()

def save_news_cache(ticker: str, articles: List[Dict[str, Any]]):
    """
    Saves a list of news articles to the cache table.
    Each article should have: 'title', 'url', 'source', 'content_snippet', 'sentiment_label', 'sentiment_score', 'published_at'.
    """
    now_iso = _get_now_iso()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for art in articles:
            # Generate a unique hash for the URL to use as ID
            url = art["url"]
            art_id = hashlib.sha256(url.encode("utf-8")).hexdigest()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO news_cache (
                    id, ticker, title, url, source, content_snippet, sentiment_label, sentiment_score, published_at, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    art_id,
                    ticker.upper(),
                    art["title"],
                    url,
                    art["source"],
                    art.get("content_snippet", ""),
                    art["sentiment_label"],
                    art["sentiment_score"],
                    art.get("published_at", now_iso),
                    now_iso
                )
            )
        conn.commit()
        logger.debug(f"Saved {len(articles)} news articles to cache for {ticker}.")
    except Exception as e:
        logger.error(f"Error saving news cache for {ticker}: {e}")
    finally:
        conn.close()


# --- Analysis History operations ---

def save_analysis_report(ticker: str, mode: str, recommendation: str, markdown: str, market: str = "VN"):
    """
    Persists a generated analysis report to the history table.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analysis_history (ticker, market, analysis_mode, recommendation, report_markdown)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticker.upper(), market.upper(), mode.lower(), recommendation.upper(), markdown)
        )
        conn.commit()
        logger.debug(f"Analysis report saved to history for {ticker} (Market: {market}).")
    except Exception as e:
        logger.error(f"Error saving analysis report for {ticker}: {e}")
    finally:
        conn.close()

def get_analysis_history(limit: int = 15) -> List[Dict[str, Any]]:
    """
    Retrieves previous analysis reports from the database.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, ticker, market, analysis_mode, recommendation, created_at
            FROM analysis_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching analysis history: {e}")
        return []
    finally:
        conn.close()

def get_analysis_report_by_id(report_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single full analysis report by ID.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, ticker, market, analysis_mode, recommendation, report_markdown, created_at
            FROM analysis_history
            WHERE id = ?
            """,
            (report_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error fetching report by ID {report_id}: {e}")
        return None
    finally:
        conn.close()

def delete_analysis_report(report_id: int) -> bool:
    """
    Deletes a single analysis report by its ID.
    Returns True if successful, False otherwise.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM analysis_history WHERE id = ?",
            (report_id,)
        )
        conn.commit()
        logger.debug(f"Analysis report with ID {report_id} deleted.")
        return True
    except Exception as e:
        logger.error(f"Error deleting analysis report {report_id}: {e}")
        return False
    finally:
        conn.close()
