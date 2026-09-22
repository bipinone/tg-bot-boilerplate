import asyncio
import time
import logging
from typing import Optional, List
from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
from app.bot.filters.admin import IsAdminFilter
from app.database.session import DatabaseSession

logger = logging.getLogger(__name__)

router = Router(name="broadcast_module")
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())

# --- Global Broadcast State Management ---
broadcast_state = {
    "running": False,
    "paused": False,
    "cancelled": False,
    "total": 0,
    "processed": 0,
    "success": 0,
    "blocked": 0,
    "failed": 0,
    "start_time": 0.0
}

broadcast_pause_event = asyncio.Event()
broadcast_pause_event.set()

def render_progress_bar(current: int, total: int, length: int = 12) -> str:
    """Renders a clean unicode visual progress bar."""
    if total <= 0:
        return "[" + "░" * length + "] 0.0%"
    fraction = min(max(current / total, 0.0), 1.0)
    filled = int(fraction * length)
    bar = "█" * filled + "░" * (length - filled)
    percent = fraction * 100
    return f"[{bar}] <b>{percent:.1f}%</b>"

def get_broadcast_controls_markup(is_paused: bool = False) -> InlineKeyboardMarkup:
    """Generates real-time pause/resume/cancel interactive buttons."""
    pause_resume_btn = (
        InlineKeyboardButton(text="▶️ Resume", callback_data="bcast:resume")
        if is_paused
        else InlineKeyboardButton(text="⏸️ Pause", callback_data="bcast:pause")
    )
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            pause_resume_btn,
            InlineKeyboardButton(text="🛑 Cancel", callback_data="bcast:cancel")
        ]
    ])

# --- Broadcast Command Handler ---

