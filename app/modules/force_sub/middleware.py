import os
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

class ForceSubMiddleware(BaseMiddleware):
    """Enforces channel membership before user can interact with the bot."""
    def __init__(self, channel_id: str = None):
        self.channel_id = channel_id or os.getenv("FORCE_SUB_CHANNEL", "")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not self.channel_id:
            return await handler(event, data)

        user = getattr(event, "from_user", None)
        bot: Bot = data.get("bot")

        if user and bot and not user.is_bot:
            try:
                member = await bot.get_chat_member(chat_id=self.channel_id, user_id=user.id)
                # Valid statuses: creator, administrator, member
                if member.status not in ("creator", "administrator", "member"):
                    if isinstance(event, Message):
                        channel_url = os.getenv("FORCE_SUB_URL", f"https://t.me/{self.channel_id.replace('@', '')}")
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Join Required Channel 📢", url=channel_url)],
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
                logger.error("ForceSub check failed (make sure bot is admin in channel): %s", e)
                return await handler(event, data)

        return await handler(event, data)
