import logging
import datetime
from typing import Optional, List
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from app.config import config

logger = logging.getLogger(__name__)

class TelegramLogService:
    """
    Asynchronous Telegram logging service.
    Supports:
    - Standard Groups & Channels (LOG_CHAT_ID)
    - Static Forum Topic (LOG_CHAT_ID + LOG_THREAD_ID)
    - Dynamic Per-User Forum Topics (AUTO_CREATE_USER_TOPICS=true)
      Automatically creates a dedicated Forum Topic for each new user!
    """
    def __init__(self, bot: Bot):
        self.bot = bot
        self.chat_id = config.logging.chat_id
        self.default_thread_id = config.logging.thread_id

    async def send_log(self, text: str, thread_id: Optional[int] = None) -> bool:
        """Sends a formatted log message to the configured Telegram chat/topic."""
        if not self.chat_id:
            return False

        target_thread = thread_id if thread_id is not None else self.default_thread_id

        try:
            kwargs = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            if target_thread:
                kwargs["message_thread_id"] = target_thread

            await self.bot.send_message(**kwargs)
            return True
        except TelegramAPIError as e:
            logger.warning("Failed to deliver log to Telegram (chat: %s, thread: %s): %s", self.chat_id, target_thread, e)
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
        if not self.chat_id or not config.logging.create_user_topics:
            return None

        # Check existing topic in db
        existing_topic = await db.get_user_topic(user_id)
        if existing_topic:
            return existing_topic

        try:
            topic_name = f"{first_name} | {user_id}"[:128]
            topic = await self.bot.create_forum_topic(
                chat_id=self.chat_id,
                name=topic_name
            )
            thread_id = topic.message_thread_id
            await db.set_user_topic(user_id, thread_id)
            logger.info("Created dedicated forum topic #%s for user %s (%s)", thread_id, user_id, first_name)
            return thread_id
        except Exception as e:
            logger.warning("Could not auto-create forum topic for user %s (chat may not be a forum): %s", user_id, e)
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
