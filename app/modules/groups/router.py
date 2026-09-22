import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR
from aiogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from app.database.session import DatabaseSession
from app.bot.filters.admin import IsAdminFilter

logger = logging.getLogger(__name__)

router = Router(name="groups_module")

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=(MEMBER | ADMINISTRATOR | CREATOR)))
async def bot_added_to_group(event: ChatMemberUpdated, db: DatabaseSession):
    """Triggered when bot is added to a group or promoted to admin."""
    chat = event.chat
    logger.info("Bot added to group %s (ID: %s)", chat.title, chat.id)
    await db.upsert_group(
        chat_id=chat.id,
        title=chat.title or "Untitled Group",
        chat_type=chat.type,
        is_active=True
    )

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=(KICKED | LEFT)))
async def bot_removed_from_group(event: ChatMemberUpdated, db: DatabaseSession):
    """Triggered when bot is removed from a group."""
    chat = event.chat
    logger.info("Bot removed from group %s (ID: %s)", chat.title, chat.id)
    await db.upsert_group(
        chat_id=chat.id,
        title=chat.title or "Untitled Group",
        chat_type=chat.type,
        is_active=False
    )

@router.message(Command("groups"))
async def admin_list_groups(message: Message, db: DatabaseSession):
    """List all registered active groups (Admin only)."""
    group_ids = await db.get_all_active_group_ids()
    if not group_ids:
        await message.reply("ℹ️ No active groups currently registered.")
        return

    lines = [f"👥 <b>Active Communities ({len(group_ids)}):</b>\n"]
    for cid in group_ids:
        grp = await db.get_group(cid)
        if grp:
            lines.append(f"• <b>{grp.get('title', 'Group')}</b> (ID: <code>{cid}</code>) [{grp.get('chat_type', 'group')}]")
        else:
            lines.append(f"• ID: <code>{cid}</code>")

    await message.reply("\n".join(lines), parse_mode="HTML")
