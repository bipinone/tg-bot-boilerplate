#!/usr/bin/env python3
import asyncio
import logging
import sys
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    TypeHandler
)
from telegram import Update

from bot.config import config
from bot.database.db import Database
from bot.middlewares.rate_limit import RateLimiter
from bot.handlers.common import (
    start_handler,
    help_handler,
    ping_handler,
    callback_query_handler
)
from bot.handlers.admin import (
    stats_handler,
    broadcast_handler,
    ban_handler,
    unban_handler
)
from bot.handlers.errors import global_error_handler

logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
)
logger = logging.getLogger("TeleCore")

async def rate_limit_middleware(update: Update, context):
    """Global middleware to reject flooded updates."""
    if update.effective_user:
        limiter: RateLimiter = context.bot_data["rate_limiter"]
        if limiter.is_rate_limited(update.effective_user.id):
            # Dropping update silently to avoid flood escalation
            return

def build_application() -> Application:
    """Constructs the Telegram Bot application with handlers and middlewares."""
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN is missing! Please set it in your .env file.")
        sys.exit(1)

    app = Application.builder().token(config.BOT_TOKEN).build()

    # Shared instances
    db = Database(config.DATABASE_PATH)
    limiter = RateLimiter(limit_seconds=config.RATE_LIMIT_SECONDS)

    app.bot_data["db"] = db
    app.bot_data["rate_limiter"] = limiter

    # Setup database on startup
    async def on_startup(application: Application):
        await db.init()
        bot_info = await application.bot.get_me()
        logger.info("Bot started successfully as @%s (ID: %s)", bot_info.username, bot_info.id)

    app.post_init = on_startup

    # Register Handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("ping", ping_handler))

    # Admin Handlers
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))
    app.add_handler(CommandHandler("ban", ban_handler))
    app.add_handler(CommandHandler("unban", unban_handler))

    # Interactive Menus
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    # Global Error Handler
    app.add_error_handler(global_error_handler)

    return app

def main():
    """Entry point to launch the bot."""
    logger.info("Starting TeleCore Telegram Bot Engine...")
    application = build_application()
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
