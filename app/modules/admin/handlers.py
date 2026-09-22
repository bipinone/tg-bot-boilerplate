import csv
import io
import os
import datetime
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    BufferedInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from app.config import config
from app.bot.filters.admin import IsAdminFilter, IsOwnerFilter
from app.database.session import DatabaseSession

router = Router(name="admin_module")
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())

VALID_ROLES = ("owner", "admin", "moderator", "user")

async def build_panel_markup(db: DatabaseSession) -> tuple[str, InlineKeyboardMarkup]:
    """Generates the real-time dynamic admin control dashboard and keyboard."""
    # 1. Force sub dynamic state
    fs_setting = await db.get_setting("force_sub_enabled")
    if fs_setting is not None:
        fs_enabled = fs_setting.lower() in ("true", "1", "yes", "on")
    else:
        fs_enabled = config.modules.force_sub

    fs_channel = await db.get_setting("force_sub_channel", os.getenv("FORCE_SUB_CHANNEL", "Not Set"))

    # 2. Maintenance dynamic state
    maint_setting = await db.get_setting("maintenance_mode", "false")
    maint_enabled = maint_setting.lower() in ("true", "1", "yes", "on")

    # 3. Overall stats
    stats = await db.get_stats()

    fs_btn_text = "📢 Force-Sub: ON 🟢" if fs_enabled else "📢 Force-Sub: OFF 🔴"
    maint_btn_text = "🛠️ Maint: ACTIVE ⚠️" if maint_enabled else "🛠️ Maint: OFF 🟢"

    text = (
        "🎛️ <b>TeleCore Dynamic Management Panel</b>\n\n"
        "⚡ <b>Live System & Feature Status:</b>\n"
        f"• <b>Force Subscription:</b> {'🟢 <b>ACTIVE</b>' if fs_enabled else '🔴 <i>DISABLED</i>'}\n"
        f"  └ Target Channel: <code>{fs_channel}</code>\n"
        f"• <b>Maintenance Mode:</b> {'⚠️ <b>ACTIVE (Admins Only)</b>' if maint_enabled else '🟢 <i>OFF (Public Access)</i>'}\n"
        f"• <b>Support Topic Relay:</b> {'🟢 Active' if config.support.enabled else '⚪ Disabled'}\n"
        f"• <b>AI Assistant:</b> {'🟢 Active' if config.modules.ai else '⚪ Disabled'}\n\n"
        "👥 <b>User Base Overview:</b>\n"
        f"• Active Users: <code>{stats['active_users']}</code> | Banned: <code>{stats['banned_users']}</code> | Total: <code>{stats['total_users']}</code>\n\n"
        "<i>Tap buttons below to toggle runtime settings without restarting the bot:</i>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=fs_btn_text, callback_data="admin_toggle:forcesub"),
            InlineKeyboardButton(text=maint_btn_text, callback_data="admin_toggle:maintenance"),
        ],
        [
            InlineKeyboardButton(text="👑 Staff Directory", callback_data="admin_panel:staff"),
            InlineKeyboardButton(text="📊 Detailed Stats", callback_data="admin_panel:stats"),
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_panel:refresh"),
            InlineKeyboardButton(text="❌ Close", callback_data="admin_panel:close"),
        ]
    ])

    return text, keyboard

# --- Admin Panel Commands ---

@router.message(Command("panel", "settings"))
async def admin_panel_cmd(message: Message, db: DatabaseSession):
    """Displays the dynamic in-bot configuration dashboard."""
    text, keyboard = await build_panel_markup(db)
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("admin_toggle:"))
async def admin_toggle_callback(callback: CallbackQuery, db: DatabaseSession):
    """Handles real-time setting toggles from the control panel."""
    action = callback.data.split(":")[1]

    if action == "forcesub":
        fs_setting = await db.get_setting("force_sub_enabled")
        current = fs_setting.lower() in ("true", "1", "yes", "on") if fs_setting is not None else config.modules.force_sub
        new_val = "false" if current else "true"
        await db.set_setting("force_sub_enabled", new_val)
        await callback.answer(f"Force-Sub set to: {'ENABLED' if new_val == 'true' else 'DISABLED'}")

    elif action == "maintenance":
        maint_setting = await db.get_setting("maintenance_mode", "false")
        current = maint_setting.lower() in ("true", "1", "yes", "on")
        new_val = "false" if current else "true"
        await db.set_setting("maintenance_mode", new_val)
        await callback.answer(f"Maintenance Mode: {'ACTIVATED' if new_val == 'true' else 'DEACTIVATED'}")

    text, keyboard = await build_panel_markup(db)
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        pass

