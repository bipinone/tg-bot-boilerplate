import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.database.session import DatabaseSession
from app.bot.filters.admin import IsAdminFilter

logger = logging.getLogger(__name__)

router = Router(name="subscriptions_module")

@router.message(Command("sub", "plan"))
async def user_subscription_status(message: Message, db: DatabaseSession):
    """Checks user current subscription plan and entitlement status."""
    sub = await db.get_user_subscription(message.from_user.id)
    if not sub:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Upgrade to Pro", callback_data="plans:view")]
        ])
        await message.reply(
            "💳 <b>Subscription Status</b>\n\n"
            "• <b>Current Plan:</b> <i>Free Tier</i>\n"
            "• <b>Status:</b> Active\n\n"
            "Upgrade to Pro or VIP to unlock unlimited AI queries, zero rate-limits, and priority support!",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    end_date = sub.get("end_date", "Never")[:10]
    await message.reply(
        "⭐ <b>Active Membership</b>\n\n"
        f"• <b>Current Plan:</b> <b>{sub.get('plan', 'Pro').upper()} 👑</b>\n"
        f"• <b>Valid Until:</b> <code>{end_date}</code>\n"
        f"• <b>Features:</b> Unlimited AI, Zero Cooldowns, Priority Support",
        parse_mode="HTML"
    )

@router.message(Command("plans"))
async def view_plans_cmd(message: Message):
    """Displays available subscription plans."""
    text = (
        "💎 <b>TeleCore Subscription Tiers</b>\n\n"
        "🥉 <b>Free Tier:</b>\n"
        "• Basic bot access\n"
        "• Standard rate limits (1 req/s)\n\n"
        "🥈 <b>Pro Tier:</b>\n"
        "• Unlimited AI Assistant queries\n"
        "• Bypass flood rate limits\n"
        "• Premium customer support\n\n"
        "🥇 <b>VIP Tier:</b>\n"
        "• Everything in Pro\n"
        "• Custom workflows & early features\n\n"
        "<i>Use /pay to purchase via Telegram Stars!</i>"
    )
    await message.reply(text, parse_mode="HTML")

@router.message(Command("grant_sub"))
async def admin_grant_sub(message: Message, db: DatabaseSession):
    """Admin command to grant or extend subscription to a user."""
    # Enforce admin filter
    if not await IsAdminFilter()(message, db=db):
        return

    parts = message.text.split()
    if len(parts) < 3 or not parts[1].isdigit():
        await message.reply("⚠️ Usage: <code>/grant_sub &lt;user_id&gt; &lt;pro|vip&gt; [days=30]</code>", parse_mode="HTML")
        return

    target_id = int(parts[1])
    plan = parts[2].lower()
    days = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 30

    sub = await db.create_subscription(target_id, plan=plan, duration_days=days)
    await message.reply(
        f"✅ <b>Subscription Granted!</b>\n\n"
        f"• User ID: <code>{target_id}</code>\n"
        f"• Plan: <b>{plan.upper()}</b>\n"
        f"• Duration: <code>{days} days</code>\n"
        f"• Valid Until: <code>{sub['end_date'][:10]}</code>",
        parse_mode="HTML"
    )
