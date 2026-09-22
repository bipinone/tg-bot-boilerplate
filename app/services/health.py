import time
import datetime
import logging
from aiohttp import web
from app.config import config
from app.database.session import DatabaseSession

logger = logging.getLogger(__name__)

class HealthServer:
    """Lightweight HTTP server for cloud liveness probes and uptime monitors."""
    def __init__(self, db: DatabaseSession):
        self.db = db
        self.start_time = time.time()
        self.app = web.Application()
        self.setup_routes()
        self.runner = None

    def setup_routes(self):
        self.app.router.add_get("/", self.handle_root)
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_get("/metrics", self.handle_metrics)

    async def handle_root(self, request: web.Request) -> web.Response:
        return web.json_response({
            "service": "TeleCore Telegram Bot",
            "version": "2.0.0",
            "status": "online",
            "repository": "https://github.com/bipinone/tg-bot-boilerplate"
        })

    async def handle_health(self, request: web.Request) -> web.Response:
        uptime = round(time.time() - self.start_time, 1)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return web.json_response({
            "status": "healthy",
            "uptime_seconds": uptime,
            "timestamp": now,
            "polling": not config.webhook.enabled
        })

    async def handle_metrics(self, request: web.Request) -> web.Response:
        stats = await self.db.get_stats()
        return web.json_response({
            "uptime_seconds": round(time.time() - self.start_time, 1),
            "users": stats
        })

    async def start(self):
        """Starts the HTTP server concurrently."""
        if not config.health.enabled or config.webhook.enabled:
            return

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, config.health.host, config.health.port)
        try:
            await site.start()
            logger.info("Health server running on http://%s:%s/health", config.health.host, config.health.port)
        except OSError as e:
            logger.warning("Could not bind Health server to port %s: %s (Bot will continue running)", config.health.port, e)

    async def stop(self):
        """Gracefully stops the HTTP server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Health server stopped.")