@router.callback_query(F.data.startswith("admin_panel:"))
async def admin_panel_action_callback(callback: CallbackQuery, db: DatabaseSession):
    """Handles secondary panel actions."""
    action = callback.data.split(":")[1]

    if action == "refresh":
        text, keyboard = await build_panel_markup(db)
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass
        await callback.answer("Panel refreshed ✅")

    elif action == "close":
        await callback.message.delete()
        await callback.answer("Panel closed")

    elif action == "staff":
        staff_users = await db.get_staff_users()
        lines = [f"• .env Admin ID: <code>{a}</code> (Superadmin)" for a in config.bot.admins]
        for s in staff_users:
            uname = f"@{s['username']}" if s.get('username') else s.get('first_name', 'User')
            lines.append(f"• {uname} (ID: <code>{s['user_id']}</code>) - <b>{s.get('role', 'user').upper()}</b>")

        staff_text = (
            "👑 <b>TeleCore Staff Directory</b>\n\n"
            + "\n".join(lines) + "\n\n"
            "<i>Use <code>/setrole &lt;user_id&gt; &lt;role&gt;</code> to manage team permissions.</i>"
        )
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to Panel", callback_data="admin_panel:refresh")]
        ])
        await callback.message.edit_text(staff_text, reply_markup=back_kb, parse_mode="HTML")
        await callback.answer()

    elif action == "stats":
        stats = await db.get_stats()
        stats_text = (
            "📊 <b>Detailed Bot Analytics</b>\n\n"
            f"• <b>Total Users:</b> <code>{stats['total_users']}</code>\n"
            f"• <b>Active Users:</b> <code>{stats['active_users']}</code>\n"
            f"• <b>Banned Users:</b> <code>{stats['banned_users']}</code>\n"
            f"• <b>Total Events Logged:</b> <code>{stats['total_events']}</code>"
        )
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to Panel", callback_data="admin_panel:refresh")]
        ])
        await callback.message.edit_text(stats_text, reply_markup=back_kb, parse_mode="HTML")
        await callback.answer()

# --- Force Subscription Configuration Commands ---

@router.message(Command("set_channel", "setchannel"))
async def admin_set_channel(message: Message, db: DatabaseSession):
    """Dynamically set the force subscription channel."""
    args = message.text.split()[1:]
    if not args:
        await message.reply(
            "⚠️ Usage: <code>/set_channel &lt;@channel_username_or_id&gt;</code>\n"
            "Example: <code>/set_channel @mychannel</code>",
            parse_mode="HTML"
        )
        return

    channel = args[0]
    await db.set_setting("force_sub_channel", channel)
    await db.set_setting("force_sub_enabled", "true")
    await message.reply(
        f"✅ <b>Force-Sub Channel Updated</b>\n\n"
        f"Target Channel: <code>{channel}</code>\n"
        f"Status: 🟢 <b>Enabled</b>\n\n"
        f"<i>Make sure the bot has been promoted to Admin in {channel}!</i>",
        parse_mode="HTML"
    )

@router.message(Command("set_channel_url", "setchannelurl"))
async def admin_set_channel_url(message: Message, db: DatabaseSession):
    """Dynamically set custom invite link for force subscription."""
    args = message.text.split()[1:]
    if not args:
        await message.reply("⚠️ Usage: <code>/set_channel_url &lt;invite_link&gt;</code>", parse_mode="HTML")
        return

    url = args[0]
    await db.set_setting("force_sub_url", url)
    await message.reply(f"✅ Force-Sub invite URL updated to:\n<code>{url}</code>", parse_mode="HTML")

