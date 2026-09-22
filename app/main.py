import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from app.config import config
from app.database.session import DatabaseSession
from app.bot.middlewares.rate_limit import RateLimitMiddleware
from app.bot.handlers.common import router as common_router

# Feature module routers
from app.modules.admin.handlers import router as admin_router
from app.modules.broadcast.router import router as broadcast_router
from app.modules.referrals.router import router as referrals_router
from app.modules.ai.router import router as ai_router
from app.modules.miniapp.router import router as miniapp_router
from app.modules.payments.router import router as payments_router
from app.modules.force_sub.middleware import ForceSubMiddleware

logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    level=getattr(logging, config.log_level.upper(), logging.INFO)
)
logger = logging.getLogger("TeleCore")

def create_dispatcher(db: DatabaseSession) -> Dispatcher:
    """Builds and wires up the aiogram 3 Dispatcher with active modules."""
    dp = Dispatcher()

    # Inject shared database session
    dp["db"] = db

    # Global Rate Limiting
    dp.message.middleware(RateLimitMiddleware(limit_seconds=config.bot.rate_limit))

    # Optional Force Subscription Middleware
    if config.modules.force_sub:
        logger.info("Module ENABLED: Force Subscription")
        dp.message.middleware(ForceSubMiddleware())

    # Common router (always active)
    dp.include_router(common_router)

    # Pluggable Feature Modules
    if config.modules.admin:
        logger.info("Module ENABLED: Admin Suite")
        dp.include_router(admin_router)

    if config.modules.broadcast:
        logger.info("Module ENABLED: Broadcast Engine")
        dp.include_router(broadcast_router)

    if config.modules.referrals:
        logger.info("Module ENABLED: Referral Program")
        dp.include_router(referrals_router)

    if config.modules.ai:
        logger.info("Module ENABLED: AI Assistant")
        dp.include_router(ai_router)

    if config.modules.miniapp:
        logger.info("Module ENABLED: Telegram Mini App")
        dp.include_router(miniapp_router)

    if config.modules.payments:
        logger.info("Module ENABLED: Telegram Stars & Payments")
        dp.include_router(payments_router)

    return dp

async def run_polling(bot: Bot, dp: Dispatcher, db: DatabaseSession):
    """Starts polling loop."""
    await db.init_models()
    logger.info("Starting TeleCore bot in POLLING mode...")
    await bot.delete_webhook(drop_pending_updates=config.bot.drop_pending_updates)
    await dp.start_polling(bot)

async def run_webhook(bot: Bot, dp: Dispatcher, db: DatabaseSession):
    """Starts aiohttp server for Webhook mode."""
    await db.init_models()
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    app = web.Application()
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=config.webhook.path)
    setup_application(app, dp, bot=bot)

    await bot.set_webhook(url=config.webhook.url, drop_pending_updates=config.bot.drop_pending_updates)
    logger.info("Starting TeleCore bot in WEBHOOK mode on %s:%s%s", config.webhook.host, config.webhook.port, config.webhook.path)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.webhook.host, config.webhook.port)
    await site.start()
    await asyncio.Event().wait()

async def main():
    if not config.bot.token:
        logger.error("BOT_TOKEN is not set! Please check your .env file.")
        sys.exit(1)

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    db = DatabaseSession(config.db.sqlite_path)
    dp = create_dispatcher(db)

    try:
        if config.webhook.enabled:
            await run_webhook(bot, dp, db)
        else:
            await run_polling(bot, dp, db)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("TeleCore bot stopped gracefully.")
