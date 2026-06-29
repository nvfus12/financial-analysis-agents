import sqlite3
from src.infrastructure.config import Config

def get_connection() -> sqlite3.Connection:
    """
    Establishes and returns a SQLite database connection.
    Configures row_factory for dict-like access and enables WAL mode for thread safety.
    """
    db_path = Config.get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Enable WAL (Write-Ahead Logging) to allow concurrent reads and writes
    conn.execute("PRAGMA journal_mode=WAL;")
    # Enforce foreign key constraints
    conn.execute("PRAGMA foreign_keys=ON;")
    
    return conn
