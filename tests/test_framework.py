import asyncio
import os
import tempfile
import unittest

from app.config import AppConfig, _parse_bool, _parse_list_ints
from app.database.session import DatabaseSession

class TestTeleCoreFramework(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        self.temp_file.close()
        self.db = DatabaseSession(self.temp_file.name)
        await self.db.init_models()

    async def asyncTearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_config_parsers(self):
        self.assertTrue(_parse_bool("true"))
        self.assertTrue(_parse_bool("1"))
        self.assertFalse(_parse_bool("false"))
        self.assertFalse(_parse_bool(None, default=False))

        ints = _parse_list_ints("123, 456, invalid, 789")
        self.assertEqual(ints, [123, 456, 789])

    async def test_database_user_upsert_and_referral(self):
        # 1. Register Referrer
        is_new_referrer = await self.db.upsert_user(
            user_id=1001,
            username="referrer_user",
            first_name="Referrer",
            last_name="Boss"
        )
        self.assertTrue(is_new_referrer)

        # 2. Register Referred User via deep link
        is_new_referee = await self.db.upsert_user(
            user_id=2002,
            username="referee_user",
            first_name="Friend",
            referrer_id=1001
        )
        self.assertTrue(is_new_referee)

        # 3. Check referral counter
        ref_count = await self.db.get_referral_count(1001)
        self.assertEqual(ref_count, 1)

        # 4. Log analytics event
        await self.db.log_event(2002, "test_event")

        # 5. Check stats
        stats = await self.db.get_stats()
        self.assertEqual(stats["total_users"], 2)
        self.assertEqual(stats["active_users"], 2)
        self.assertEqual(stats["total_events"], 1)

    async def test_ban_and_active_user_list(self):
        await self.db.upsert_user(user_id=3003, username="spammer", first_name="Spam")
        await self.db.set_ban(user_id=3003, is_banned=True)

        user = await self.db.get_user(3003)
        self.assertEqual(user["is_banned"], 1)

        active_users = await self.db.get_all_active_user_ids()
        self.assertNotIn(3003, active_users)

if __name__ == "__main__":
    unittest.main()
