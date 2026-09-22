# TeleCore Telegram Bot Framework
# Author: bipinone (https://github.com/bipinone)
# Repository: https://github.com/bipinone/tg-bot-boilerplate

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ErrorEvent
from aiohttp import web

from app.config import config
from app.database.session import DatabaseSession
from app.services.logger import TelegramLogService
from app.services.health import HealthServer
from app.bot.middlewares.rate_limit import RateLimitMiddleware
from app.bot.middlewares.ban import BanCheckMiddleware
from app.modules.i18n.middleware import I18nMiddleware
from app.bot.handlers.common import router as common_router

# Feature module routers
from app.modules.admin.handlers import router as admin_router
from app.modules.broadcast.router import router as broadcast_router
from app.modules.referrals.router import router as referrals_router
from app.modules.ai.router import router as ai_router
from app.modules.miniapp.router import router as miniapp_router
from app.modules.payments.router import router as payments_router
from app.modules.support.router import router as support_router
from app.modules.force_sub.middleware import ForceSubMiddleware
from app.modules.i18n.router import router as i18n_router
from app.modules.groups.router import router as groups_router
from app.modules.subscriptions.router import router as subscriptions_router
from app.modules.scheduler.service import TaskScheduler
from app.bot.setup_commands import setup_bot_metadata

logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    level=getattr(logging, config.log_level.upper(), logging.INFO)
)

logger = logging.getLogger("TeleCore")

def get_active_module_names() -> list:
    """Returns list of currently active feature flags."""
    active = ["I18n", "Groups", "Subscriptions"]
    if config.modules.admin: active.append("Admin")
    if config.modules.broadcast: active.append("Broadcast")
    if config.modules.force_sub: active.append("ForceSub")
    if config.modules.referrals: active.append("Referrals")
    if config.modules.ai: active.append("AI")
    if config.modules.miniapp: active.append("MiniApp")
    if config.modules.payments: active.append("Payments")
    if config.support.enabled: active.append("LiveSupport")
    if config.health.enabled: active.append("HealthServer")
    return active

def create_dispatcher(db: DatabaseSession, tg_logger: TelegramLogService) -> Dispatcher:
    """Builds and wires up the aiogram 3 Dispatcher with active modules and logging."""
    dp = Dispatcher()

    # Inject shared database session and Telegram logger into context
    dp["db"] = db
    dp["tg_logger"] = tg_logger

    # Global Rate Limiting
    dp.message.middleware(RateLimitMiddleware(limit_seconds=config.bot.rate_limit))

    # Global Ban & Maintenance Enforcement
    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())

    # Multi-Language I18n Middleware
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())

    # Dynamic Force Subscription Middleware (Always wired, checks dynamic DB status)
    dp.message.middleware(ForceSubMiddleware())

    # Common router (always active)
    dp.include_router(common_router)
    dp.include_router(i18n_router)
    dp.include_router(groups_router)
    dp.include_router(subscriptions_router)

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

    if config.support.enabled:
        logger.info("Module ENABLED: Two-Way Topic Live Support Chat")
        dp.include_router(support_router)

    # Global Error Handler
    @dp.error()
    async def global_error_handler(event: ErrorEvent):
        logger.exception("Unhandled exception occurred: %s", event.exception)
        user_id = event.update.effective_user.id if event.update and event.update.effective_user else None
        cmd = event.update.message.text if event.update and event.update.message else None
        await tg_logger.log_error(str(event.exception), user_id=user_id, command=cmd)

    return dp


async def run_polling(bot: Bot, dp: Dispatcher, db: DatabaseSession, tg_logger: TelegramLogService):
    """Starts polling loop."""
    await db.init_models()
    bot_info = await bot.get_me()
    logger.info("Starting TeleCore bot @%s in POLLING mode...", bot_info.username)

    # Register default BotCommand menu, descriptions, and bipinone credits
    await setup_bot_metadata(bot)

    # Send startup alert to log channel/topic
    await tg_logger.log_startup(bot_info.username, get_active_module_names())

    await bot.delete_webhook(drop_pending_updates=config.bot.drop_pending_updates)
    await dp.start_polling(bot)

async def run_webhook(bot: Bot, dp: Dispatcher, db: DatabaseSession, tg_logger: TelegramLogService):
    """Starts aiohttp server for Webhook mode."""
    await db.init_models()
    bot_info = await bot.get_me()
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    app = web.Application()
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=config.webhook.path)
    setup_application(app, dp, bot=bot)

    # Register default BotCommand menu, descriptions, and bipinone credits
    await setup_bot_metadata(bot)

    await bot.set_webhook(url=config.webhook.url, drop_pending_updates=config.bot.drop_pending_updates)
    logger.info("Starting TeleCore bot @%s in WEBHOOK mode on %s:%s%s", bot_info.username, config.webhook.host, config.webhook.port, config.webhook.path)

    # Send startup alert to log channel/topic
    await tg_logger.log_startup(bot_info.username, get_active_module_names())

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

    db = DatabaseSession.from_config(config.db)
    tg_logger = TelegramLogService(bot)
    dp = create_dispatcher(db, tg_logger)

    # Start Cloud Health Server (concurrent liveness probe)
    health_server = HealthServer(db)
    await health_server.start()

    # Start Background Task Scheduler (cron & recurring maintenance)
    scheduler = TaskScheduler(bot, db)
    await scheduler.start()

    try:
        if config.webhook.enabled:
            await run_webhook(bot, dp, db, tg_logger)
        else:
            await run_polling(bot, dp, db, tg_logger)
    finally:
        await scheduler.stop()
        await health_server.stop()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    # Activate ultra-fast C-based event loop on Linux/macOS
    try:
        import uvloop
        uvloop.install()
        logger.info("⚡ Ultra-fast uvloop event loop activated")
    except (ImportError, AttributeError):
        pass

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("TeleCore bot stopped gracefully.")