@router.message(Command("maintenance"))
async def admin_maintenance_toggle(message: Message, db: DatabaseSession):
    """Toggle maintenance mode on or off."""
    args = message.text.split()[1:]
    if not args or args[0].lower() not in ("on", "off"):
        await message.reply("⚠️ Usage: <code>/maintenance &lt;on|off&gt;</code>", parse_mode="HTML")
        return

    is_on = args[0].lower() == "on"
    await db.set_setting("maintenance_mode", "true" if is_on else "false")
    await message.reply(
        f"🛠️ <b>Maintenance Mode:</b> {'⚠️ <b>ACTIVATED (Admins Only)</b>' if is_on else '🟢 <b>DEACTIVATED (Public Access)</b>'}",
        parse_mode="HTML"
    )

# --- Role-Based Access Control (RBAC) ---

@router.message(Command("setrole"))
async def admin_set_role(message: Message, db: DatabaseSession):
    """Promote or demote a user's role (owner, admin, moderator, user)."""
    # Verify executing user is Owner or Superadmin
    sender_id = message.from_user.id
    sender_role = await db.get_user_role(sender_id)
    if sender_id not in config.bot.admins and sender_role != "owner":
        await message.reply("⛔ Only Bot Owners can assign staff roles.", parse_mode="HTML")
        return

    args = message.text.split()[1:]
    if len(args) < 2 or not args[0].isdigit() or args[1].lower() not in VALID_ROLES:
        await message.reply(
            "⚠️ Usage: <code>/setrole &lt;user_id&gt; &lt;role&gt;</code>\n"
            f"Valid roles: <code>{', '.join(VALID_ROLES)}</code>",
            parse_mode="HTML"
        )
        return

    target_id = int(args[0])
    target_role = args[1].lower()

    # Prevent demoting .env superadmins
    if target_id in config.bot.admins and target_role != "owner":
        await message.reply("⛔ Cannot change the role of hardcoded .env Superadmins.", parse_mode="HTML")
        return

    ok = await db.set_user_role(target_id, target_role)
    if ok:
        await message.reply(
            f"👑 <b>Role Updated Successfully</b>\n\n"
            f"• User ID: <code>{target_id}</code>\n"
            f"• New Role: <b>{target_role.upper()}</b>",
            parse_mode="HTML"
        )
    else:
        await message.reply(f"⚠️ User <code>{target_id}</code> not found in database.", parse_mode="HTML")

@router.message(Command("admins", "staff"))
async def admin_list_staff(message: Message, db: DatabaseSession):
    """Lists all current bot staff and roles."""
    staff = await db.get_staff_users()
    lines = [f"• Superadmin (ID: <code>{a}</code>) - <b>OWNER (.env)</b>" for a in config.bot.admins]
    for s in staff:
        uname = f"@{s['username']}" if s.get('username') else s.get('first_name', 'User')
        lines.append(f"• {uname} (ID: <code>{s['user_id']}</code>) - <b>{s.get('role', 'user').upper()}</b>")

    text = (
        "👑 <b>Current TeleCore Staff Members:</b>\n\n"
        + "\n".join(lines) + "\n\n"
        "<i>Use <code>/setrole &lt;user_id&gt; &lt;role&gt;</code> to update roles.</i>"
    )
    await message.reply(text, parse_mode="HTML")

# --- Moderation: Ban & Unban with Reason ---

