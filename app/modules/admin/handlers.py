import csv
import io
import os
import datetime
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
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
from app.services.logger import TelegramLogService
from app.modules.admin.states import AdminLogState

router = Router(name="admin_module")
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())

VALID_ROLES = ("owner", "admin", "moderator", "user")

async def build_panel_markup(db: DatabaseSession, tg_logger: Optional[TelegramLogService] = None) -> tuple[str, InlineKeyboardMarkup]:
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

    # 3. Dynamic Logging state
    log_status_str = "⚪ <i>Not Configured</i>"
    if tg_logger:
        log_cfg = await tg_logger.get_effective_config()
        if log_cfg["enabled"] and log_cfg["chat_id"]:
            log_type_label = "💬 Topic Group" if log_cfg["thread_id"] or log_cfg.get("chat_type") == "topic_group" else "📢 Normal"
            topic_str = f" (#{log_cfg['thread_id']})" if log_cfg["thread_id"] else ""
            log_status_str = f"🟢 <b>ON</b> — <code>{log_cfg['chat_id']}</code> [{log_type_label}{topic_str}]"
        elif log_cfg["chat_id"]:
            log_status_str = f"🔴 <i>OFF</i> (<code>{log_cfg['chat_id']}</code>)"
        else:
            log_status_str = "⚪ <i>Not Set</i>"

    # 4. Overall stats
    stats = await db.get_stats()

    fs_btn_text = "📢 Force-Sub: ON 🟢" if fs_enabled else "📢 Force-Sub: OFF 🔴"
    maint_btn_text = "🛠️ Maint: ACTIVE ⚠️" if maint_enabled else "🛠️ Maint: OFF 🟢"

    text = (
        "🎛️ <b>TeleCore Dynamic Management Panel</b>\n\n"
        "⚡ <b>Live System & Feature Status:</b>\n"
        f"• <b>Logs Channel/Group:</b> {log_status_str}\n"
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
            InlineKeyboardButton(text="📑 Logs Settings", callback_data="admin_panel:logs"),
            InlineKeyboardButton(text="👑 Staff Directory", callback_data="admin_panel:staff"),
        ],
        [
            InlineKeyboardButton(text=fs_btn_text, callback_data="admin_toggle:forcesub"),
            InlineKeyboardButton(text=maint_btn_text, callback_data="admin_toggle:maintenance"),
        ],
        [
            InlineKeyboardButton(text="📊 Detailed Stats", callback_data="admin_panel:stats"),
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_panel:refresh"),
        ],
        [
            InlineKeyboardButton(text="❌ Close", callback_data="admin_panel:close"),
        ]
    ])

    return text, keyboard


async def build_logs_panel_markup(db: DatabaseSession, tg_logger: TelegramLogService) -> tuple[str, InlineKeyboardMarkup]:
    """Generates the dedicated forum topic logs configuration dashboard."""
    cfg = await tg_logger.get_effective_config(db=db)
    is_enabled = cfg["enabled"] and bool(cfg["chat_id"])
    has_chat = bool(cfg["chat_id"])

    stats = await db.get_stats()
    total_users = stats.get("total_users", 0)

    status_icon = "🟢 <b>ACTIVE</b>" if is_enabled else ("🔴 <i>DISABLED</i>" if has_chat else "⚪ <i>NOT CONFIGURED</i>")
    dest_str = f"<code>{cfg['chat_id']}</code>" if has_chat else "<i>None (Not Set)</i>"

    text = (
        "📑 <b>Forum Topic Logs Supergroup Dashboard</b>\n\n"
        f"• <b>Logging Status:</b> {status_icon}\n"
        f"• <b>Logs Supergroup:</b> {dest_str}\n"
        "• <b>Topic Mode:</b> 💬 <b>1 Dedicated Topic Per User</b> (Always ON 🟢)\n"
        f"• <b>Total Registered Users:</b> <code>{total_users}</code>\n\n"
        "<i>Har user ka personal forum topic banega. User activities, messages aur admin live support sab user ke topic me relay hoga!</i>"
    )

    toggle_btn_text = "🔴 Turn Logs OFF" if cfg["enabled"] else "🟢 Turn Logs ON"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=toggle_btn_text, callback_data="admin_toggle:logging"),
            InlineKeyboardButton(text="🧪 Send Test Log", callback_data="admin_action:test_log"),
        ],
        [
            InlineKeyboardButton(text="💬 Set Logs Supergroup", callback_data="admin_prompt:log_topic_chat"),
            InlineKeyboardButton(text="🔄 Sync All User Topics", callback_data="admin_action:sync_topics"),
        ],
        [
            InlineKeyboardButton(text="🗑️ Disconnect Logs Group", callback_data="admin_action:reset_logs"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Back to Control Panel", callback_data="admin_panel:refresh"),
        ]
    ])
    return text, keyboard


