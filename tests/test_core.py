import asyncio
import os
import tempfile
import unittest
from bot.database.db import Database
from bot.middlewares.rate_limit import RateLimiter

class TestTeleCore(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        await self.db.init()

    async def asyncTearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    async def test_user_registration_and_stats(self):
        # Register new user
        is_new = await self.db.register_user(
            user_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        self.assertTrue(is_new)

        # Re-register same user updates count
        is_new_again = await self.db.register_user(
            user_id=12345,
            username="testuser_updated",
            first_name="Test",
            last_name="User"
        )
        self.assertFalse(is_new_again)

        # Check user fetch
        user = await self.db.get_user(12345)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser_updated")
        self.assertEqual(user["message_count"], 2)

        # Check stats
        stats = await self.db.get_statistics()
        self.assertEqual(stats["total_users"], 1)
        self.assertEqual(stats["active_users"], 1)
        self.assertEqual(stats["banned_users"], 0)

    async def test_ban_unban(self):
        await self.db.register_user(999, "baduser", "Bad", None)
        await self.db.set_ban_status(999, is_banned=True)

        user = await self.db.get_user(999)
        self.assertEqual(user["is_banned"], 1)

        # Should not be in broadcast list
        active_ids = await self.db.get_all_user_ids()
        self.assertNotIn(999, active_ids)

        # Unban
        await self.db.set_ban_status(999, is_banned=False)
        active_ids_after = await self.db.get_all_user_ids()
        self.assertIn(999, active_ids_after)

    def test_rate_limiter(self):
        limiter = RateLimiter(limit_seconds=0.5)
        self.assertFalse(limiter.is_rate_limited(101))
        # Second call immediately should be limited
        self.assertTrue(limiter.is_rate_limited(101))

if __name__ == "__main__":
    unittest.main()
