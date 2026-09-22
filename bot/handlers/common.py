import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.utils.keyboards import get_start_keyboard, get_back_keyboard
from bot.database.db import Database
from bot.config import config

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command, registers user in db, and displays menu."""
    user = update.effective_user
    db: Database = context.bot_data["db"]

    # Register or update user
    is_new = await db.register_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    if is_new:
        logger.info("New user registered: %s (@%s)", user.id, user.username)

    # Check ban status
    user_data = await db.get_user(user.id)
    if user_data and user_data.get("is_banned"):
        await update.message.reply_text("⛔ You are banned from using this bot.")
        return

    text = (
        f"👋 *Welcome, {user.first_name}!*\n\n"
        f"This is **TeleCore** — a production-ready, high-performance Telegram Bot Boilerplate.\n\n"
        f"⚡ *Features Built-in:*\n"
        f"• Async SQLite Database\n"
        f"• Admin Panel & User Analytics\n"
        f"• Mass Broadcast Tool\n"
        f"• Anti-Flood Rate Limiting\n"
        f"• Modular Clean Architecture\n\n"
        f"Select an option below to explore:"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=get_start_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /help command."""
    text = (
        "📖 *Available Commands:*\n\n"
        "/start — Launch or reset bot menu\n"
        "/help — View command reference\n"
        "/ping — Check bot latency & status\n\n"
        "*Admin Commands:*\n"
        "/stats — View real-time database stats\n"
        "/broadcast <message> — Send mass announcement\n"
        "/ban <user_id> — Ban a user\n"
        "/unban <user_id> — Unban a user"
    )
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

async def ping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks latency."""
    import time
    start = time.time()
    msg = await update.message.reply_text("🏓 Pong...")
    latency = round((time.time() - start) * 1000, 2)
    await msg.edit_text(f"🏓 *Pong!*\nLatency: `{latency} ms`", parse_mode=ParseMode.MARKDOWN)

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline menu callbacks."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_main":
        user = update.effective_user
        text = (
            f"👋 *Welcome, {user.first_name}!*\n\n"
            f"Select an option below to explore:"
        )
        await query.message.edit_text(
            text=text,
            reply_markup=get_start_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "menu_help":
        await help_handler(update, context)
    elif data == "menu_features":
        text = (
            "🛠️ *TeleCore Production Features:*\n\n"
            "1. **Async SQLite Engine**: Non-blocking queries with automatic table creation.\n"
            "2. **Admin Command Suite**: Live stats, user banning, and safe mass broadcasting.\n"
            "3. **Rate Limiting**: Sliding window middleware preventing Telegram API 429 flood errors.\n"
            "4. **Docker & 1-Click Deploy**: Includes Dockerfile and Docker Compose.\n"
            "5. **Zero Bloat**: Clean code structure designed for rapid extension."
        )
        await query.message.edit_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
