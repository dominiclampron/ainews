# data/__init__.py
"""
Data module - SQLite database management for article storage.
"""

from data.database import (
    get_connection,
    close_connection,
    get_cursor,
    get_db_path,
    get_schema_version,
    get_database_stats,
    vacuum_database,
)
from data.models import (
    ArticleRecord,
    SummaryRecord,
    DigestRecord,
    save_article,
    save_articles,
    get_article_by_url,
    get_article_by_id,
    get_recent_articles,
    get_articles_for_digest,
    delete_old_articles,
    article_exists,
    save_summary,
    get_summary_for_article,
    save_digest,
    get_recent_digests,
    get_digest_for_period,
)

__all__ = [
    # Database
    "get_connection",
    "close_connection",
    "get_cursor",
    "get_db_path",
    "get_schema_version",
    "get_database_stats",
    "vacuum_database",
    # Models
    "ArticleRecord",
    "SummaryRecord",
    "DigestRecord",
    # Article CRUD
    "save_article",
    "save_articles",
    "get_article_by_url",
    "get_article_by_id",
    "get_recent_articles",
    "get_articles_for_digest",
    "delete_old_articles",
    "article_exists",
    # Summary CRUD
    "save_summary",
    "get_summary_for_article",
    # Digest CRUD
    "save_digest",
    "get_recent_digests",
    "get_digest_for_period",
]

