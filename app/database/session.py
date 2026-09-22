import logging
from typing import Optional, Dict, Any, List, Union

from app.database.base import BaseDatabaseAdapter
from app.database.adapters.sqlite import SQLiteAdapter
from app.database.factory import create_database_adapter
from app.database.cache import MemoryTTLCache

logger = logging.getLogger(__name__)

class DatabaseSession:
    """
    High-Performance Unified Database Manager with:
    - Multi-Database backend support (SQLite, PostgreSQL, MySQL, MongoDB).
    - Sub-millisecond in-memory TTL caching for hot middleware reads (ban checks, RBAC roles, settings).
    - Transparent cache invalidation on write events.
    """

    def __init__(
        self,
        db_path_or_adapter: Optional[Union[str, BaseDatabaseAdapter]] = None,
        db_type: Optional[str] = None,
        url: Optional[str] = None,
        cache_ttl: float = 60.0,
        **kwargs
    ):
        if isinstance(db_path_or_adapter, BaseDatabaseAdapter):
            self.adapter = db_path_or_adapter
        elif isinstance(db_path_or_adapter, str) and not db_type and not url:
            # Backward-compatible SQLite file path initialization
            self.adapter = SQLiteAdapter(db_path=db_path_or_adapter)
        else:
            self.adapter = create_database_adapter(
                db_type=db_type,
                url=url,
                sqlite_path=db_path_or_adapter if isinstance(db_path_or_adapter, str) else None,
                **kwargs
            )

        # Ultra-fast in-memory TTL cache for hot lookups
        self.cache = MemoryTTLCache(default_ttl_seconds=cache_ttl)

    @classmethod
    def from_config(cls, db_config, cache_ttl: float = 60.0) -> "DatabaseSession":
        """Factory constructor using strongly-typed application DatabaseConfig."""
        adapter = create_database_adapter(
            db_type=getattr(db_config, "db_type", None),
            url=getattr(db_config, "url", None),
            sqlite_path=getattr(db_config, "sqlite_path", "bot_database.sqlite3"),
            host=getattr(db_config, "host", "localhost"),
            port=getattr(db_config, "port", 0),
            user=getattr(db_config, "user", ""),
            password=getattr(db_config, "password", ""),
            database=getattr(db_config, "database", "telecore_bot")
        )
        return cls(db_path_or_adapter=adapter, cache_ttl=cache_ttl)

    async def init_models(self) -> None:
        """Initializes tables, collections, and indexes on the configured database."""
        await self.adapter.init_models()

    async def upsert_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str] = None,
        language_code: Optional[str] = "en",
        referrer_id: Optional[int] = None
    ) -> bool:
        """Registers or updates user details; invalidates cached user entry."""
        self.cache.delete(f"user:{user_id}")
        return await self.adapter.upsert_user(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            referrer_id=referrer_id
        )

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        cache_key = f"user:{user_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        user = await self.adapter.get_user(user_id)
        if user is not None:
            self.cache.set(cache_key, user, ttl=30.0)
        return user

    async def get_all_active_user_ids(self) -> List[int]:
        return await self.adapter.get_all_active_user_ids()

    async def get_all_users(self) -> List[Dict[str, Any]]:
        return await self.adapter.get_all_users()

    async def set_ban(self, user_id: int, is_banned: bool = True, reason: Optional[str] = None) -> bool:
        """Bans/unbans user and immediately evicts cached ban & user status."""
        ok = await self.adapter.set_ban(user_id, is_banned, reason)
        self.cache.delete(f"ban:{user_id}")
        self.cache.delete(f"user:{user_id}")
        return ok

    async def is_user_banned(self, user_id: int) -> bool:
        """Cached sub-millisecond check for global ban middleware."""
        cache_key = f"ban:{user_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        is_banned = await self.adapter.is_user_banned(user_id)
        self.cache.set(cache_key, is_banned, ttl=60.0)
        return is_banned

    async def log_event(self, user_id: int, event_name: str) -> None:
        await self.adapter.log_event(user_id, event_name)

    async def get_stats(self) -> Dict[str, Any]:
        return await self.adapter.get_stats()

    async def get_referral_count(self, user_id: int) -> int:
        return await self.adapter.get_referral_count(user_id)

    async def set_user_topic(self, user_id: int, topic_id: int) -> bool:
        self.cache.delete(f"topic:{user_id}")
        return await self.adapter.set_user_topic(user_id, topic_id)

    async def get_user_topic(self, user_id: int) -> Optional[int]:
        cache_key = f"topic:{user_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        topic_id = await self.adapter.get_user_topic(user_id)
        if topic_id is not None:
            self.cache.set(cache_key, topic_id, ttl=300.0)
        return topic_id

    async def get_user_by_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        return await self.adapter.get_user_by_topic(topic_id)

    # --- Role-Based Access Control (RBAC) ---

    async def set_user_role(self, user_id: int, role: str) -> bool:
        """Updates role and purges role cache."""
        ok = await self.adapter.set_user_role(user_id, role)
        self.cache.delete(f"role:{user_id}")
        self.cache.delete(f"user:{user_id}")
        return ok

    async def get_user_role(self, user_id: int) -> str:
        """Cached sub-millisecond check for RBAC filters and middlewares."""
        cache_key = f"role:{user_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        role = await self.adapter.get_user_role(user_id)
        self.cache.set(cache_key, role, ttl=60.0)
        return role

    async def get_staff_users(self) -> List[Dict[str, Any]]:
        return await self.adapter.get_staff_users()

    # --- Dynamic In-Bot System Settings (Overrides .env) ---

    async def set_setting(self, key: str, value: str) -> None:
        """Updates dynamic setting and purges setting cache."""
        await self.adapter.set_setting(key, value)
        self.cache.delete(f"setting:{key}")

    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Cached sub-millisecond check for dynamic settings."""
        cache_key = f"setting:{key}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        val = await self.adapter.get_setting(key, default)
        if val is not None:
            self.cache.set(cache_key, val, ttl=30.0)
        return val

    async def get_all_settings(self) -> Dict[str, str]:
        return await self.adapter.get_all_settings()

    async def close(self) -> None:
        """Releases database connections and pools."""
        await self.adapter.close()
        self.cache.clear()
