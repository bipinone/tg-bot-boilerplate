import aiosqlite
import datetime
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "bot_database.sqlite3"):
        self.db_path = db_path

    async def init(self):
        """Initializes database tables if they do not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 1,
                    is_banned BOOLEAN DEFAULT 0
                )
            """)
            await db.commit()
            logger.info("Database initialized successfully at %s", self.db_path)

    async def register_user(self, user_id: int, username: Optional[str], first_name: str, last_name: Optional[str]) -> bool:
        """Registers a new user or updates existing user's last_seen."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id, message_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()

            if row is None:
                await db.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, joined_at, last_seen, message_count)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (user_id, username, first_name, last_name, now, now))
                await db.commit()
                return True
            else:
                await db.execute("""
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, last_seen = ?, message_count = message_count + 1
                    WHERE user_id = ?
                """, (username, first_name, last_name, now, user_id))
                await db.commit()
                return False

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch user by telegram user_id."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_user_ids(self) -> List[int]:
        """Returns list of active, non-banned user IDs for broadcasting."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users WHERE is_banned = 0") as cursor:
                rows = await cursor.fetchall()
                return [r[0] for r in rows]

    async def set_ban_status(self, user_id: int, is_banned: bool = True) -> bool:
        """Ban or unban a user."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if is_banned else 0, user_id))
            await db.commit()
            return cursor.rowcount > 0

    async def get_statistics(self) -> Dict[str, Any]:
        """Calculates system and user statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total_users = (await cursor.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1") as cursor:
                banned_users = (await cursor.fetchone())[0]

            async with db.execute("SELECT SUM(message_count) FROM users") as cursor:
                total_messages = (await cursor.fetchone())[0] or 0

            return {
                "total_users": total_users,
                "banned_users": banned_users,
                "active_users": total_users - banned_users,
                "total_messages": total_messages
            }
