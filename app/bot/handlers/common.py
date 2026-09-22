# TeleCore Telegram Bot Framework
# Author: bipinone (https://github.com/bipinone)
# Repository: https://github.com/bipinone/tg-bot-boilerplate

import time
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.database.session import DatabaseSession

router = Router(name="common_router")

def get_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ Features", callback_data="btn_features"),
            InlineKeyboardButton(text="📖 Help", callback_data="btn_help"),
            InlineKeyboardButton(text="ℹ️ About", callback_data="btn_about")
        ],
        [
            InlineKeyboardButton(text="📢 Official Channel", url="https://t.me/BipinOne"),
            InlineKeyboardButton(text="💬 Community Chat", url="https://t.me/BipinOneChat")
        ],
        [
            InlineKeyboardButton(text="⭐ GitHub Repository", url="https://github.com/bipinone/tg-bot-boilerplate")
        ]
    ])

@router.message(CommandStart())
async def start_handler(message: Message, db: DatabaseSession, tg_logger = None):
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

    # Send log to group/topic (auto-creates a dedicated user topic if missing)
    if tg_logger:
        if is_new:
            await tg_logger.log_new_user(user.id, user.username, user.first_name, referrer_id, db=db)
        else:
            await tg_logger.ensure_user_topic(user.id, user.first_name, user.username, db=db)

    text = (
        f"👋 <b>Welcome, {user.first_name}!</b>\n\n"
        "This is <b>TeleCore</b> — a production-ready, modular Telegram Bot Framework built with Python & <code>aiogram 3.x</code>.\n\n"
        "🧱 <b>Active Architectural Highlights:</b>\n"
        "• <b>Multi-Database DAL:</b> SQLite, PostgreSQL, MySQL, MongoDB\n"
        "• <b>Internationalization:</b> Multi-language engine (English, Hindi)\n"
        "• <b>SaaS Subscriptions:</b> Free, Pro & VIP entitlement gates\n"
        "• <b>Mass Broadcast:</b> High-speed flag engine with live progress bar\n"
        "• <b>Multi-Provider AI:</b> OpenAI, Gemini, Claude, and local models\n\n"
        "👨‍💻 <i>Crafted with ❤️ by <a href=\"https://github.com/bipinone\">@bipinone</a></i>\n\n"
        "Select an option below to explore:"
    )

    await message.reply(text, reply_markup=get_main_keyboard(), parse_mode="HTML")

@router.message(Command("help"))
async def help_command_handler(message: Message):
    """Displays user command reference."""
    text = (
        "📖 <b>TeleCore Command Reference:</b>\n\n"
        "• <code>/start</code> — Open or reset the main bot dashboard\n"
        "• <code>/help</code> — View this command manual\n"
        "• <code>/language</code> — Switch preferred language (English / हिन्दी)\n"
        "• <code>/sub</code> — View active subscription tier and expiry\n"
        "• <code>/plans</code> — Browse Pro and VIP membership benefits\n"
        "• <code>/ref</code> — Get your invitation link and points\n"
        "• <code>/ask &lt;query&gt;</code> — Consult the integrated AI assistant\n"
        "• <code>/ping</code> — Test server response speed\n"
        "• <code>/about</code> — Developer info and credits\n\n"
        "👨‍💻 <i>Created by <a href=\"https://t.me/BipinOne\">@BipinOne</a></i>"
    )
    await message.reply(text, parse_mode="HTML")

