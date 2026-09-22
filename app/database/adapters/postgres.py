import datetime
import logging
from typing import Optional, Dict, Any, List
from app.database.base import BaseDatabaseAdapter

logger = logging.getLogger(__name__)

try:
    import asyncpg
except ImportError:
    asyncpg = None

class PostgresAdapter(BaseDatabaseAdapter):
    """Production-grade PostgreSQL database adapter with asyncpg connection pooling."""

    def __init__(self, dsn: str, min_connections: int = 5, max_connections: int = 20):
        if not asyncpg:
            raise ImportError("asyncpg is required to use PostgreSQL. Run: pip install asyncpg")
        self.dsn = dsn
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: Optional[asyncpg.Pool] = None

    async def _get_pool(self) -> asyncpg.Pool:
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=self.min_connections,
                max_size=self.max_connections
            )
        return self.pool

    async def init_models(self) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT NOT NULL,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'en',
                    referrer_id BIGINT,
                    points INTEGER DEFAULT 0,
                    topic_id BIGINT,
                    role TEXT DEFAULT 'user',
                    is_banned BOOLEAN DEFAULT FALSE,
                    ban_reason TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS analytics_events (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    event_name TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """)
        logger.info("PostgreSQL schema initialized successfully with connection pool.")

    async def upsert_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str] = None,
        language_code: Optional[str] = "en",
        referrer_id: Optional[int] = None
    ) -> bool:
        pool = await self._get_pool()
        now = datetime.datetime.now(datetime.timezone.utc)
        async with pool.acquire() as conn:
            existing = await conn.fetchrow("SELECT user_id FROM users WHERE user_id = $1", user_id)
            if existing is None:
                await conn.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, language_code, referrer_id, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, user_id, username, first_name, last_name, language_code, referrer_id, now, now)
                return True
            else:
                await conn.execute("""
                    UPDATE users
                    SET username = $1, first_name = $2, last_name = $3, language_code = $4, updated_at = $5
                    WHERE user_id = $6
                """, username, first_name, last_name, language_code, now, user_id)
                return False

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            return dict(row) if row else None

    async def get_all_active_user_ids(self) -> List[int]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM users WHERE is_banned = FALSE")
            return [r["user_id"] for r in rows]

    async def get_all_users(self) -> List[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, username, first_name, last_name, language_code, referrer_id, points, is_banned, created_at 
                FROM users ORDER BY created_at DESC
            """)
            return [dict(r) for r in rows]

    async def set_ban(self, user_id: int, is_banned: bool = True, reason: Optional[str] = None) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            res = await conn.execute(
                "UPDATE users SET is_banned = $1, ban_reason = $2 WHERE user_id = $3",
                is_banned, reason if is_banned else None, user_id
            )
            # res format: 'UPDATE <count>'
            return int(res.split()[1]) > 0

    async def is_user_banned(self, user_id: int) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT is_banned FROM users WHERE user_id = $1", user_id)
            return bool(val) if val is not None else False

    async def log_event(self, user_id: int, event_name: str) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO analytics_events (user_id, event_name) VALUES ($1, $2)",
                user_id, event_name
            )

    async def get_stats(self) -> Dict[str, Any]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            banned_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_banned = TRUE")
            total_events = await conn.fetchval("SELECT COUNT(*) FROM analytics_events")
            return {
                "total_users": total_users,
                "banned_users": banned_users,
                "active_users": total_users - banned_users,
                "total_events": total_events
            }

    async def get_referral_count(self, user_id: int) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT COUNT(*) FROM users WHERE referrer_id = $1", user_id)
            return val or 0

    async def set_user_topic(self, user_id: int, topic_id: int) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            res = await conn.execute("UPDATE users SET topic_id = $1 WHERE user_id = $2", topic_id, user_id)
            return int(res.split()[1]) > 0

    async def get_user_topic(self, user_id: int) -> Optional[int]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT topic_id FROM users WHERE user_id = $1", user_id)
            return val

    async def get_user_by_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE topic_id = $1", topic_id)
            return dict(row) if row else None

    async def set_user_role(self, user_id: int, role: str) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            res = await conn.execute("UPDATE users SET role = $1 WHERE user_id = $2", role.lower(), user_id)
            return int(res.split()[1]) > 0

    async def get_user_role(self, user_id: int) -> str:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT role FROM users WHERE user_id = $1", user_id)
            return val if val else "user"

    async def get_staff_users(self) -> List[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, username, first_name, role 
                FROM users 
                WHERE role IN ('owner', 'admin', 'moderator')
            """)
            return [dict(r) for r in rows]

    async def set_setting(self, key: str, value: str) -> None:
        pool = await self._get_pool()
        now = datetime.datetime.now(datetime.timezone.utc)
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO system_settings (key, value, updated_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at
            """, key, str(value), now)

    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT value FROM system_settings WHERE key = $1", key)
            return val if val is not None else default

    async def get_all_settings(self) -> Dict[str, str]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT key, value FROM system_settings")
            return {r["key"]: r["value"] for r in rows}

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
