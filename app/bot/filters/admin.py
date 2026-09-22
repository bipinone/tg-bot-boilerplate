from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject
from typing import Union
from app.config import config

class IsAdminFilter(BaseFilter):
    """Filter to ensure the user executing command is an admin."""
    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if not user:
            return False
        return user.id in config.bot.admins