@router.message(Command("about"))
async def about_command_handler(message: Message):
    """Displays developer credits and project links."""
    text = (
        "🤖 <b>About TeleCore</b>\n\n"
        "A production-ready, modular Telegram Bot Framework built on Python and aiogram 3.x.\n\n"
        "👨‍💻 <b>Developer & Lead Architect:</b>\n"
        "• <b>Author:</b> Bipin (<a href=\"https://github.com/bipinone\">@bipinone</a>)\n"
        "• <b>Telegram Channel:</b> <a href=\"https://t.me/BipinOne\">@BipinOne</a>\n"
        "• <b>Community Group:</b> <a href=\"https://t.me/BipinOneChat\">@BipinOneChat</a>\n"
        "• <b>Instagram:</b> <a href=\"https://www.instagram.com/bipinone\">@bipinone</a>\n"
        "• <b>Source Code:</b> <a href=\"https://github.com/bipinone/tg-bot-boilerplate\">github.com/bipinone/tg-bot-boilerplate</a>\n\n"
        "⭐ <i>Free and open-source under the MIT License.</i>"
    )
    await message.reply(text, parse_mode="HTML")

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
        "1. <b>Multi-Database Provider:</b> SQLite, Postgres, MySQL, MongoDB\n"
        "2. <b>i18n Localization:</b> Multi-language engine (`/language`)\n"
        "3. <b>SaaS Subscriptions:</b> Tier gates (`/sub`, `/plans`)\n"
        "4. <b>Admin Engine:</b> <code>/panel</code>, <code>/stats</code>, <code>/setrole</code>\n"
        "5. <b>Broadcast Engine:</b> Flag-based delivery (`-copy`, `-pin`, `-silent`, `-fast`)\n"
        "6. <b>Referral Engine:</b> Deep links (<code>/ref</code>) and points\n"
        "7. <b>Community Engine:</b> Group tracking and supergroup CRM\n"
        "8. <b>AI & Mini Apps:</b> Pluggable LLM and WebApp integration\n\n"
        "👨‍💻 <i>Crafted with ❤️ by <a href=\"https://github.com/bipinone\">@bipinone</a></i>"
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
        "• <code>/language</code> — Change language preference\n"
        "• <code>/sub</code> — Check subscription membership\n"
        "• <code>/plans</code> — View membership tiers\n"
        "• <code>/ref</code> — View your referral link & points\n"
        "• <code>/ask &lt;prompt&gt;</code> — Chat with AI assistant\n"
        "• <code>/ping</code> — Test server latency\n"
        "• <code>/about</code> — Developer info & credits\n\n"
        "<b>Staff / Admin Commands:</b>\n"
        "• <code>/panel</code> — Interactive real-time control dashboard\n"
        "• <code>/stats</code> — Real-time analytics\n"
        "• <code>/broadcast</code> — Fast mass messaging\n"
        "• <code>/admins</code> — Staff directory\n"
        "• <code>/ban &lt;user_id&gt;</code> — Suspend user\n"
        "• <code>/unban &lt;user_id&gt;</code> — Restore user\n\n"
        "👨‍💻 <i>Crafted by @bipinone</i>"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Back to Main Menu", callback_data="btn_main")]
    ])
    await call.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML")

@router.callback_query(F.data == "btn_about")
async def cb_about(call: CallbackQuery):
    await call.answer()
    text = (
        "🤖 <b>About TeleCore</b>\n\n"
        "Production-ready, modular Telegram Bot Framework built on Python and aiogram 3.x.\n\n"
        "👨‍💻 <b>Developer & Lead Architect:</b>\n"
        "• <b>Author:</b> Bipin (<a href=\"https://github.com/bipinone\">@bipinone</a>)\n"
        "• <b>Telegram Channel:</b> <a href=\"https://t.me/BipinOne\">@BipinOne</a>\n"
        "• <b>Community Chat:</b> <a href=\"https://t.me/BipinOneChat\">@BipinOneChat</a>\n"
        "• <b>Instagram:</b> <a href=\"https://www.instagram.com/bipinone\">@bipinone</a>\n"
        "• <b>GitHub:</b> <a href=\"https://github.com/bipinone/tg-bot-boilerplate\">github.com/bipinone/tg-bot-boilerplate</a>\n\n"
        "⭐ <i>Open-source under the MIT License.</i>"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Back to Main Menu", callback_data="btn_main")]
    ])
    await call.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML")
