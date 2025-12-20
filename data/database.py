"""
data/database.py - SQLite database connection manager.

Provides:
- Thread-safe connection management
- Schema migration system
- Secure file permissions
- Automatic table creation
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Optional, Generator

from config.settings import get_settings


# Database version for migrations
SCHEMA_VERSION = 1

# Thread lock for connection management
_db_lock = Lock()
_connection: Optional[sqlite3.Connection] = None


def get_db_path() -> Path:
    """Get the database file path from settings."""
    settings = get_settings()
    return settings.database.get_full_path()


def ensure_permissions(path: Path):
    """Set secure file permissions (600 - owner only)."""
    if path.exists():
        try:
            os.chmod(path, 0o600)
        except (OSError, AttributeError):
            pass  # Windows doesn't support chmod


def get_connection() -> sqlite3.Connection:
    """
    Get or create database connection.
    
    Returns:
        sqlite3.Connection with row factory enabled
    """
    global _connection
    
    with _db_lock:
        if _connection is None:
            db_path = get_db_path()
            
            # Ensure parent directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create connection
            _connection = sqlite3.connect(
                str(db_path),
                check_same_thread=False,
                timeout=30.0,
            )
            
            # Enable row factory for dict-like access
            _connection.row_factory = sqlite3.Row
            
            # Enable foreign keys
            _connection.execute("PRAGMA foreign_keys = ON")
            
            # Set secure permissions
            ensure_permissions(db_path)
            
            # Initialize schema
            _init_schema(_connection)
        
        return _connection


def close_connection():
    """Close the database connection."""
    global _connection
    
    with _db_lock:
        if _connection is not None:
            _connection.close()
            _connection = None


@contextmanager
def get_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """
    Get a database cursor with automatic commit/rollback.
    
    Example:
        with get_cursor() as cursor:
            cursor.execute("INSERT INTO ...")
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def _init_schema(conn: sqlite3.Connection):
    """Initialize database schema."""
    cursor = conn.cursor()
    
    # Check current version
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("SELECT MAX(version) FROM schema_version")
    row = cursor.fetchone()
    current_version = row[0] if row[0] else 0
    
    # Apply migrations
    if current_version < 1:
        _migrate_v1(cursor)
        cursor.execute("INSERT INTO schema_version (version) VALUES (1)")
    
    conn.commit()
    cursor.close()


def _migrate_v1(cursor: sqlite3.Cursor):
    """
    Schema version 1 - Initial schema.
    
    Tables:
    - articles: Stored article data
    - ai_summaries: AI-generated summaries
    - digests: Weekly/daily compilations
    - settings: Key-value settings (future multi-user ready)
    """
    
    # Articles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            url_hash TEXT NOT NULL,
            title TEXT NOT NULL,
            outlet TEXT,
            outlet_key TEXT,
            category TEXT,
            published_at DATETIME,
            summary TEXT,
            image_url TEXT,
            
            -- Scoring
            recency_score REAL DEFAULT 0,
            importance_score REAL DEFAULT 0,
            source_score REAL DEFAULT 0,
            final_score REAL DEFAULT 0,
            
            -- Metadata
            priority TEXT DEFAULT 'normal',
            why_matters TEXT,
            reading_time_min INTEGER DEFAULT 0,
            
            -- Clustering
            cluster_id TEXT,
            is_cluster_primary INTEGER DEFAULT 1,
            related_articles_json TEXT,
            
            -- Timestamps
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles(url_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_score ON articles(final_score DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at)")
    
    # AI Summaries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            summary_text TEXT NOT NULL,
            token_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_summaries_article ON ai_summaries(article_id)")
    
    # Digests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            digest_type TEXT DEFAULT 'weekly',
            digest_text TEXT NOT NULL,
            article_count INTEGER DEFAULT 0,
            provider TEXT,
            model TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_digests_period ON digests(period_start, period_end)")
    
    # Settings table (for future multi-user support)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kv_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


def get_schema_version() -> int:
    """Get current schema version."""
    with get_cursor() as cursor:
        cursor.execute("SELECT MAX(version) FROM schema_version")
        row = cursor.fetchone()
        return row[0] if row[0] else 0


def vacuum_database():
    """Optimize database by running VACUUM."""
    conn = get_connection()
    conn.execute("VACUUM")


def get_database_stats() -> dict:
    """Get database statistics."""
    with get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ai_summaries")
        summary_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM digests")
        digest_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM articles")
        row = cursor.fetchone()
        oldest = row[0]
        newest = row[1]
    
    # Get file size
    db_path = get_db_path()
    size_bytes = db_path.stat().st_size if db_path.exists() else 0
    
    return {
        "articles": article_count,
        "summaries": summary_count,
        "digests": digest_count,
        "oldest_article": oldest,
        "newest_article": newest,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
        "schema_version": get_schema_version(),
    }
