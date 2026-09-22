import datetime
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from app.database.base import BaseDatabaseAdapter

logger = logging.getLogger(__name__)

try:
    import aiomysql
except ImportError:
    aiomysql = None

class MySQLAdapter(BaseDatabaseAdapter):
    """Production-grade MySQL database adapter with aiomysql connection pooling."""

    def __init__(
        self,
        url: Optional[str] = None,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        db: str = "telecore_bot",
        minsize: int = 5,
        maxsize: int = 20
    ):
        if not aiomysql:
            raise ImportError("aiomysql is required to use MySQL. Run: pip install aiomysql PyMySQL")

        if url:
            parsed = urlparse(url)
            self.host = parsed.hostname or host
            self.port = parsed.port or port
            self.user = parsed.username or user
            self.password = parsed.password or password
            self.db = parsed.path.lstrip("/") or db
        else:
            self.host = host
            self.port = port
            self.user = user
            self.password = password
            self.db = db

        self.minsize = minsize
        self.maxsize = maxsize
        self.pool: Optional[aiomysql.Pool] = None

    async def _get_pool(self) -> aiomysql.Pool:
        if not self.pool:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.db,
                minsize=self.minsize,
                maxsize=self.maxsize,
                autocommit=True,
                cursorclass=aiomysql.DictCursor
            )
        return self.pool

    async def init_models(self) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        first_name VARCHAR(255) NOT NULL,
                        last_name VARCHAR(255),
                        language_code VARCHAR(16) DEFAULT 'en',
                        referrer_id BIGINT,
                        points INT DEFAULT 0,
                        topic_id BIGINT,
                        role VARCHAR(32) DEFAULT 'user',
                        is_banned TINYINT(1) DEFAULT 0,
                        ban_reason TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        event_name VARCHAR(255) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS system_settings (
                        `key` VARCHAR(255) PRIMARY KEY,
                        `value` TEXT NOT NULL,
                        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
        logger.info("MySQL schema initialized successfully.")

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
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                existing = await cur.fetchone()
                if existing is None:
                    await cur.execute("""
                        INSERT INTO users (user_id, username, first_name, last_name, language_code, referrer_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, username, first_name, last_name, language_code, referrer_id, now, now))
                    return True
                else:
                    await cur.execute("""
                        UPDATE users
                        SET username = %s, first_name = %s, last_name = %s, language_code = %s, updated_at = %s
                        WHERE user_id = %s
                    """, (username, first_name, last_name, language_code, now, user_id))
                    return False

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                return await cur.fetchone()

    async def get_all_active_user_ids(self) -> List[int]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id FROM users WHERE is_banned = 0")
                rows = await cur.fetchall()
                return [r["user_id"] for r in rows]

    async def get_all_users(self) -> List[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT user_id, username, first_name, last_name, language_code, referrer_id, points, is_banned, created_at 
                    FROM users ORDER BY created_at DESC
                """)
                return await cur.fetchall()

    async def set_ban(self, user_id: int, is_banned: bool = True, reason: Optional[str] = None) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET is_banned = %s, ban_reason = %s WHERE user_id = %s",
                    (1 if is_banned else 0, reason if is_banned else None, user_id)
                )
                return cur.rowcount > 0

    async def is_user_banned(self, user_id: int) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT is_banned FROM users WHERE user_id = %s", (user_id,))
                row = await cur.fetchone()
                return bool(row["is_banned"]) if row else False

    async def log_event(self, user_id: int, event_name: str) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO analytics_events (user_id, event_name) VALUES (%s, %s)",
                    (user_id, event_name)
                )

    async def get_stats(self) -> Dict[str, Any]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) as c FROM users")
                total_users = (await cur.fetchone())["c"]

                await cur.execute("SELECT COUNT(*) as c FROM users WHERE is_banned = 1")
                banned_users = (await cur.fetchone())["c"]

                await cur.execute("SELECT COUNT(*) as c FROM analytics_events")
                total_events = (await cur.fetchone())["c"]

                return {
                    "total_users": total_users,
                    "banned_users": banned_users,
                    "active_users": total_users - banned_users,
                    "total_events": total_events
                }

    async def get_referral_count(self, user_id: int) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) as c FROM users WHERE referrer_id = %s", (user_id,))
                row = await cur.fetchone()
                return row["c"] if row else 0

    async def set_user_topic(self, user_id: int, topic_id: int) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE users SET topic_id = %s WHERE user_id = %s", (topic_id, user_id))
                return cur.rowcount > 0

    async def get_user_topic(self, user_id: int) -> Optional[int]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT topic_id FROM users WHERE user_id = %s", (user_id,))
                row = await cur.fetchone()
                return row["topic_id"] if row else None

    async def get_user_by_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE topic_id = %s", (topic_id,))
                return await cur.fetchone()

    async def set_user_role(self, user_id: int, role: str) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE users SET role = %s WHERE user_id = %s", (role.lower(), user_id))
                return cur.rowcount > 0

    async def get_user_role(self, user_id: int) -> str:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
                row = await cur.fetchone()
                return row["role"] if row and row["role"] else "user"

    async def get_staff_users(self) -> List[Dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT user_id, username, first_name, role 
                    FROM users 
                    WHERE role IN ('owner', 'admin', 'moderator')
                """)
                return await cur.fetchall()

    async def set_setting(self, key: str, value: str) -> None:
        pool = await self._get_pool()
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO system_settings (`key`, `value`, `updated_at`)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE `value` = VALUES(`value`), `updated_at` = VALUES(`updated_at`)
                """, (key, str(value), now))

    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT `value` FROM system_settings WHERE `key` = %s", (key,))
                row = await cur.fetchone()
                return row["value"] if row else default

    async def get_all_settings(self) -> Dict[str, str]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT `key`, `value` FROM system_settings")
                rows = await cur.fetchall()
                return {r["key"]: r["value"] for r in rows}

    async def close(self) -> None:
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
