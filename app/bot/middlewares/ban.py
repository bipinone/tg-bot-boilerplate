import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.config import config

logger = logging.getLogger(__name__)

class BanCheckMiddleware(BaseMiddleware):
    """
    Global middleware enforcing:
    1. Ban restrictions with dynamic ban reason.
    2. Maintenance mode restrictions (bypassed by staff/admins).
    """

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
        if not db:
            return await handler(event, data)

        is_superadmin = user.id in config.bot.admins
        role = await db.get_user_role(user.id)
        is_staff = is_superadmin or role in ("owner", "admin", "moderator")

        # 1. Enforce Ban Check (Superadmins cannot be banned)
        if not is_superadmin:
            user_data = await db.get_user(user.id)
            if user_data and user_data.get("is_banned"):
                reason = user_data.get("ban_reason") or "Violation of community rules"
                if isinstance(event, Message):
                    await event.reply(
                        f"⛔ <b>Access Denied</b>\n\n"
                        f"Your account has been suspended.\n"
                        f"<b>Reason:</b> {reason}\n\n"
                        f"<i>If you believe this is an error, please contact an administrator.</i>",
                        parse_mode="HTML"
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(f"⛔ Suspended: {reason}", show_alert=True)
                return None

        # 2. Enforce Maintenance Mode (Staff bypasses)
        if not is_staff:
            maint_setting = await db.get_setting("maintenance_mode", "false")
            if maint_setting and maint_setting.lower() in ("true", "1", "yes", "on"):
                if isinstance(event, Message):
                    await event.reply(
                        "🛠️ <b>Maintenance Mode Active</b>\n\n"
                        "The bot is undergoing scheduled maintenance and updates.\n"
                        "Please check back in a few minutes! ⏳",
                        parse_mode="HTML"
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer("🛠️ Bot is currently under maintenance.", show_alert=True)
                return None

        return await handler(event, data)
