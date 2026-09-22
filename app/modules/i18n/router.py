from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.modules.i18n.service import i18n
from app.database.session import DatabaseSession

router = Router(name="i18n_module")

def get_language_selection_markup() -> InlineKeyboardMarkup:
    buttons = []
    for code, label in i18n.SUPPORTED_LANGUAGES.items():
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"set_lang:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("language", "lang"))
async def language_command(message: Message, _ = None, user_lang: str = "en"):
    """Prompt user to change language preference."""
    prompt_text = _("lang_choose") if _ else i18n.t("lang_choose", lang=user_lang)
    await message.reply(
        prompt_text,
        reply_markup=get_language_selection_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("set_lang:"))
async def language_callback(callback: CallbackQuery, db: DatabaseSession):
    """Save selected language preference to database."""
    target_lang = callback.data.split(":")[1]
    if target_lang not in i18n.SUPPORTED_LANGUAGES:
        await callback.answer("Unsupported language", show_alert=True)
        return

    user = callback.from_user
    await db.set_user_language(user.id, target_lang)

    confirm_text = i18n.t("lang_updated", lang=target_lang)
    try:
        await callback.message.edit_text(confirm_text, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer(f"Language set to {i18n.SUPPORTED_LANGUAGES[target_lang]} ✅")