# --- Admin Panel Commands ---

@router.message(Command("panel", "settings"))
async def admin_panel_cmd(message: Message, db: DatabaseSession, tg_logger: TelegramLogService):
    """Displays the dynamic in-bot configuration dashboard."""
    text, keyboard = await build_panel_markup(db, tg_logger)
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("admin_toggle:"))
async def admin_toggle_callback(callback: CallbackQuery, db: DatabaseSession, tg_logger: TelegramLogService):
    """Handles real-time setting toggles from the control panel."""
    action = callback.data.split(":")[1]

    if action == "forcesub":
        fs_setting = await db.get_setting("force_sub_enabled")
        current = fs_setting.lower() in ("true", "1", "yes", "on") if fs_setting is not None else config.modules.force_sub
        new_val = "false" if current else "true"
        await db.set_setting("force_sub_enabled", new_val)
        await callback.answer(f"Force-Sub set to: {'ENABLED' if new_val == 'true' else 'DISABLED'}")
        text, keyboard = await build_panel_markup(db, tg_logger)
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass

    elif action == "maintenance":
        maint_setting = await db.get_setting("maintenance_mode", "false")
        current = maint_setting.lower() in ("true", "1", "yes", "on")
        new_val = "false" if current else "true"
        await db.set_setting("maintenance_mode", new_val)
        await callback.answer(f"Maintenance Mode: {'ACTIVATED' if new_val == 'true' else 'DEACTIVATED'}")
        text, keyboard = await build_panel_markup(db, tg_logger)
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass

    elif action == "logging":
        cfg = await tg_logger.get_effective_config()
        new_val = "false" if cfg["enabled"] else "true"
        await db.set_setting("log_enabled", new_val)
        await callback.answer(f"Logging is now: {'ENABLED' if new_val == 'true' else 'DISABLED'}")
        text, keyboard = await build_logs_panel_markup(db, tg_logger)
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass

    elif action == "user_topics":
        cfg = await tg_logger.get_effective_config()
        new_val = "false" if cfg["user_topics"] else "true"
        await db.set_setting("log_user_topics", new_val)
        await callback.answer(f"Per-User Forum Topics: {'ENABLED' if new_val == 'true' else 'DISABLED'}")
        text, keyboard = await build_logs_panel_markup(db, tg_logger)
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass


@router.callback_query(F.data.startswith("admin_action:"))
async def admin_action_callback(callback: CallbackQuery, db: DatabaseSession, tg_logger: TelegramLogService):
    """Handles log actions like testing, syncing user topics, or resetting."""
    action = callback.data.split(":")[1]

    if action == "test_log":
        cfg = await tg_logger.get_effective_config(db=db)
        if not cfg["chat_id"]:
            await callback.answer("⚠️ No log destination configured! Please set a forum supergroup first.", show_alert=True)
            return

        await callback.answer("Sending verification test log...")
        ok, msg, _ = await tg_logger.test_connection(cfg["chat_id"], cfg["thread_id"])
        if ok:
            await callback.message.reply(
                f"✅ <b>Test Log Delivered Successfully!</b>\n\n"
                f"• <b>Destination:</b> <code>{cfg['chat_id']}</code>\n"
                f"• <b>Topic ID:</b> <code>{cfg['thread_id'] or 'None (General)'}</code>\n"
                f"• <b>Result:</b> {msg}",
                parse_mode="HTML"
            )
        else:
            await callback.message.reply(
                f"❌ <b>Test Log Delivery Failed</b>\n\n"
                f"• <b>Destination:</b> <code>{cfg['chat_id']}</code>\n"
                f"• <b>Error:</b> <code>{msg}</code>\n\n"
                "<i>Make sure the bot has Administrator permissions in the forum supergroup!</i>",
                parse_mode="HTML"
            )

    elif action == "sync_topics":
        cfg = await tg_logger.get_effective_config(db=db)
        if not cfg["chat_id"]:
            await callback.answer("⚠️ No forum log group configured! Click [💬 Set Logs Supergroup] first.", show_alert=True)
            return

        await callback.answer("🔄 Syncing topics for all database users...")
        status_msg = await callback.message.reply("⏳ <i>Syncing topics for all database users...</i>", parse_mode="HTML")
        created, existing, failed = await tg_logger.sync_all_user_topics(db)
        await status_msg.edit_text(
            f"🔄 <b>User Topics Synchronization Completed!</b>\n\n"
            f"• 🆕 <b>New Topics Created:</b> <code>{created}</code>\n"
            f"• ℹ️ <b>Already Had Topics:</b> <code>{existing}</code>\n"
            f"• ⚠️ <b>Failed / Skipped:</b> <code>{failed}</code>\n\n"
            "<i>All active bot users now have their dedicated forum log topic!</i>",
            parse_mode="HTML"
        )

    elif action == "reset_logs":
        await db.set_setting("log_chat_id", "")
        await db.set_setting("log_thread_id", "")
        await db.set_setting("log_enabled", "false")
        await db.set_setting("log_user_topics", "false")
        await callback.answer("Logging destination reset and disconnected.", show_alert=True)
        text, keyboard = await build_logs_panel_markup(db, tg_logger)
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass


@router.callback_query(F.data.startswith("admin_prompt:"))
async def admin_prompt_callback(callback: CallbackQuery, state: FSMContext):
    """Initiates interactive FSM input for log settings."""
    prompt_type = callback.data.split(":")[1]
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="admin_panel:logs")]
    ])

    if prompt_type in ("log_topic_chat", "log_chat"):
        await state.set_state(AdminLogState.waiting_for_chat)
        await callback.message.edit_text(
            "💬 <b>Connect Forum Supergroup for Dedicated User Logs</b>\n\n"
            "Forward any message from your Forum Supergroup (with Topics enabled), or send its <code>-100...</code> Chat ID:\n\n"
            "<b>Requirements:</b>\n"
            "1. Group must have <b>Forum Topics</b> enabled.\n"
            "2. Bot must be an <b>Administrator</b> with <b>Manage Topics</b> and <b>Post Messages</b> permissions.\n\n"
            "<i>Every bot user will get an individual dedicated topic created automatically!</i>",
            reply_markup=cancel_kb,
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data.startswith("admin_panel:"))
async def admin_panel_action_callback(callback: CallbackQuery, db: DatabaseSession, tg_logger: TelegramLogService, state: FSMContext):
    """Handles secondary panel actions."""
    action = callback.data.split(":")[1]

    if action == "refresh":
        await state.clear()
        text, keyboard = await build_panel_markup(db, tg_logger)
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass
        await callback.answer("Panel refreshed ✅")

    elif action == "logs":
        await state.clear()
        text, keyboard = await build_logs_panel_markup(db, tg_logger)
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass
        await callback.answer()

    elif action == "close":
        await state.clear()
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

# --- Dynamic Logs Group & Topic Configuration ---

@router.message(Command("cancel"), AdminLogState.waiting_for_chat)
async def admin_cancel_log_setup(message: Message, state: FSMContext, db: DatabaseSession, tg_logger: TelegramLogService):
    """Cancels ongoing log setup and returns to logs dashboard."""
    await state.clear()
    text, kb = await build_logs_panel_markup(db, tg_logger)
    await message.reply("❌ Log setup cancelled.", reply_markup=kb, parse_mode="HTML")

