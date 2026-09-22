import asyncio
import logging
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from app.bot.filters.admin import IsAdminFilter
from app.database.session import DatabaseSession

logger = logging.getLogger(__name__)

router = Router(name="broadcast_module")
router.message.filter(IsAdminFilter())

@router.message(Command("broadcast"))
async def broadcast_command(message: Message, bot: Bot, db: DatabaseSession):
    """Mass broadcast message to all registered users safely."""
    reply_msg = message.reply_to_message
    broadcast_text = " ".join(message.text.split()[1:]) if len(message.text.split()) > 1 else None

    if not reply_msg and not broadcast_text:
        await message.reply(
            "⚠️ <b>Usage:</b>\n"
            "<code>/broadcast &lt;your announcement&gt;</code>\n"
            "Or reply to any text/media message with <code>/broadcast</code>",
            parse_mode="HTML"
        )
        return

    users = await db.get_all_active_user_ids()
    if not users:
        await message.reply("ℹ️ No active users found to broadcast to.")
        return

    progress_msg = await message.reply(f"🚀 Starting broadcast to {len(users)} users...")

    sent = 0
    blocked = 0
    failed = 0

    for user_id in users:
        try:
            if reply_msg:
                await reply_msg.copy_to(chat_id=user_id)
            else:
                await bot.send_message(chat_id=user_id, text=broadcast_text, parse_mode="HTML")
            sent += 1
        except TelegramForbiddenError:
            blocked += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            sent += 1
        except Exception as e:
            logger.warning("Broadcast failed for user %s: %s", user_id, e)
            failed += 1

        # Throttle to stay safely below Telegram limit (30 msgs/sec)
        await asyncio.sleep(0.04)

    summary = (
        "✅ <b>Broadcast Completed!</b>\n\n"
        f"• <b>Delivered:</b> <code>{sent}</code>\n"
        f"• <b>Blocked/Deleted:</b> <code>{blocked}</code>\n"
        f"• <b>Failed:</b> <code>{failed}</code>"
    )
    await progress_msg.edit_text(summary, parse_mode="HTML")
