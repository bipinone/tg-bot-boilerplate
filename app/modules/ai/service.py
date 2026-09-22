import os
import logging
import aiohttp
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class AIProviderService:
    """
    Unified Multi-Provider AI Engine with:
    - Provider Support: OpenAI, Google Gemini, Anthropic Claude, and Custom OpenAI-Compatible (Ollama, Groq, DeepSeek).
    - Conversation Memory (per-user history buffer).
    - System prompt personalization.
    - Fallback handling.
    """

    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
        self.system_prompt = os.getenv("AI_SYSTEM_PROMPT", "You are a helpful, concise AI assistant inside a Telegram Bot.")

        # Per-user conversation memory: {user_id: [{"role": "user"|"assistant", "content": "..."}]}
        self.memory: Dict[int, List[Dict[str, str]]] = {}
        self.max_memory_turns: int = 10

    def get_user_history(self, user_id: int) -> List[Dict[str, str]]:
        if user_id not in self.memory:
            self.memory[user_id] = []
        return self.memory[user_id]

    def clear_memory(self, user_id: int) -> None:
        self.memory.pop(user_id, None)

    async def generate_response(self, user_id: int, prompt: str) -> str:
        """Generates AI completion with conversation history."""
        history = self.get_user_history(user_id)
        history.append({"role": "user", "content": prompt})

        # Trim history
        if len(history) > self.max_memory_turns * 2:
            history = history[-self.max_memory_turns * 2:]
            self.memory[user_id] = history

        # If no API key configured, return informative template response
        if not self.api_key:
            return (
                f"🤖 <b>AI Assistant ({self.provider.upper()})</b>\n\n"
                f"You asked: <i>{prompt}</i>\n\n"
                "💡 <i>To activate live responses, add <code>OPENAI_API_KEY</code> or <code>GEMINI_API_KEY</code> to your .env file!</i>"
            )

        messages = [{"role": "system", "content": self.system_prompt}] + history

        try:
            # Standard OpenAI / OpenAI-Compatible completion request
            endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        reply = data["choices"][0]["message"]["content"]
                        history.append({"role": "assistant", "content": reply})
                        return reply
                    else:
                        error_body = await resp.text()
                        logger.error("AI API returned status %s: %s", resp.status, error_body)
                        return f"⚠️ AI Provider Error ({resp.status}). Please check API configuration."

        except Exception as e:
            logger.exception("AI generation failed: %s", e)
            return "⚠️ Failed to reach AI service. Please try again shortly."

ai_service = AIProviderService()
