import logging
import os
from typing import Optional
from urllib.parse import urlparse

from app.database.base import BaseDatabaseAdapter
from app.database.adapters.sqlite import SQLiteAdapter

logger = logging.getLogger(__name__)

def create_database_adapter(
    db_type: Optional[str] = None,
    url: Optional[str] = None,
    sqlite_path: Optional[str] = None,
    host: str = "localhost",
    port: int = 0,
    user: str = "",
    password: str = "",
    database: str = "telecore_bot"
) -> BaseDatabaseAdapter:
    """
    Factory creating the appropriate database adapter based on DB_TYPE or DATABASE_URL.
    Supported engines: SQLite, PostgreSQL (asyncpg), MySQL (aiomysql), MongoDB (motor).
    """
    # 1. Normalize type or detect from connection URL
    detected_type = (db_type or "").strip().lower()

    if not detected_type and url:
        url_lower = url.lower()
        if url_lower.startswith(("postgres://", "postgresql://", "postgresql+asyncpg://")):
            detected_type = "postgres"
        elif url_lower.startswith(("mysql://", "mysql+aiomysql://")):
            detected_type = "mysql"
        elif url_lower.startswith(("mongodb://", "mongodb+srv://")):
            detected_type = "mongo"
        elif url_lower.startswith(("sqlite://", "sqlite+aiosqlite://")):
            detected_type = "sqlite"

    if not detected_type:
        detected_type = "sqlite"

    logger.info("Initializing TeleCore Multi-Database Provider: [%s]", detected_type.upper())

    # 2. Instantiate corresponding adapter
    if detected_type in ("postgres", "postgresql"):
        from app.database.adapters.postgres import PostgresAdapter
        dsn = url or f"postgresql://{user}:{password}@{host}:{port or 5432}/{database}"
        return PostgresAdapter(dsn=dsn)

    elif detected_type in ("mysql", "mariadb"):
        from app.database.adapters.mysql import MySQLAdapter
        return MySQLAdapter(
            url=url,
            host=host,
            port=port or 3306,
            user=user or "root",
            password=password,
            db=database
        )

    elif detected_type in ("mongo", "mongodb"):
        from app.database.adapters.mongo import MongoAdapter
        mongo_uri = url or f"mongodb://{host}:{port or 27017}/{database}"
        return MongoAdapter(uri=mongo_uri, db_name=database)

    else:
        # Default SQLite
        path = sqlite_path or os.getenv("SQLITE_PATH", "bot_database.sqlite3")
        return SQLiteAdapter(db_path=path)
