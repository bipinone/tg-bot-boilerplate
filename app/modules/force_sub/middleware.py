import os
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from app.config import config

logger = logging.getLogger(__name__)

class ForceSubMiddleware(BaseMiddleware):
    """
    Enforces channel membership before user can interact with the bot.
    Dynamically checks in-bot DB settings for instant toggling without restarts.
    """
    def __init__(self, channel_id: str = None):
        self.default_channel_id = channel_id or os.getenv("FORCE_SUB_CHANNEL", "")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, "from_user", None)
        if not user or user.is_bot:
            return await handler(event, data)

        db = data.get("db")
        bot: Bot = data.get("bot")

        # 1. Determine Dynamic Enabled Status & Channel ID
        is_enabled = config.modules.force_sub
        target_channel = self.default_channel_id
        target_url = os.getenv("FORCE_SUB_URL", "")

        if db:
            db_enabled = await db.get_setting("force_sub_enabled")
            if db_enabled is not None:
                is_enabled = db_enabled.lower() in ("true", "1", "yes", "on")

            db_channel = await db.get_setting("force_sub_channel")
            if db_channel:
                target_channel = db_channel

            db_url = await db.get_setting("force_sub_url")
            if db_url:
                target_url = db_url

        if not is_enabled or not target_channel:
            return await handler(event, data)

        # 2. Bypass Superadmins and Staff (Owner, Admin)
        if user.id in config.bot.admins:
            return await handler(event, data)

        if db:
            role = await db.get_user_role(user.id)
            if role in ("owner", "admin"):
                return await handler(event, data)

        # 3. Check Channel Membership
        if bot:
            try:
                member = await bot.get_chat_member(chat_id=target_channel, user_id=user.id)
                # Valid statuses: creator, administrator, member
                if member.status not in ("creator", "administrator", "member"):
                    if isinstance(event, Message):
                        if not target_url:
                            target_url = f"https://t.me/{target_channel.replace('@', '')}"
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Join Required Channel 📢", url=target_url)],
                            [InlineKeyboardButton(text="I Have Joined ✅", callback_data="check_subscription")]
                        ])
                        await event.reply(
                            "⚠️ <b>Access Restricted</b>\n\n"
                            "You must join our official channel to use this bot.\n"
                            "Please join the channel below and click 'I Have Joined'.",
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                    return None
            except TelegramBadRequest as e:
                logger.error("ForceSub check failed (make sure bot is admin in channel %s): %s", target_channel, e)
                return await handler(event, data)

        return await handler(event, data)
