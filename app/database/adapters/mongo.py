import datetime
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from app.database.base import BaseDatabaseAdapter

logger = logging.getLogger(__name__)

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    AsyncIOMotorClient = None

class MongoAdapter(BaseDatabaseAdapter):
    """Production-grade MongoDB / DocumentDB adapter powered by motor async driver."""

    def __init__(self, uri: str = "mongodb://localhost:27017/telecore_bot", db_name: Optional[str] = None):
        if not AsyncIOMotorClient:
            raise ImportError("motor is required to use MongoDB. Run: pip install motor pymongo")

        self.uri = uri
        if not db_name:
            parsed = urlparse(uri)
            db_name = parsed.path.lstrip("/") or "telecore_bot"
        self.db_name = db_name

        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    def _get_db(self):
        if self.client is None:
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client[self.db_name]
        return self.db

    async def init_models(self) -> None:
        db = self._get_db()
        # Create indexes for ultra-fast query performance
        await db.users.create_index("user_id", unique=True)
        await db.users.create_index("referrer_id")
        await db.users.create_index("topic_id")
        await db.system_settings.create_index("key", unique=True)
        await db.analytics_events.create_index("user_id")
        logger.info("MongoDB collections and indexes initialized successfully for DB: %s", self.db_name)

    async def upsert_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str] = None,
        language_code: Optional[str] = "en",
        referrer_id: Optional[int] = None
    ) -> bool:
        db = self._get_db()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        res = await db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "language_code": language_code,
                    "updated_at": now
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "referrer_id": referrer_id,
                    "points": 0,
                    "topic_id": None,
                    "role": "user",
                    "is_banned": False,
                    "ban_reason": None,
                    "created_at": now
                }
            },
            upsert=True
        )
        return res.upserted_id is not None

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        db = self._get_db()
        doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        return doc

    async def get_all_active_user_ids(self) -> List[int]:
        db = self._get_db()
        cursor = db.users.find({"is_banned": {"$ne": True}}, {"user_id": 1})
        docs = await cursor.to_list(length=None)
        return [d["user_id"] for d in docs]

    async def get_all_users(self) -> List[Dict[str, Any]]:
        db = self._get_db()
        cursor = db.users.find({}, {"_id": 0}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def set_ban(self, user_id: int, is_banned: bool = True, reason: Optional[str] = None) -> bool:
        db = self._get_db()
        res = await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": is_banned, "ban_reason": reason if is_banned else None}}
        )
        return res.matched_count > 0

    async def is_user_banned(self, user_id: int) -> bool:
        db = self._get_db()
        doc = await db.users.find_one({"user_id": user_id}, {"is_banned": 1})
        return bool(doc.get("is_banned", False)) if doc else False

    async def log_event(self, user_id: int, event_name: str) -> None:
        db = self._get_db()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await db.analytics_events.insert_one({
            "user_id": user_id,
            "event_name": event_name,
            "created_at": now
        })

    async def get_stats(self) -> Dict[str, Any]:
        db = self._get_db()
        total_users = await db.users.count_documents({})
        banned_users = await db.users.count_documents({"is_banned": True})
        total_events = await db.analytics_events.count_documents({})

        return {
            "total_users": total_users,
            "banned_users": banned_users,
            "active_users": total_users - banned_users,
            "total_events": total_events
        }

    async def get_referral_count(self, user_id: int) -> int:
        db = self._get_db()
        return await db.users.count_documents({"referrer_id": user_id})

    async def set_user_topic(self, user_id: int, topic_id: int) -> bool:
        db = self._get_db()
        res = await db.users.update_one({"user_id": user_id}, {"$set": {"topic_id": topic_id}})
        return res.matched_count > 0

    async def get_user_topic(self, user_id: int) -> Optional[int]:
        db = self._get_db()
        doc = await db.users.find_one({"user_id": user_id}, {"topic_id": 1})
        return doc.get("topic_id") if doc else None

    async def get_user_by_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        db = self._get_db()
        doc = await db.users.find_one({"topic_id": topic_id}, {"_id": 0})
        return doc

    async def set_user_role(self, user_id: int, role: str) -> bool:
        db = self._get_db()
        res = await db.users.update_one({"user_id": user_id}, {"$set": {"role": role.lower()}})
        return res.matched_count > 0

    async def get_user_role(self, user_id: int) -> str:
        db = self._get_db()
        doc = await db.users.find_one({"user_id": user_id}, {"role": 1})
        return doc.get("role", "user") if doc else "user"

    async def get_staff_users(self) -> List[Dict[str, Any]]:
        db = self._get_db()
        cursor = db.users.find(
            {"role": {"$in": ["owner", "admin", "moderator"]}},
            {"_id": 0, "user_id": 1, "username": 1, "first_name": 1, "role": 1}
        )
        return await cursor.to_list(length=None)

    async def set_setting(self, key: str, value: str) -> None:
        db = self._get_db()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await db.system_settings.update_one(
            {"key": key},
            {"$set": {"value": str(value), "updated_at": now}},
            upsert=True
        )

    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        db = self._get_db()
        doc = await db.system_settings.find_one({"key": key}, {"value": 1})
        return doc["value"] if doc and "value" in doc else default

    async def get_all_settings(self) -> Dict[str, str]:
        db = self._get_db()
        cursor = db.system_settings.find({}, {"_id": 0, "key": 1, "value": 1})
        docs = await cursor.to_list(length=None)
        return {d["key"]: d["value"] for d in docs}

    async def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