@router.message(AdminLogState.waiting_for_chat)
async def admin_log_chat_input(message: Message, state: FSMContext, db: DatabaseSession, tg_logger: TelegramLogService):
    """Receives target forum supergroup ID or forwarded message for logging."""
    target_chat = None

    if message.forward_from_chat:
        target_chat = message.forward_from_chat.id
    elif message.text:
        raw = message.text.strip()
        if raw.startswith("http"):
            parts = raw.rstrip("/").split("/")
            if "t.me" in parts:
                idx = parts.index("t.me") if "t.me" in parts else -1
                if idx != -1 and len(parts) > idx + 1:
                    raw = parts[idx + 1]
                    if raw == "c" and len(parts) > idx + 2:
                        raw = "-100" + parts[idx + 2]
        try:
            target_chat = int(raw)
        except ValueError:
            target_chat = raw if raw.startswith("@") else f"@{raw}"

    if not target_chat:
        await message.reply("⚠️ Could not detect chat. Please send a valid Chat ID (e.g. <code>-1001234567890</code>) or <code>@username</code>:", parse_mode="HTML")
        return

    status_msg = await message.reply("⏳ <i>Verifying Forum Supergroup connectivity & admin permissions...</i>", parse_mode="HTML")
    ok, detail, chat_type = await tg_logger.test_connection(target_chat)

    if not ok:
        await status_msg.edit_text(
            f"❌ <b>Connection Test Failed for <code>{target_chat}</code></b>\n\n"
            f"• <b>Error:</b> <code>{detail}</code>\n\n"
            "<b>Troubleshooting:</b>\n"
            "1. Did you add the bot to that Forum Supergroup?\n"
            "2. Is <b>Topics / Forum mode</b> enabled in group settings?\n"
            "3. Did you promote the bot to <b>Administrator</b> with <b>Manage Topics</b> and <b>Post Messages</b> permissions?\n\n"
            "<i>Send another ID to retry, or send <code>/cancel</code> to abort.</i>",
            parse_mode="HTML"
        )
        return

    await db.set_setting("log_chat_id", str(target_chat))
    await db.set_setting("log_enabled", "true")
    await db.set_setting("log_user_topics", "true")
    await db.set_setting("log_chat_type", "topic_group")

    await status_msg.edit_text(
        f"✅ <b>Connected to Forum Supergroup!</b>\n\n"
        f"• <b>Chat:</b> <code>{target_chat}</code> ({chat_type})\n"
        "⏳ <i>Now auto-creating / syncing dedicated topics for all database users...</i>",
        parse_mode="HTML"
    )

    created, existing, failed = await tg_logger.sync_all_user_topics(db)
    await state.clear()
    text, kb = await build_logs_panel_markup(db, tg_logger)

    await status_msg.edit_text(
        f"🎉 <b>Forum Topic Logging Configured!</b>\n\n"
        f"• <b>Destination:</b> <code>{target_chat}</code>\n"
        f"• <b>Mode:</b> 🧵 1 Dedicated Topic Per User\n"
        f"• <b>Status:</b> 🟢 <b>Active</b>\n\n"
        f"<b>Initial Topic Sync:</b>\n"
        f"• 🆕 <b>Created:</b> <code>{created}</code>\n"
        f"• ℹ️ <b>Existing:</b> <code>{existing}</code>\n"
        f"• ⚠️ <b>Failed:</b> <code>{failed}</code>\n\n"
        "<i>New users will also automatically have their topic created whenever they interact with the bot!</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# --- Direct Admin Commands for Logs ---

@router.message(Command("logs", "logsettings", "log_settings"))
async def admin_logs_menu_cmd(message: Message, db: DatabaseSession, tg_logger: TelegramLogService):
    """Opens the logs configuration menu."""
    text, kb = await build_logs_panel_markup(db, tg_logger)
    await message.reply(text, reply_markup=kb, parse_mode="HTML")

@router.message(Command("logson"))
async def admin_logson_cmd(message: Message, db: DatabaseSession, tg_logger: TelegramLogService):
    """Turns logs ON dynamically."""
    await db.set_setting("log_enabled", "true")
    cfg = await tg_logger.get_effective_config(db=db)
    dest = f"<code>{cfg['chat_id']}</code>" if cfg['chat_id'] else "<i>(Not Set yet - use /setlogs)</i>"
    await message.reply(f"🟢 <b>Telegram Logging Activated</b>\nDestination: {dest}", parse_mode="HTML")

@router.message(Command("logsoff"))
async def admin_logsoff_cmd(message: Message, db: DatabaseSession):
    """Turns logs OFF dynamically."""
    await db.set_setting("log_enabled", "false")
    await message.reply("🔴 <b>Telegram Logging Deactivated</b>", parse_mode="HTML")

@router.message(Command("setlogs", "set_logs"))
async def admin_setlogs_cmd(message: Message, db: DatabaseSession, tg_logger: TelegramLogService):
    """
    Directly set logs forum supergroup and auto-sync user topics.
    Usage:
      /setlogs <supergroup_chat_id>
    Example:
      /setlogs -1001234567890
    """
    args = message.text.split()[1:]
    if not args:
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/setlogs &lt;supergroup_chat_id&gt;</code>\n\n"
            "<b>Example:</b> <code>/setlogs -1001234567890</code>\n\n"
            "<i>(Group must have Forum Topics enabled and bot must be Administrator with Manage Topics)</i>",
            parse_mode="HTML"
        )
        return

    raw_chat = args[0].strip()
    try:
        target_chat = int(raw_chat)
    except ValueError:
        target_chat = raw_chat if raw_chat.startswith("@") else f"@{raw_chat}"

    status_msg = await message.reply("⏳ <i>Testing connection and permissions...</i>", parse_mode="HTML")
    ok, detail, chat_type = await tg_logger.test_connection(target_chat)

    if not ok:
        await status_msg.edit_text(
            f"❌ <b>Could not connect to {target_chat}</b>\n\n"
            f"• <b>Error:</b> <code>{detail}</code>\n\n"
            "<i>Make sure the bot has been added as Administrator in the forum supergroup with 'Manage Topics' and 'Post Messages' permissions.</i>",
            parse_mode="HTML"
        )
        return

    await db.set_setting("log_chat_id", str(target_chat))
    await db.set_setting("log_enabled", "true")
    await db.set_setting("log_user_topics", "true")
    await db.set_setting("log_chat_type", "topic_group")

    await status_msg.edit_text(
        f"✅ <b>Supergroup Connected!</b>\n\n"
        f"• <b>Destination:</b> <code>{target_chat}</code>\n"
        "⏳ <i>Auto-syncing dedicated topics for all users...</i>",
        parse_mode="HTML"
    )

    created, existing, failed = await tg_logger.sync_all_user_topics(db)
    await status_msg.edit_text(
        f"🎉 <b>Forum Topic Logging Configured!</b>\n\n"
        f"• <b>Destination:</b> <code>{target_chat}</code>\n"
        f"• <b>Mode:</b> 🧵 1 Dedicated Topic Per User\n"
        f"• <b>Status:</b> 🟢 <b>Active</b>\n\n"
        f"<b>Topic Sync:</b>\n"
        f"• 🆕 <b>Created:</b> <code>{created}</code>\n"
        f"• ℹ️ <b>Existing:</b> <code>{existing}</code>\n"
        f"• ⚠️ <b>Failed:</b> <code>{failed}</code>",
        parse_mode="HTML"
    )

