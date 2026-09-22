import time
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.database.session import DatabaseSession

router = Router(name="common_router")

def get_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Modules & Features ⚡", callback_data="btn_features"),
            InlineKeyboardButton(text="Help & Commands 📖", callback_data="btn_help")
        ],
        [
            InlineKeyboardButton(text="Official Channel 📢", url="https://t.me/BipinOne"),
            InlineKeyboardButton(text="Community Group 💬", url="https://t.me/BipinOneChat")
        ],
        [
            InlineKeyboardButton(text="GitHub Repository ⭐", url="https://github.com/bipinone/tg-bot-boilerplate")
        ]
    ])

@router.message(CommandStart())
async def start_handler(message: Message, db: DatabaseSession):
    """Handles /start command with deep linking support."""
    user = message.from_user
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    referrer_id = None

    # Parse deep-link referral (e.g. /start ref_123456)
    if args and args[0].startswith("ref_"):
        raw_ref = args[0].replace("ref_", "")
        if raw_ref.isdigit() and int(raw_ref) != user.id:
            referrer_id = int(raw_ref)

    # Upsert user into database
    is_new = await db.upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        referrer_id=referrer_id
    )

    await db.log_event(user.id, "start")

    text = (
        f"👋 <b>Welcome, {user.first_name}!</b>\n\n"
        f"This is <b>TeleCore</b> — an enterprise-grade, modular Telegram Bot Starter Kit built on Python & <code>aiogram 3.x</code>.\n\n"
        f"🧱 <b>Active Architecture:</b>\n"
        f"• Modular Plug-and-Play Architecture\n"
        f"• Async Database Layer (SQLite / Postgres)\n"
        f"• Anti-Flood Sliding Window Limiter\n"
        f"• Deep-Linking & Referral Engine\n"
        f"• Production Docker Compose Stack\n\n"
        f"Select an option below to explore:"
    )

    await message.reply(text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@router.message(Command("ping"))
async def ping_handler(message: Message):
    """Measures bot response latency."""
    start = time.time()
    msg = await message.reply("🏓 <i>Pong...</i>", parse_mode="HTML")
    latency = round((time.time() - start) * 1000, 2)
    await msg.edit_text(f"🏓 <b>Pong!</b> Latency: <code>{latency} ms</code>", parse_mode="HTML")

@router.callback_query(F.data == "btn_main")
async def cb_main_menu(call: CallbackQuery):
    await call.answer()
    user = call.from_user
    await call.message.edit_text(
        f"👋 <b>Welcome back, {user.first_name}!</b>\n\nSelect an option below to explore:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "btn_features")
async def cb_features(call: CallbackQuery):
    await call.answer()
    text = (
        "⚡ <b>TeleCore Modular Engines:</b>\n\n"
        "1. <b>Admin Engine:</b> <code>/stats</code>, <code>/ban</code>, <code>/unban</code>\n"
        "2. <b>Broadcast Engine:</b> Safe mass announcements with progress tracking\n"
        "3. <b>Referral Engine:</b> Deep links (<code>/ref</code>) and invitation rewards\n"
        "4. <b>Force Subscription:</b> Enforces channel joining before bot usage\n"
        "5. <b>Mini Apps:</b> One-click WebApp integration\n"
        "6. <b>AI & Payments:</b> Pluggable endpoints for LLMs & Telegram Stars\n\n"
        "<i>All modules can be toggled on/off in <code>.env</code> file!</i>"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Back to Main Menu", callback_data="btn_main")]
    ])
    await call.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML")

@router.callback_query(F.data == "btn_help")
async def cb_help(call: CallbackQuery):
    await call.answer()
    text = (
        "📖 <b>Command Reference:</b>\n\n"
        "• <code>/start</code> — Launch or reset bot menu\n"
        "• <code>/ping</code> — Test server latency\n"
        "• <code>/ref</code> — View your referral link & points\n"
        "• <code>/app</code> — Launch integrated Mini App\n"
        "• <code>/ask &lt;prompt&gt;</code> — Chat with AI assistant\n\n"
        "<b>Admin Commands:</b>\n"
        "• <code>/stats</code> — Real-time analytics\n"
        "• <code>/broadcast &lt;msg&gt;</code> — Send mass broadcast\n"
        "• <code>/ban &lt;user_id&gt;</code> — Ban user\n"
        "• <code>/unban &lt;user_id&gt;</code> — Unban user"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Back to Main Menu", callback_data="btn_main")]
    ])
    await call.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML")
