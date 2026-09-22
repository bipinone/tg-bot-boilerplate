import datetime
import logging
import aiosqlite
from typing import Optional, Dict, Any, List
from app.database.base import BaseDatabaseAdapter

logger = logging.getLogger(__name__)

class SQLiteAdapter(BaseDatabaseAdapter):
    """SQLite database adapter powered by aiosqlite."""

    def __init__(self, db_path: str = "bot_database.sqlite3"):
        self.db_path = db_path

    async def init_models(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'en',
                    referrer_id INTEGER,
                    points INTEGER DEFAULT 0,
                    topic_id INTEGER,
                    role TEXT DEFAULT 'user',
                    is_banned BOOLEAN DEFAULT 0,
                    ban_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Backwards compatibility auto-migrations
            for col, col_type in [
                ("topic_id", "INTEGER"),
                ("role", "TEXT DEFAULT 'user'"),
                ("ban_reason", "TEXT")
            ]:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            await db.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    event_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
            logger.info("SQLite schema initialized successfully at %s", self.db_path)

    async def upsert_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str] = None,
        language_code: Optional[str] = "en",
        referrer_id: Optional[int] = None
    ) -> bool:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()

            if row is None:
                await db.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, language_code, referrer_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, language_code, referrer_id, now, now))
                await db.commit()
                return True
            else:
                await db.execute("""
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, language_code = ?, updated_at = ?
                    WHERE user_id = ?
                """, (username, first_name, last_name, language_code, now, user_id))
                await db.commit()
                return False

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_active_user_ids(self) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users WHERE is_banned = 0") as cursor:
                rows = await cursor.fetchall()
                return [r[0] for r in rows]

    async def get_all_users(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT user_id, username, first_name, last_name, language_code, referrer_id, points, is_banned, created_at 
                FROM users ORDER BY created_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def set_ban(self, user_id: int, is_banned: bool = True, reason: Optional[str] = None) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE users SET is_banned = ?, ban_reason = ? WHERE user_id = ?",
                (1 if is_banned else 0, reason if is_banned else None, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def is_user_banned(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                return bool(row[0]) if row else False

    async def log_event(self, user_id: int, event_name: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO analytics_events (user_id, event_name) VALUES (?, ?)",
                (user_id, event_name)
            )
            await db.commit()

    async def get_stats(self) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cur:
                total_users = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1") as cur:
                banned_users = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM analytics_events") as cur:
                total_events = (await cur.fetchone())[0]

            return {
                "total_users": total_users,
                "banned_users": banned_users,
                "active_users": total_users - banned_users,
                "total_events": total_events
            }

    async def get_referral_count(self, user_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,)) as cur:
                return (await cur.fetchone())[0]

    async def set_user_topic(self, user_id: int, topic_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("UPDATE users SET topic_id = ? WHERE user_id = ?", (topic_id, user_id))
            await db.commit()
            return cursor.rowcount > 0

    async def get_user_topic(self, user_id: int) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT topic_id FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                return row[0] if row and row[0] else None

    async def get_user_by_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE topic_id = ?", (topic_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def set_user_role(self, user_id: int, role: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("UPDATE users SET role = ? WHERE user_id = ?", (role.lower(), user_id))
            await db.commit()
            return cursor.rowcount > 0

    async def get_user_role(self, user_id: int) -> str:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                return row[0] if row and row[0] else "user"

    async def get_staff_users(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT user_id, username, first_name, role 
                FROM users 
                WHERE role IN ('owner', 'admin', 'moderator')
            """) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def set_setting(self, key: str, value: str) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO system_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """, (key, str(value), now))
            await db.commit()

    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM system_settings WHERE key = ?", (key,)) as cur:
                row = await cur.fetchone()
                return row[0] if row and row[0] is not None else default

    async def get_all_settings(self) -> Dict[str, str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT key, value FROM system_settings") as cur:
                rows = await cur.fetchall()
                return {r[0]: r[1] for r in rows}

    async def close(self) -> None:
        pass