@router.message(Command("ban"))
async def admin_ban(message: Message, bot: Bot, db: DatabaseSession):
    """Ban a user by user_id with an optional reason."""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.reply("⚠️ Usage: <code>/ban &lt;user_id&gt; [reason]</code>", parse_mode="HTML")
        return

    target_id = int(parts[1])
    reason = parts[2] if len(parts) > 2 else "Violation of terms"

    # Cannot ban .env superadmins or fellow owners
    if target_id in config.bot.admins:
        await message.reply("⛔ Cannot ban a Superadmin configured in .env.", parse_mode="HTML")
        return

    target_role = await db.get_user_role(target_id)
    if target_role == "owner":
        await message.reply("⛔ Cannot ban another Owner.", parse_mode="HTML")
        return

    ok = await db.set_ban(target_id, is_banned=True, reason=reason)
    if ok:
        await message.reply(
            f"⛔ <b>User Suspended</b>\n\n"
            f"• User ID: <code>{target_id}</code>\n"
            f"• Reason: <i>{reason}</i>",
            parse_mode="HTML"
        )
        # Attempt to notify target user
        try:
            await bot.send_message(
                chat_id=target_id,
                text=f"⛔ <b>Account Suspended</b>\n\nYour account has been banned by an administrator.\n<b>Reason:</b> {reason}",
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        await message.reply(f"⚠️ User <code>{target_id}</code> not found in database.", parse_mode="HTML")

@router.message(Command("unban"))
async def admin_unban(message: Message, bot: Bot, db: DatabaseSession):
    """Unban a user by user_id."""
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.reply("⚠️ Usage: <code>/unban &lt;user_id&gt;</code>", parse_mode="HTML")
        return

    target_id = int(parts[1])
    ok = await db.set_ban(target_id, is_banned=False)
    if ok:
        await message.reply(f"✅ User <code>{target_id}</code> has been unbanned.", parse_mode="HTML")
        try:
            await bot.send_message(
                chat_id=target_id,
                text="✅ <b>Account Restored</b>\n\nYour suspension has been lifted by an administrator.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        await message.reply(f"⚠️ User <code>{target_id}</code> not found in database.", parse_mode="HTML")

@router.message(Command("user", "inspect"))
async def admin_inspect_user(message: Message, db: DatabaseSession):
    """Inspect user profile and role details."""
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.reply("⚠️ Usage: <code>/user &lt;user_id&gt;</code>", parse_mode="HTML")
        return

    target_id = int(parts[1])
    u = await db.get_user(target_id)
    if not u:
        await message.reply(f"⚠️ User <code>{target_id}</code> not found in database.", parse_mode="HTML")
        return

    status = "⛔ <b>Banned</b>" if u.get("is_banned") else "🟢 <b>Active</b>"
    reason_info = f"\n• <b>Ban Reason:</b> {u.get('ban_reason')}" if u.get("is_banned") else ""
    uname = f"@{u['username']}" if u.get('username') else "None"

    text = (
        f"👤 <b>User Profile: <code>{target_id}</code></b>\n\n"
        f"• <b>Name:</b> {u.get('first_name', '')} {u.get('last_name') or ''}\n"
        f"• <b>Username:</b> {uname}\n"
        f"• <b>Role:</b> <b>{u.get('role', 'user').upper()}</b>\n"
        f"• <b>Status:</b> {status}{reason_info}\n"
        f"• <b>Points:</b> <code>{u.get('points', 0)}</code>\n"
        f"• <b>Language:</b> <code>{u.get('language_code', 'en')}</code>\n"
        f"• <b>Joined:</b> <code>{u.get('created_at', 'Unknown')}</code>"
    )
    await message.reply(text, parse_mode="HTML")

# --- Stats & CSV Export ---

@router.message(Command("stats"))
async def admin_stats(message: Message, db: DatabaseSession):
    """Admin command to show system analytics."""
    stats = await db.get_stats()
    text = (
        "📊 <b>TeleCore Administration & Analytics</b>\n\n"
        f"• <b>Total Users:</b> <code>{stats['total_users']}</code>\n"
        f"• <b>Active Users:</b> <code>{stats['active_users']}</code>\n"
        f"• <b>Banned Users:</b> <code>{stats['banned_users']}</code>\n"
        f"• <b>Total Events Logged:</b> <code>{stats['total_events']}</code>"
    )
    await message.reply(text, parse_mode="HTML")

@router.message(Command("export", "export_users"))
async def admin_export_users(message: Message, db: DatabaseSession):
    """Exports all registered users into a CSV spreadsheet file."""
    status_msg = await message.reply("⏳ <i>Generating users export file...</i>", parse_mode="HTML")
    users = await db.get_all_users()

    if not users:
        await status_msg.edit_text("ℹ️ No user records found in database.", parse_mode="HTML")
        return

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "user_id", "username", "first_name", "last_name", "language_code",
        "referrer_id", "points", "is_banned", "created_at"
    ])
    writer.writeheader()
    for u in users:
        writer.writerow(u)

    csv_bytes = output.getvalue().encode("utf-8")
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    file = BufferedInputFile(csv_bytes, filename=f"users_export_{timestamp}.csv")

    await status_msg.delete()
    await message.reply_document(
        document=file,
        caption=f"📁 <b>Users Database Export</b>\nTotal Records: <code>{len(users)}</code>",
        parse_mode="HTML"
    )
