import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

router = Router(name="miniapp_module")

@router.message(Command("app", "webapp", "miniapp"))
async def open_miniapp(message: Message):
    """Sends button to launch Telegram Web App."""
    app_url = os.getenv("MINIAPP_URL", "https://t.me/bipinone")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Launch Mini App 🚀", web_app=WebAppInfo(url=app_url))]
    ])

    await message.reply(
        "📱 <b>Telegram Mini App</b>\n\n"
        "Click the button below to launch the integrated Web App interface:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