@router.message(Command("broadcast"))
async def broadcast_command(message: Message, bot: Bot, db: DatabaseSession):
    """
    High-Performance Flag-Based Mass Broadcast Engine.
    
    Supported Flags:
      -copy    : Cleanly clone/copy message without 'Forwarded from' header.
      -pin     : Automatically pin message in user/group chats.
      -silent  : Deliver quietly with notifications disabled.
      -fast    : High-throughput mode (50 concurrent workers).
      -user    : Send to private bot users.
    
    Usage:
      Reply to any message: `/broadcast -copy -pin -silent`
      Or with text: `/broadcast -silent Update: Maintenance completed!`
    """
    if broadcast_state["running"]:
        await message.reply(
            "⚠️ <b>Broadcast already in progress!</b>\n\n"
            "Use <code>/broadcast_pause</code>, <code>/broadcast_resume</code>, or <code>/broadcast_cancel</code> to manage it.",
            parse_mode="HTML"
        )
        return

    reply_msg = message.reply_to_message
    raw_text = message.text or ""
    parts = raw_text.split()
    cmd = parts[0] if parts else "/broadcast"
    args = parts[1:]

    # Parse flags
    copy_mode = "-copy" in args
    pin_mode = "-pin" in args
    silent_mode = "-silent" in args
    fast_mode = "-fast" in args
    concurrency_limit = 50 if fast_mode else 30

    # Extract non-flag text content
    clean_text_words = [w for w in args if not w.startswith("-")]
    broadcast_text = " ".join(clean_text_words) if clean_text_words else None

    if not reply_msg and not broadcast_text:
        await message.reply(
            "📢 <b>Pro Mass Broadcast Engine</b>\n\n"
            "<b>Usage:</b>\n"
            "• Reply to any message: <code>/broadcast -copy -pin -silent</code>\n"
            "• Or send direct text: <code>/broadcast -fast Your announcement here</code>\n\n"
            "<b>Supported Flags:</b>\n"
            "• <code>-copy</code> : Copy without forward tag\n"
            "• <code>-pin</code> : Pin message after delivery\n"
            "• <code>-silent</code> : Send with notification disabled\n"
            "• <code>-fast</code> : Ultra-fast mode (50 parallel workers)\n\n"
            "<b>Live Controls:</b>\n"
            "• <code>/broadcast_pause</code> | <code>/broadcast_resume</code> | <code>/broadcast_cancel</code>",
            parse_mode="HTML"
        )
        return

    # Fetch recipients
    targets = await db.get_all_active_user_ids()
    total_targets = len(targets)

    if total_targets == 0:
        await message.reply("ℹ️ No active users found in database to broadcast to.")
        return

    # Initialize State
    broadcast_state["running"] = True
    broadcast_state["paused"] = False
    broadcast_state["cancelled"] = False
    broadcast_state["total"] = total_targets
    broadcast_state["processed"] = 0
    broadcast_state["success"] = 0
    broadcast_state["blocked"] = 0
    broadcast_state["failed"] = 0
    broadcast_state["start_time"] = time.time()
    broadcast_pause_event.set()

    status_msg = await message.reply(
        "🚀 <b>Initializing High-Speed Broadcast...</b>\n\n"
        f"• Total Targets: <code>{total_targets}</code>\n"
        f"• Concurrency: <code>{concurrency_limit} workers</code>\n"
        f"• Mode: <code>{'Copy' if copy_mode else 'Forward/Direct'}</code>\n"
        f"• Pin: <code>{'Yes' if pin_mode else 'No'}</code> | Silent: <code>{'Yes' if silent_mode else 'No'}</code>",
        reply_markup=get_broadcast_controls_markup(is_paused=False),
        parse_mode="HTML"
    )

    last_edit_time = 0.0

    async def update_live_status(final: bool = False):
        nonlocal last_edit_time
        now = time.time()
        if not final and (now - last_edit_time < 2.0):
            return

        last_edit_time = now
        elapsed = max(int(now - broadcast_state["start_time"]), 1)
        proc = broadcast_state["processed"]
        speed = proc / elapsed if elapsed > 0 else 0
        rem_items = max(total_targets - proc, 0)
        eta_seconds = int(rem_items / speed) if speed > 0 else 0

        header = "✅ <b>Broadcast Completed!</b>" if final else (
            "⏸️ <b>Broadcast PAUSED</b>" if broadcast_state["paused"] else "🚀 <b>Broadcasting in Progress...</b>"
        )
        if broadcast_state["cancelled"]:
            header = "🛑 <b>Broadcast CANCELLED</b>"

        bar = render_progress_bar(proc, total_targets)
        text = (
            f"{header}\n\n"
            f"{bar}\n\n"
            "📊 <b>Delivery Statistics:</b>\n"
            f"• <b>Processed:</b> <code>{proc} / {total_targets}</code>\n"
            f"• <b>Delivered:</b> <code>{broadcast_state['success']}</code> ✅\n"
            f"• <b>Blocked/Deleted:</b> <code>{broadcast_state['blocked']}</code> ⛔\n"
            f"• <b>Failed:</b> <code>{broadcast_state['failed']}</code> ❌\n\n"
            "⚡ <b>Performance:</b>\n"
            f"• <b>Speed:</b> <code>{speed:.1f} msg/s</code>\n"
            f"• <b>Elapsed:</b> <code>{elapsed}s</code>" + (f" | <b>ETA:</b> <code>~{eta_seconds}s</code>" if not final else "")
        )

        reply_markup = None if final or broadcast_state["cancelled"] else get_broadcast_controls_markup(broadcast_state["paused"])
        try:
            await status_msg.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            pass

    semaphore = asyncio.Semaphore(concurrency_limit)

    async def _send_worker(target_id: int):
        if broadcast_state["cancelled"]:
            return

        # Handle pause
        while broadcast_state["paused"]:
            await broadcast_pause_event.wait()
            if broadcast_state["cancelled"]:
                return

        async with semaphore:
            sent_msg = None
            try:
                if reply_msg:
                    if copy_mode:
                        sent_msg = await reply_msg.copy_to(chat_id=target_id, disable_notification=silent_mode)
                    else:
                        sent_msg = await reply_msg.forward(chat_id=target_id, disable_notification=silent_mode)
                else:
                    sent_msg = await bot.send_message(
                        chat_id=target_id,
                        text=broadcast_text,
                        parse_mode="HTML",
                        disable_notification=silent_mode
                    )

                if pin_mode and sent_msg:
                    try:
                        await bot.pin_chat_message(chat_id=target_id, message_id=sent_msg.message_id, disable_notification=True)
                    except Exception:
                        pass

                broadcast_state["success"] += 1

            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                return await _send_worker(target_id)

            except TelegramForbiddenError:
                broadcast_state["blocked"] += 1
                try:
                    await db.set_ban(target_id, is_banned=True, reason="User blocked the bot")
                except Exception:
                    pass

            except TelegramBadRequest as e:
                broadcast_state["failed"] += 1
                err_str = str(e).lower()
                if "chat not found" in err_str or "user is deactivated" in err_str:
                    broadcast_state["blocked"] += 1

            except Exception as e:
                logger.debug("Failed sending broadcast to %s: %s", target_id, e)
                broadcast_state["failed"] += 1

            finally:
                broadcast_state["processed"] += 1
                await update_live_status(final=False)

    try:
        tasks = [_send_worker(tid) for tid in targets]
        await asyncio.gather(*tasks)
    finally:
        broadcast_state["running"] = False
        await update_live_status(final=True)

