import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError, Forbidden

from bot.config import config
from bot.database.db import Database

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Checks if a given user_id is in ADMIN_IDS list."""
    return user_id in config.ADMIN_IDS

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to show bot user and usage statistics."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ You are not authorized to view admin statistics.")
        return

    db: Database = context.bot_data["db"]
    stats = await db.get_statistics()

    text = (
        "📊 *Bot Analytics & Statistics*\n\n"
        f"• **Total Registered Users:** `{stats['total_users']}`\n"
        f"• **Active Users:** `{stats['active_users']}`\n"
        f"• **Banned Users:** `{stats['banned_users']}`\n"
        f"• **Total Handled Messages:** `{stats['total_messages']}`\n"
    )

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to broadcast a message to all users."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ You are not authorized to use broadcast.")
        return

    # Check broadcast message content
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "⚠️ *Usage:*\n"
            "`/broadcast <message>`\n"
            "Or reply to any message with `/broadcast`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    broadcast_text = " ".join(context.args) if context.args else None
    reply_msg = update.message.reply_to_message

    db: Database = context.bot_data["db"]
    user_ids = await db.get_all_user_ids()

    if not user_ids:
        await update.message.reply_text("ℹ️ No active users found to broadcast to.")
        return

    status_msg = await update.message.reply_text(f"🚀 Starting broadcast to {len(user_ids)} users...")

    success_count = 0
    blocked_count = 0
    failed_count = 0

    for idx, target_id in enumerate(user_ids):
        try:
            if reply_msg:
                await reply_msg.copy(chat_id=target_id)
            else:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=broadcast_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            success_count += 1
        except Forbidden:
            # User blocked the bot
            blocked_count += 1
        except Exception as e:
            logger.warning("Broadcast failed for user %s: %s", target_id, e)
            failed_count += 1

        # Prevent Telegram flood limits (max 30 msgs/sec)
        await asyncio.sleep(0.04)

    summary = (
        "✅ *Broadcast Finished!*\n\n"
        f"• **Total Sent:** `{success_count}`\n"
        f"• **Blocked / Inaccessible:** `{blocked_count}`\n"
        f"• **Failed:** `{failed_count}`"
    )
    await status_msg.edit_text(summary, parse_mode=ParseMode.MARKDOWN)

async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to ban a user from using the bot."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ Usage: `/ban <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return

    target_id = int(context.args[0])
    db: Database = context.bot_data["db"]
    ok = await db.set_ban_status(target_id, is_banned=True)

    if ok:
        await update.message.reply_text(f"⛔ User `{target_id}` has been banned.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"⚠️ User `{target_id}` not found in database.", parse_mode=ParseMode.MARKDOWN)

async def unban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to unban a user."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("⚠️ Usage: `/unban <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return

    target_id = int(context.args[0])
    db: Database = context.bot_data["db"]
    ok = await db.set_ban_status(target_id, is_banned=False)

    if ok:
        await update.message.reply_text(f"✅ User `{target_id}` has been unbanned.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"⚠️ User `{target_id}` not found in database.", parse_mode=ParseMode.MARKDOWN)
