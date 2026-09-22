from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject
from typing import List, Union
from app.config import config

class IsAdminFilter(BaseFilter):
    """Checks if user is an Admin (either in .env ADMIN_IDS or has 'owner'/'admin' role in db)."""
    async def __call__(self, event: TelegramObject, **kwargs) -> bool:
        user = getattr(event, "from_user", None)
        if not user:
            return False

        # 1. Hardcoded superadmin check from .env
        if user.id in config.bot.admins:
            return True

        # 2. Database RBAC check
        db = kwargs.get("db")
        if db:
            role = await db.get_user_role(user.id)
            if role in ("owner", "admin"):
                return True

        return False

class IsOwnerFilter(BaseFilter):
    """Checks if user is SuperAdmin/Owner (in .env ADMIN_IDS or role == 'owner')."""
    async def __call__(self, event: TelegramObject, **kwargs) -> bool:
        user = getattr(event, "from_user", None)
        if not user:
            return False

        if user.id in config.bot.admins:
            return True

        db = kwargs.get("db")
        if db:
            role = await db.get_user_role(user.id)
            if role == "owner":
                return True

        return False