# --- Broadcast Control Commands ---

@router.message(Command("broadcast_pause"))
async def broadcast_pause_cmd(message: Message):
    """Pause currently running broadcast."""
    if not broadcast_state["running"]:
        await message.reply("❌ No broadcast is currently running.")
        return
    broadcast_state["paused"] = True
    broadcast_pause_event.clear()
    await message.reply("⏸️ <b>Broadcast paused.</b> Use <code>/broadcast_resume</code> to continue.", parse_mode="HTML")

@router.message(Command("broadcast_resume"))
async def broadcast_resume_cmd(message: Message):
    """Resume a paused broadcast."""
    if not broadcast_state["paused"]:
        await message.reply("ℹ️ Broadcast is not paused.")
        return
    broadcast_state["paused"] = False
    broadcast_pause_event.set()
    await message.reply("▶️ <b>Broadcast resumed!</b>", parse_mode="HTML")

@router.message(Command("broadcast_cancel"))
async def broadcast_cancel_cmd(message: Message):
    """Cancel a running or paused broadcast."""
    if not broadcast_state["running"]:
        await message.reply("❌ No broadcast is currently running.")
        return
    broadcast_state["cancelled"] = True
    broadcast_state["paused"] = False
    broadcast_pause_event.set()
    await message.reply("🛑 <b>Broadcast cancelled.</b> Pending tasks will terminate.", parse_mode="HTML")

# --- Inline Button Callbacks ---

@router.callback_query(F.data.startswith("bcast:"))
async def broadcast_callback_control(callback: CallbackQuery):
    """Handle 1-tap interactive pause, resume, and cancel buttons on broadcast progress message."""
    action = callback.data.split(":")[1]

    if action == "pause":
        if not broadcast_state["running"]:
            await callback.answer("No broadcast running.", show_alert=True)
            return
        broadcast_state["paused"] = True
        broadcast_pause_event.clear()
        await callback.answer("Broadcast paused ⏸️")
        try:
            await callback.message.edit_reply_markup(reply_markup=get_broadcast_controls_markup(is_paused=True))
        except Exception:
            pass

    elif action == "resume":
        if not broadcast_state["paused"]:
            await callback.answer("Broadcast is not paused.", show_alert=True)
            return
        broadcast_state["paused"] = False
        broadcast_pause_event.set()
        await callback.answer("Broadcast resumed ▶️")
        try:
            await callback.message.edit_reply_markup(reply_markup=get_broadcast_controls_markup(is_paused=False))
        except Exception:
            pass

    elif action == "cancel":
        if not broadcast_state["running"]:
            await callback.answer("No broadcast running.", show_alert=True)
            return
        broadcast_state["cancelled"] = True
        broadcast_state["paused"] = False
        broadcast_pause_event.set()
        await callback.answer("Broadcast cancelled 🛑")
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
