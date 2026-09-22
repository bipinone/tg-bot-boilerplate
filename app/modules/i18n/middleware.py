from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from app.modules.i18n.service import i18n

class I18nMiddleware(BaseMiddleware):
    """
    Middleware resolving user language preference and injecting translation helper `_` into handlers.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, "from_user", None)
        lang = "en"

        if user and not user.is_bot:
            db = data.get("db")
            if db:
                user_record = await db.get_user(user.id)
                if user_record and user_record.get("language_code"):
                    lang = user_record["language_code"]
                elif user.language_code:
                    lang = user.language_code[:2].lower()
            elif user.language_code:
                lang = user.language_code[:2].lower()

        # Fallback to English if language not supported
        if lang not in i18n.SUPPORTED_LANGUAGES:
            lang = "en"

        data["user_lang"] = lang
        data["i18n"] = i18n
        data["_"] = lambda key, **kwargs: i18n.t(key, lang=lang, **kwargs)

        return await handler(event, data)
