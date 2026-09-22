from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import os

router = Router(name="ai_module")

@router.message(Command("ai", "ask"))
async def ai_query_handler(message: Message):
    """Handles AI text generation requests."""
    prompt = " ".join(message.text.split()[1:])
    if not prompt:
        await message.reply("🤖 <b>AI Assistant</b>\n\nUsage: <code>/ask What is Python?</code>", parse_mode="HTML")
        return

    status_msg = await message.reply("💭 <i>Thinking...</i>", parse_mode="HTML")

    # Clean pluggable stub ready for OpenAI / Gemini API call
    response_text = (
        f"🤖 <b>AI Response:</b>\n\n"
        f"Here is an automated response for: <i>{prompt}</i>\n\n"
        f"<i>(To connect live OpenAI / Google Gemini API, configure OPENAI_API_KEY in .env)</i>"
    )

    await status_msg.edit_text(response_text, parse_mode="HTML")
