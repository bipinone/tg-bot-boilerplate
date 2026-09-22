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

        # 6. Test get_all_users for CSV export
        all_users = await self.db.get_all_users()
        self.assertEqual(len(all_users), 2)
        self.assertEqual(all_users[0]["user_id"], 2002)

    async def test_ban_and_active_user_list(self):
        await self.db.upsert_user(user_id=3003, username="spammer", first_name="Spam")
        await self.db.set_ban(user_id=3003, is_banned=True, reason="Spamming links")

        user = await self.db.get_user(3003)
        self.assertEqual(user["is_banned"], 1)
        self.assertEqual(user["ban_reason"], "Spamming links")
        self.assertTrue(await self.db.is_user_banned(3003))

        active_users = await self.db.get_all_active_user_ids()
        self.assertNotIn(3003, active_users)

        # Unban test
        await self.db.set_ban(user_id=3003, is_banned=False)
        self.assertFalse(await self.db.is_user_banned(3003))

    async def test_dynamic_system_settings(self):
        # 1. Default fallback
        val = await self.db.get_setting("custom_key", "default_val")
        self.assertEqual(val, "default_val")

        # 2. Insert dynamic setting
        await self.db.set_setting("force_sub_enabled", "true")
        await self.db.set_setting("force_sub_channel", "@mychannel")

        # 3. Retrieve
        self.assertEqual(await self.db.get_setting("force_sub_enabled"), "true")
        self.assertEqual(await self.db.get_setting("force_sub_channel"), "@mychannel")

        # 4. Upsert/Update existing setting
        await self.db.set_setting("force_sub_enabled", "false")
        self.assertEqual(await self.db.get_setting("force_sub_enabled"), "false")

        # 5. Get all settings
        all_s = await self.db.get_all_settings()
        self.assertIn("force_sub_enabled", all_s)
        self.assertIn("force_sub_channel", all_s)

    async def test_rbac_roles_and_filters(self):
        from app.bot.filters.admin import IsAdminFilter, IsOwnerFilter
        from unittest.mock import MagicMock

        # Create normal user
        await self.db.upsert_user(user_id=5001, username="normal", first_name="Norm")
        self.assertEqual(await self.db.get_user_role(5001), "user")

        # Promote to Moderator, then Admin, then Owner
        await self.db.set_user_role(5001, "moderator")
        self.assertEqual(await self.db.get_user_role(5001), "moderator")

        await self.db.set_user_role(5001, "admin")
        self.assertEqual(await self.db.get_user_role(5001), "admin")

        staff = await self.db.get_staff_users()
        self.assertEqual(len(staff), 1)
        self.assertEqual(staff[0]["user_id"], 5001)

        # Test IsAdminFilter with DB
        admin_filter = IsAdminFilter()
        owner_filter = IsOwnerFilter()

        event_mock = MagicMock()
        event_mock.from_user.id = 5001

        # Role is 'admin' -> IsAdminFilter True, IsOwnerFilter False
        self.assertTrue(await admin_filter(event_mock, db=self.db))
        self.assertFalse(await owner_filter(event_mock, db=self.db))

        # Promote to 'owner' -> Both True
        await self.db.set_user_role(5001, "owner")
        self.assertTrue(await admin_filter(event_mock, db=self.db))
        self.assertTrue(await owner_filter(event_mock, db=self.db))

    async def test_telegram_log_service(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.services.logger import TelegramLogService

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(return_value=True)

        logger_service = TelegramLogService(mock_bot)
        logger_service.chat_id = -1001234567890
        logger_service.default_thread_id = 42

        # 1. Test log send with default topic thread_id
        await logger_service.send_log("Test log")
        mock_bot.send_message.assert_called_with(
            chat_id=-1001234567890,
            text="Test log",
            parse_mode="HTML",
            disable_web_page_preview=True,
            message_thread_id=42
        )

        # 2. Test log send without thread_id (normal group/channel)
        logger_service.default_thread_id = None
        await logger_service.send_log("Normal group log")
        mock_bot.send_message.assert_called_with(
            chat_id=-1001234567890,
            text="Normal group log",
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        # 3. Test dynamic auto-creation of per-user forum topic
        mock_topic = MagicMock()
        mock_topic.message_thread_id = 999
        mock_bot.create_forum_topic = AsyncMock(return_value=mock_topic)

        await self.db.upsert_user(user_id=7777, username="newuser", first_name="Alex")
        thread_id = await logger_service.get_or_create_user_topic(7777, "Alex", "newuser", self.db)
        self.assertEqual(thread_id, 999)
        mock_bot.create_forum_topic.assert_called_with(
            chat_id=-1001234567890,
            name="Alex | 7777"
        )

        # Second call should retrieve from db without re-calling create_forum_topic
        mock_bot.create_forum_topic.reset_mock()
        cached_thread = await logger_service.get_or_create_user_topic(7777, "Alex", "newuser", self.db)
        self.assertEqual(cached_thread, 999)
        mock_bot.create_forum_topic.assert_not_called()

    async def test_health_server(self):
        from app.services.health import HealthServer
        server = HealthServer(self.db)
        self.assertIsNotNone(server.app)

    async def test_ban_check_middleware(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.bot.middlewares.ban import BanCheckMiddleware

        from aiogram.types import Message
        middleware = BanCheckMiddleware()
        mock_handler = AsyncMock(return_value="handler_reached")

        # 1. Normal active user should reach handler
        await self.db.upsert_user(user_id=6001, username="clean_user", first_name="Clean")
        clean_event = MagicMock(spec=Message)
        mock_user = MagicMock()
        mock_user.id = 6001
        mock_user.is_bot = False
        clean_event.from_user = mock_user
        clean_event.reply = AsyncMock()


        res = await middleware(mock_handler, clean_event, {"db": self.db})
        self.assertEqual(res, "handler_reached")

        # 2. Banned user should be blocked from reaching handler
        await self.db.set_ban(6001, is_banned=True, reason="Abuse detected")
        clean_event.reply.reset_mock()
        mock_handler.reset_mock()

        blocked_res = await middleware(mock_handler, clean_event, {"db": self.db})
        self.assertIsNone(blocked_res)
        mock_handler.assert_not_called()
        self.assertTrue(clean_event.reply.called)
        self.assertIn("Abuse detected", clean_event.reply.call_args[0][0])

        # 3. Maintenance mode check
        await self.db.set_ban(6001, is_banned=False)
        await self.db.set_setting("maintenance_mode", "true")
        mock_handler.reset_mock()
        clean_event.reply.reset_mock()

        maint_res = await middleware(mock_handler, clean_event, {"db": self.db})
        self.assertIsNone(maint_res)
        mock_handler.assert_not_called()
        self.assertTrue(clean_event.reply.called)
        self.assertIn("Maintenance Mode", clean_event.reply.call_args[0][0])

        # 4. Staff bypasses maintenance mode
        await self.db.set_user_role(6001, "admin")
        mock_handler.reset_mock()

        staff_res = await middleware(mock_handler, clean_event, {"db": self.db})
        self.assertEqual(staff_res, "handler_reached")
        mock_handler.assert_called_once()

    def test_memory_ttl_cache(self):
        from app.database.cache import MemoryTTLCache
        import time

        cache = MemoryTTLCache(default_ttl_seconds=0.1)
        cache.set("key1", "val1")
        self.assertEqual(cache.get("key1"), "val1")

        # Test expiration
        time.sleep(0.15)
        self.assertIsNone(cache.get("key1"))

        # Test deletion
        cache.set("key2", "val2", ttl=10.0)
        cache.delete("key2")
        self.assertIsNone(cache.get("key2"))

    async def test_database_caching_and_invalidation(self):
        # 1. Ban caching
        await self.db.upsert_user(user_id=8001, username="test_cache", first_name="CacheTest")
        self.assertFalse(await self.db.is_user_banned(8001))
        # Ensure it's in cache
        self.assertEqual(self.db.cache.get("ban:8001"), False)

        # Ban user -> should invalidate cache and return True
        await self.db.set_ban(8001, is_banned=True, reason="Rule violation")
        self.assertIsNone(self.db.cache.get("ban:8001"))
        self.assertTrue(await self.db.is_user_banned(8001))

        # 2. Setting caching
        await self.db.set_setting("speed_test", "100")
        self.assertEqual(await self.db.get_setting("speed_test"), "100")
        self.assertEqual(self.db.cache.get("setting:speed_test"), "100")

        # Updating setting invalidates cache
        await self.db.set_setting("speed_test", "200")
        self.assertIsNone(self.db.cache.get("setting:speed_test"))
        self.assertEqual(await self.db.get_setting("speed_test"), "200")

        # 3. Role caching
        await self.db.set_user_role(8001, "moderator")
        self.assertEqual(await self.db.get_user_role(8001), "moderator")
        self.assertEqual(self.db.cache.get("role:8001"), "moderator")

        await self.db.set_user_role(8001, "admin")
        self.assertIsNone(self.db.cache.get("role:8001"))
        self.assertEqual(await self.db.get_user_role(8001), "admin")

    def test_multi_database_factory(self):
        from app.database.factory import create_database_adapter
        from app.database.adapters.sqlite import SQLiteAdapter
        from app.database.adapters.postgres import PostgresAdapter
        from app.database.adapters.mysql import MySQLAdapter
        from app.database.adapters.mongo import MongoAdapter

        # 1. SQLite
        sqlite_ad = create_database_adapter(db_type="sqlite")
        self.assertIsInstance(sqlite_ad, SQLiteAdapter)

        # 2. Postgres
        pg_ad = create_database_adapter(url="postgresql://user:pass@localhost:5432/testdb")
        self.assertIsInstance(pg_ad, PostgresAdapter)

        # 3. MySQL
        mysql_ad = create_database_adapter(url="mysql://user:pass@localhost:3306/testdb")
        self.assertIsInstance(mysql_ad, MySQLAdapter)

        # 4. Mongo
        mongo_ad = create_database_adapter(url="mongodb://localhost:27017/testdb")
        self.assertIsInstance(mongo_ad, MongoAdapter)

        # 5. Fallback auto-detection from db_type string
        mongo_ad2 = create_database_adapter(db_type="mongo")
        self.assertIsInstance(mongo_ad2, MongoAdapter)

    def test_broadcast_engine_helpers(self):
        from app.modules.broadcast.router import render_progress_bar, broadcast_state, get_broadcast_controls_markup

        # 1. Progress Bar
        bar_0 = render_progress_bar(0, 100, length=10)
        self.assertIn("0.0%", bar_0)

        bar_50 = render_progress_bar(50, 100, length=10)
        self.assertIn("50.0%", bar_50)
        self.assertIn("█████", bar_50)

        bar_100 = render_progress_bar(100, 100, length=10)
        self.assertIn("100.0%", bar_100)
        self.assertIn("██████████", bar_100)

        # 2. Control Markup
        kb_running = get_broadcast_controls_markup(is_paused=False)
        self.assertEqual(kb_running.inline_keyboard[0][0].text, "⏸️ Pause")

        kb_paused = get_broadcast_controls_markup(is_paused=True)
        self.assertEqual(kb_paused.inline_keyboard[0][0].text, "▶️ Resume")

        # 3. State verification
        self.assertIn("running", broadcast_state)
        self.assertIn("paused", broadcast_state)
        self.assertIn("cancelled", broadcast_state)

    def test_i18n_service(self):
        from app.modules.i18n.service import i18n

        # 1. English
        en_text = i18n.t("ping", lang="en", latency=45)
        self.assertIn("45ms", en_text)
        self.assertIn("Pong!", en_text)

        # 2. Hindi
        hi_text = i18n.t("ping", lang="hi", latency=45)
        self.assertIn("पोंग!", hi_text)

        # 3. Missing key fallback
        unknown = i18n.t("non_existent_key", lang="hi")
        self.assertEqual(unknown, "non_existent_key")

    async def test_group_management(self):
        # 1. Register group
        is_new = await self.db.upsert_group(chat_id=-100999888, title="Test Community", chat_type="supergroup")
        self.assertTrue(is_new)

        # 2. Fetch group
        grp = await self.db.get_group(-100999888)
        self.assertIsNotNone(grp)
        self.assertEqual(grp["title"], "Test Community")

        # 3. Active group list
        active_groups = await self.db.get_all_active_group_ids()
        self.assertIn(-100999888, active_groups)

        # 4. Group settings
        await self.db.set_group_setting(-100999888, "welcome_msg", "Hello world")
        val = await self.db.get_group_setting(-100999888, "welcome_msg")
        self.assertEqual(val, "Hello world")

    async def test_subscriptions_and_entitlements(self):
        await self.db.upsert_user(user_id=9001, username="sub_user", first_name="Subber")

        # 1. Initially no active subscription
        self.assertFalse(await self.db.is_subscription_active(9001))

        # 2. Create 30-day Pro subscription
        sub = await self.db.create_subscription(user_id=9001, plan="pro", duration_days=30)
        self.assertEqual(sub["plan"], "pro")
        self.assertTrue(sub["is_active"])

        # 3. Verify active status
        self.assertTrue(await self.db.is_subscription_active(9001))
        fetched_sub = await self.db.get_user_subscription(9001)
        self.assertIsNotNone(fetched_sub)
        self.assertEqual(fetched_sub["plan"], "pro")

    async def test_task_scheduler(self):
        from unittest.mock import MagicMock, AsyncMock
        from app.modules.scheduler.service import TaskScheduler

        mock_bot = MagicMock()
        scheduler = TaskScheduler(mock_bot, self.db)
        dummy_task = AsyncMock()

        scheduler.add_job("test_job", dummy_task, interval_seconds=0.1)
        await scheduler.start()
        self.assertTrue(scheduler._running)
        await asyncio.sleep(0.15)
        self.assertTrue(dummy_task.called)
        await scheduler.stop()
        self.assertFalse(scheduler._running)

    def test_cli_make_module(self):
        import shutil
        from pathlib import Path
        from app.cli import make_module

        test_module_name = "test_temp_mod"
        module_path = Path("app/modules") / test_module_name

        try:
            make_module(test_module_name)
            self.assertTrue(module_path.exists())
            self.assertTrue((module_path / "__init__.py").exists())
            self.assertTrue((module_path / "handlers.py").exists())
            self.assertTrue((module_path / "services.py").exists())
            self.assertTrue((module_path / "keyboards.py").exists())
            self.assertTrue((module_path / "schemas.py").exists())
            self.assertTrue((module_path / "config.py").exists())
        finally:
            if module_path.exists():
                shutil.rmtree(module_path)

    async def test_setup_bot_metadata(self):
        from unittest.mock import AsyncMock
        from app.bot.setup_commands import setup_bot_metadata

        mock_bot = AsyncMock()
        mock_bot.set_my_commands = AsyncMock()
        mock_bot.set_my_description = AsyncMock()
        mock_bot.set_my_short_description = AsyncMock()

        await setup_bot_metadata(mock_bot)

        self.assertTrue(mock_bot.set_my_commands.called)
        self.assertTrue(mock_bot.set_my_description.called)
        self.assertTrue(mock_bot.set_my_short_description.called)

        # Verify bipinone credit in description
        desc_args = mock_bot.set_my_description.call_args[1]
        self.assertIn("bipinone", desc_args["description"].lower())

        # Verify bipinone credit in short description
        short_desc_args = mock_bot.set_my_short_description.call_args[1]
        self.assertIn("bipinone", short_desc_args["short_description"].lower())


if __name__ == "__main__":
    unittest.main()





