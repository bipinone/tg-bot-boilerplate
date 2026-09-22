from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.modules.ai.service import ai_service

router = Router(name="ai_module")

@router.message(Command("ai", "ask"))
async def ai_query_handler(message: Message):
    """Handles AI queries with per-user conversation memory."""
    prompt = " ".join(message.text.split()[1:])
    if not prompt:
        await message.reply(
            "🤖 <b>AI Assistant</b>\n\n"
            "• Ask anything: <code>/ask What is an async event loop?</code>\n"
            "• Clear memory: <code>/clear_ai</code>\n"
            "• Provider status: <code>/ai_model</code>",
            parse_mode="HTML"
        )
        return

    status_msg = await message.reply("💭 <i>Generating response...</i>", parse_mode="HTML")
    response_text = await ai_service.generate_response(user_id=message.from_user.id, prompt=prompt)

    try:
        await status_msg.edit_text(response_text, parse_mode="HTML")
    except Exception:
        # Fallback to plain text if HTML formatting fails
        await status_msg.edit_text(response_text)

@router.message(Command("clear_ai", "reset_ai"))
async def clear_ai_memory_handler(message: Message):
    """Resets conversation history for user."""
    ai_service.clear_memory(message.from_user.id)
    await message.reply("🧹 AI conversation memory has been cleared!", parse_mode="HTML")

@router.message(Command("ai_model"))
async def ai_model_info_handler(message: Message):
    """Displays active AI provider and model."""
    info = (
        "🤖 <b>AI Provider Configuration:</b>\n\n"
        f"• <b>Provider:</b> <code>{ai_service.provider.upper()}</code>\n"
        f"• <b>Model:</b> <code>{ai_service.model}</code>\n"
        f"• <b>Endpoint:</b> <code>{ai_service.base_url}</code>\n"
        f"• <b>Memory Window:</b> <code>{ai_service.max_memory_turns} turns</code>"
    )
    await message.reply(info, parse_mode="HTML")
