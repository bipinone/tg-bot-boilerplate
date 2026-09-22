from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.database.session import DatabaseSession

router = Router(name="referrals_module")

@router.message(Command("ref", "referral", "invite"))
async def referral_command(message: Message, bot: Bot, db: DatabaseSession):
    """Generates unique referral link and displays user referral stats."""
    bot_info = await bot.get_me()
    user_id = message.from_user.id
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    count = await db.get_referral_count(user_id)
    user_data = await db.get_user(user_id)
    points = user_data.get("points", 0) if user_data else 0

    text = (
        "👥 <b>Referral & Invite Program</b>\n\n"
        f"Share your referral link with friends and earn points for every joined user!\n\n"
        f"🔗 <b>Your Link:</b>\n<code>{ref_link}</code>\n\n"
        f"• <b>Total Friends Invited:</b> <code>{count}</code>\n"
        f"• <b>Reward Points:</b> <code>{points}</code>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Share Link 🚀", url=f"https://t.me/share/url?url={ref_link}&text=Join%20this%20amazing%20bot!")]
    ])

    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
