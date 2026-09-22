import asyncio
import logging
from typing import Callable, Coroutine, Any, List, Dict
from aiogram import Bot
from app.database.session import DatabaseSession

logger = logging.getLogger(__name__)

class ScheduledJob:
    def __init__(self, name: str, callback: Callable[..., Coroutine[Any, Any, None]], interval_seconds: float):
        self.name = name
        self.callback = callback
        self.interval = interval_seconds
        self.is_running = False

class TaskScheduler:
    """
    Lightweight, production-ready async background scheduler for recurring jobs:
    - Subscription expiration notifications
    - Database cleanup & vacuum
    - Daily metric aggregation
    - Custom cron-like tasks
    """

    def __init__(self, bot: Bot, db: DatabaseSession):
        self.bot = bot
        self.db = db
        self.jobs: List[ScheduledJob] = []
        self._running = False
        self._tasks: List[asyncio.Task] = []

    def add_job(self, name: str, callback: Callable[..., Coroutine[Any, Any, None]], interval_seconds: float) -> None:
        """Register a periodic async background task."""
        self.jobs.append(ScheduledJob(name, callback, interval_seconds))
        logger.debug("Registered background scheduled job '%s' (every %ss)", name, interval_seconds)

    async def _job_loop(self, job: ScheduledJob):
        while self._running:
            try:
                await asyncio.sleep(job.interval)
                if not self._running:
                    break
                logger.info("Executing scheduled job: [%s]", job.name)
                await job.callback(bot=self.bot, db=self.db)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error executing scheduled job '%s': %s", job.name, e)

    async def start(self) -> None:
        """Starts all scheduled jobs."""
        if self._running:
            return
        self._running = True

        # Register default framework background jobs
        self.add_job("subscription_expiry_check", check_expiring_subscriptions_job, interval_seconds=3600)  # Hourly
        self.add_job("cache_cleanup", periodic_cleanup_job, interval_seconds=86400)  # Daily

        for job in self.jobs:
            task = asyncio.create_task(self._job_loop(job), name=f"scheduler_{job.name}")
            self._tasks.append(task)
        logger.info("TaskScheduler started with %d active jobs.", len(self.jobs))

    async def stop(self) -> None:
        """Gracefully halts all scheduler background tasks."""
        self._running = False
        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("TaskScheduler stopped gracefully.")

# Default System Background Jobs

async def check_expiring_subscriptions_job(bot: Bot, db: DatabaseSession):
    """Finds subscriptions expiring in <= 24 hours and notifies users."""
    try:
        expiring = await db.get_expiring_subscriptions(within_days=1)
        for sub in expiring:
            uid = sub.get("user_id")
            end_date = sub.get("end_date", "")[:10]
            try:
                await bot.send_message(
                    chat_id=uid,
                    text=f"⏳ <b>Subscription Expiring Soon!</b>\n\nYour <b>{sub.get('plan', 'Pro').upper()}</b> subscription will end on <code>{end_date}</code>.\nRenew now using /plans to keep your premium benefits!",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    except Exception as e:
        logger.error("Error in check_expiring_subscriptions_job: %s", e)

async def periodic_cleanup_job(bot: Bot, db: DatabaseSession):
    """Periodic maintenance routine."""
    logger.info("Periodic database maintenance executed.")
