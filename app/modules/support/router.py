import logging
from aiogram import Router, F, Bot
from aiogram.enums import ChatType
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from app.config import config
from app.database.session import DatabaseSession
from app.services.logger import TelegramLogService

logger = logging.getLogger(__name__)

router = Router(name="two_way_support_router")

# 1. User -> Admin: Relay user message to their personal Forum Topic
@router.message(F.chat.type == ChatType.PRIVATE, ~F.text.startswith("/"))
async def relay_user_to_admin_topic(
    message: Message,
    bot: Bot,
    db: DatabaseSession,
    tg_logger: TelegramLogService
):
    """
    When user sends any message in private chat, forward it directly to
    their personal dedicated topic in the admin group.
    """
    if not config.support.enabled or not config.logging.chat_id:
        return

    user = message.from_user
    # Ensure user has a dedicated topic
    thread_id = await tg_logger.get_or_create_user_topic(user.id, user.first_name, user.username, db)
    if not thread_id:
        return

    try:
        # Copy the user's message directly into their forum topic
        await message.copy_to(
            chat_id=config.logging.chat_id,
            message_thread_id=thread_id
        )
    except TelegramAPIError as e:
        logger.warning("Failed to relay user %s message to topic #%s: %s", user.id, thread_id, e)

# 2. Admin -> User: Reply inside topic and relay back to user
@router.message(
    F.chat.id == config.logging.chat_id,
    F.message_thread_id != None,
    ~F.text.startswith("/")
)
async def relay_admin_topic_to_user(message: Message, bot: Bot, db: DatabaseSession):
    """
    When an admin replies inside a user's dedicated forum topic,
    relay that message back to the user's private Telegram chat!
    """
    if not config.support.enabled:
        return

    # Ignore bot's own automated messages
    if message.from_user and message.from_user.is_bot:
        return

    topic_id = message.message_thread_id
    user_record = await db.get_user_by_topic(topic_id)

    if not user_record:
        # Not a user-managed topic
        return

    target_user_id = user_record["user_id"]

    try:
        # Send admin's message back to the user
        await message.copy_to(chat_id=target_user_id)
        # React or mark message as delivered
        try:
            await message.react([{"type": "emoji", "emoji": "👍"}])
        except Exception:
            pass
    except TelegramForbiddenError:
        await message.reply(
            "⚠️ <b>Delivery Failed:</b> The user has blocked the bot or deleted their account.",
            parse_mode="HTML"
        )
    except TelegramAPIError as e:
        logger.warning("Failed to send admin reply to user %s: %s", target_user_id, e)
        await message.reply(f"⚠️ <b>Delivery Error:</b> {e}", parse_mode="HTML")
