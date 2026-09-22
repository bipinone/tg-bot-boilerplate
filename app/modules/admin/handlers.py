import csv
import io
import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from app.bot.filters.admin import IsAdminFilter
from app.database.session import DatabaseSession

router = Router(name="admin_module")
router.message.filter(IsAdminFilter())

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

@router.message(Command("ban"))
async def admin_ban(message: Message, db: DatabaseSession):
    """Ban a user by user_id."""
    args = message.text.split()[1:]
    if not args or not args[0].isdigit():
        await message.reply("⚠️ Usage: <code>/ban &lt;user_id&gt;</code>", parse_mode="HTML")
        return

    target_id = int(args[0])
    ok = await db.set_ban(target_id, is_banned=True)
    if ok:
        await message.reply(f"⛔ User <code>{target_id}</code> has been banned.", parse_mode="HTML")
    else:
        await message.reply(f"⚠️ User <code>{target_id}</code> not found.", parse_mode="HTML")

@router.message(Command("unban"))
async def admin_unban(message: Message, db: DatabaseSession):
    """Unban a user by user_id."""
    args = message.text.split()[1:]
    if not args or not args[0].isdigit():
        await message.reply("⚠️ Usage: <code>/unban &lt;user_id&gt;</code>", parse_mode="HTML")
        return

    target_id = int(args[0])
    ok = await db.set_ban(target_id, is_banned=False)
    if ok:
        await message.reply(f"✅ User <code>{target_id}</code> has been unbanned.", parse_mode="HTML")
    else:
        await message.reply(f"⚠️ User <code>{target_id}</code> not found.", parse_mode="HTML")
