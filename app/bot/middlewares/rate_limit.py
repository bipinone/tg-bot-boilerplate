import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from app.config import config

class RateLimitMiddleware(BaseMiddleware):
    """aiogram 3 sliding window anti-flood middleware."""
    def __init__(self, limit_seconds: float = None):
        self.limit = limit_seconds if limit_seconds is not None else config.bot.rate_limit
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user and not user.is_bot:
            now = time.time()
            last_action = self.user_timestamps.get(user.id, 0.0)

            if now - last_action < self.limit:
                if isinstance(event, Message):
                    await event.reply("⚠️ Slow down! You are sending commands too quickly.")
                return None

            self.user_timestamps[user.id] = now

        return await handler(event, data)