@router.message(Command("synctopics", "sync_topics"))
async def admin_sync_topics_cmd(message: Message, db: DatabaseSession, tg_logger: TelegramLogService):
    """
    Sync and create missing topics in the logs supergroup for all database users.
    Usage: /synctopics
    """
    cfg = await tg_logger.get_effective_config(db=db)
    if not cfg["chat_id"]:
        await message.reply("⚠️ Please configure the log supergroup first via <code>/setlogs &lt;chat_id&gt;</code> or in <code>/logs</code>.", parse_mode="HTML")
        return

    status_msg = await message.reply("⏳ <i>Syncing topics for all database users...</i>", parse_mode="HTML")
    created, existing, failed = await tg_logger.sync_all_user_topics(db)
    await status_msg.edit_text(
        f"🔄 <b>User Topics Synchronization Completed!</b>\n\n"
        f"• 🆕 <b>New Topics Created:</b> <code>{created}</code>\n"
        f"• ℹ️ <b>Already Had Topics:</b> <code>{existing}</code>\n"
        f"• ⚠️ <b>Failed / Skipped:</b> <code>{failed}</code>\n\n"
        "<i>All active bot users now have their dedicated forum log topic!</i>",
        parse_mode="HTML"
    )

@router.message(Command("testlog", "test_log"))
async def admin_test_log_cmd(message: Message, db: DatabaseSession, tg_logger: TelegramLogService):
    """Sends a verification test log to the currently active destination."""
    cfg = await tg_logger.get_effective_config(db=db)
    if not cfg["chat_id"]:
        await message.reply("⚠️ No log destination configured! Use <code>/setlogs &lt;chat_id&gt;</code> first.", parse_mode="HTML")
        return

    status_msg = await message.reply("⏳ <i>Sending test log...</i>", parse_mode="HTML")
    ok, detail, chat_type = await tg_logger.test_connection(cfg["chat_id"], cfg["thread_id"])
    if ok:
        topic_info = f" (Topic #{cfg['thread_id']})" if cfg["thread_id"] else ""
        await status_msg.edit_text(
            f"✅ <b>Test log delivered successfully!</b>\n\n"
            f"• <b>Destination:</b> <code>{cfg['chat_id']}</code>{topic_info}\n"
            f"• <b>Type:</b> <code>{chat_type}</code>\n"
            f"• <b>Status:</b> 🟢 Connected",
            parse_mode="HTML"
        )
    else:
        await status_msg.edit_text(
            f"❌ <b>Delivery Failed:</b>\n<code>{detail}</code>\n\n"
            "<i>Ensure the bot has admin permissions in the destination chat.</i>",
            parse_mode="HTML"
        )

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
