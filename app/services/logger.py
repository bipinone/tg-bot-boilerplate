# TeleCore Telegram Bot Framework - Telegram Group & Topic Logging Service
# Author: bipinone (https://github.com/bipinone)
# Repository: https://github.com/bipinone/tg-bot-boilerplate

import logging
import datetime
from typing import Optional, List, Union, Dict, Any, Tuple
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from app.config import config

logger = logging.getLogger(__name__)

class TelegramLogService:
    """
    Asynchronous Telegram logging service with dynamic runtime database configuration.
    Supports:
    - Standard Groups & Channels (chat_id)
    - Specific Forum Topic in Supergroups (chat_id + thread_id)
    - Dynamic Per-User Dedicated Forum Topics (AUTO_CREATE_USER_TOPICS=true)
    - In-Bot Real-Time Runtime Controls (toggle logging, set channel/topic, test connection)
    """
    def __init__(self, bot: Bot, db=None):
        self.bot = bot
        self.db = db
        self.chat_id = config.logging.chat_id
        self.default_thread_id = config.logging.thread_id
        self.create_user_topics = config.logging.create_user_topics

    async def get_effective_config(self, db=None) -> Dict[str, Any]:
        """
        Dynamically resolves logging parameters:
        Prioritizes database runtime settings (allowing admin in-bot changes),
        falling back cleanly to .env configuration.
        """
        target_db = db or self.db
        enabled = True
        chat_id = self.chat_id
        thread_id = self.default_thread_id
        user_topics = getattr(self, "create_user_topics", True)
        chat_type = "channel_or_group"

        if target_db:
            db_enabled = await target_db.get_setting("log_enabled")
            if db_enabled is not None:
                enabled = db_enabled.lower() in ("true", "1", "yes", "on")
            elif not chat_id:
                enabled = False

            db_chat_id = await target_db.get_setting("log_chat_id")
            if db_chat_id is not None and db_chat_id.strip():
                val = db_chat_id.strip()
                try:
                    chat_id = int(val)
                except ValueError:
                    chat_id = val

            db_thread_id = await target_db.get_setting("log_thread_id")
            if db_thread_id is not None:
                cleaned = db_thread_id.strip()
                if cleaned in ("", "0", "off", "none"):
                    thread_id = None
                else:
                    try:
                        thread_id = int(cleaned)
                    except ValueError:
                        pass

            db_user_topics = await target_db.get_setting("log_user_topics")
            if db_user_topics is not None:
                user_topics = db_user_topics.lower() in ("true", "1", "yes", "on")

            db_chat_type = await target_db.get_setting("log_chat_type")
            if db_chat_type:
                chat_type = db_chat_type
        else:
            if not chat_id:
                enabled = False

        return {
            "enabled": enabled,
            "chat_id": chat_id,
            "thread_id": thread_id,
            "user_topics": user_topics,
            "chat_type": chat_type
        }

    async def test_connection(self, chat_id: Union[int, str], thread_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Sends an instant verification message to test permissions and connectivity.
        Returns (success: bool, message: str, chat_type: Optional[str]).
        """
        try:
            chat = await self.bot.get_chat(chat_id)
            title = chat.title or chat.username or str(chat_id)
            chat_type = chat.type

            now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            topic_info = f"\n• <b>Topic ID:</b> <code>{thread_id}</code>" if thread_id else ""
            test_msg = (
                "🧪 <b>TeleCore Logging Verification Test</b>\n\n"
                f"• <b>Status:</b> 🟢 Successfully Connected\n"
                f"• <b>Destination:</b> {title} (<code>{chat_id}</code>)\n"
                f"• <b>Chat Type:</b> <code>{chat_type}</code>{topic_info}\n"
                f"• <b>Timestamp:</b> <code>{now}</code>\n\n"
                "<i>Real-time system events, user registrations, and error alerts will be logged here.</i>"
            )
            kwargs = {
                "chat_id": chat_id,
                "text": test_msg,
                "parse_mode": "HTML"
            }
            if thread_id:
                kwargs["message_thread_id"] = thread_id

            await self.bot.send_message(**kwargs)
            return True, f"Verified connection to {title} ({chat_type})", chat_type
        except Exception as e:
            return False, str(e), None

    async def send_log(self, text: str, thread_id: Optional[int] = None) -> bool:
        """Sends a formatted log message to the dynamically configured Telegram chat/topic."""
        cfg = await self.get_effective_config()
        if not cfg["enabled"] or not cfg["chat_id"]:
            return False

        target_thread = thread_id if thread_id is not None else cfg["thread_id"]

        try:
            kwargs = {
                "chat_id": cfg["chat_id"],
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            if target_thread:
                kwargs["message_thread_id"] = target_thread

            await self.bot.send_message(**kwargs)
            return True
        except TelegramAPIError as e:
            logger.warning("Failed to deliver log to Telegram (chat: %s, thread: %s): %s", cfg["chat_id"], target_thread, e)
            return False
        except Exception as e:
            logger.error("Unexpected exception in TelegramLogService: %s", e)
            return False

    async def get_or_create_user_topic(
        self,
        user_id: int,
        first_name: str,
        username: Optional[str],
        db
    ) -> Optional[int]:
        """
        Creates a dedicated forum topic for each new user in the supergroup,
        or returns existing topic_id from database.
        """
        cfg = await self.get_effective_config(db=db)
        if not cfg["enabled"] or not cfg["chat_id"] or not cfg["user_topics"]:
            return None

        # Check existing topic in db
        existing_topic = await db.get_user_topic(user_id)
        if existing_topic:
            return existing_topic

        try:
            topic_name = f"{first_name} | {user_id}"[:128]
            topic = await self.bot.create_forum_topic(
                chat_id=cfg["chat_id"],
                name=topic_name
            )
            thread_id = topic.message_thread_id
            await db.set_user_topic(user_id, thread_id)
            logger.info("Created dedicated forum topic #%s for user %s (%s)", thread_id, user_id, first_name)
            return thread_id
        except Exception as e:
            logger.warning("Could not auto-create forum topic for user %s: %s", user_id, e)
            return None

    async def log_startup(self, bot_username: str, active_modules: List[str]):
        """Notifies log chat when the bot initializes."""
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        modules_str = ", ".join(f"<code>{m}</code>" for m in active_modules) if active_modules else "<i>None</i>"

        text = (
            "🚀 <b>TeleCore Bot Started</b>\n\n"
            f"• <b>Bot:</b> @{bot_username}\n"
            f"• <b>Mode:</b> <code>{'Webhook' if config.webhook.enabled else 'Polling'}</code>\n"
            f"• <b>Active Modules:</b> {modules_str}\n"
            f"• <b>Timestamp:</b> <code>{now}</code>"
        )
        await self.send_log(text)

    async def log_new_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: str,
        referrer_id: Optional[int] = None,
        db = None
    ):
        """Creates a dedicated topic for this user and drops initial profile info."""
        thread_id = None
        if db:
            thread_id = await self.get_or_create_user_topic(user_id, first_name, username, db)

        user_tag = f"@{username}" if username else f"<code>{user_id}</code>"
        ref_text = f"\n• <b>Referred By:</b> <code>{referrer_id}</code>" if referrer_id else ""

        text = (
            "👤 <b>New User Registered</b>\n\n"
            f"• <b>User:</b> {first_name} ({user_tag})\n"
            f"• <b>User ID:</b> <code>{user_id}</code>"
            f"{ref_text}\n\n"
            "<i>All future activities and messages from this user will be logged in this dedicated topic!</i>"
        )
        await self.send_log(text, thread_id=thread_id)

    async def log_user_activity(
        self,
        user_id: int,
        first_name: str,
        username: Optional[str],
        activity_text: str,
        db
    ):
        """Logs any user message or action directly to their personal topic thread."""
        thread_id = await self.get_or_create_user_topic(user_id, first_name, username, db)
        log_entry = f"💬 <b>Activity:</b>\n<code>{activity_text}</code>"
        await self.send_log(log_entry, thread_id=thread_id)

    async def log_error(self, error_message: str, user_id: Optional[int] = None, command: Optional[str] = None):
        """Logs an unexpected exception/error to the log channel or specific error topic."""
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        user_info = f"\n• <b>User ID:</b> <code>{user_id}</code>" if user_id else ""
        cmd_info = f"\n• <b>Command / Text:</b> <code>{command}</code>" if command else ""

        text = (
            "🚨 <b>Application Error Caught</b>\n\n"
            f"• <b>Error:</b> <code>{error_message}</code>"
            f"{user_info}"
            f"{cmd_info}\n"
            f"• <b>Timestamp:</b> <code>{now}</code>"
        )
        await self.send_log(text)

    async def log_broadcast_complete(self, sent: int, blocked: int, failed: int):
        """Logs broadcast summary."""
        text = (
            "📢 <b>Broadcast Execution Summary</b>\n\n"
            f"• <b>Delivered:</b> <code>{sent}</code>\n"
            f"• <b>Blocked/Deleted:</b> <code>{blocked}</code>\n"
            f"• <b>Failed:</b> <code>{failed}</code>"
        )
        await self.send_log(text)
