# TeleCore Telegram Bot Framework
# Author: bipinone (https://github.com/bipinone)
# Repository: https://github.com/bipinone/tg-bot-boilerplate

import logging
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from app.config import config

logger = logging.getLogger(__name__)

async def setup_bot_metadata(bot: Bot) -> None:
    """
    Registers default public bot menu commands, bot description,
    and profile bio with credits to bipinone.
    """
    # 1. Public Menu Commands
    public_commands = [
        BotCommand(command="start", description="🚀 Launch the bot menu"),
        BotCommand(command="help", description="📖 View command manual & guides"),
        BotCommand(command="language", description="🌐 Select language / भाषा चुनें"),
        BotCommand(command="sub", description="💎 Check subscription plan & perks"),
        BotCommand(command="plans", description="⭐ View available Pro/VIP tiers"),
        BotCommand(command="ref", description="👥 Referral link & reward points"),
        BotCommand(command="ask", description="🤖 Chat with AI Assistant"),
        BotCommand(command="ping", description="🏓 Test server response speed"),
        BotCommand(command="about", description="ℹ️ About bot & developer credits")
    ]

    try:
        await bot.set_my_commands(commands=public_commands, scope=BotCommandScopeDefault())
        logger.info("Default public menu commands registered successfully.")
    except Exception as e:
        logger.warning("Failed setting public commands: %s", e)

    # 2. Admin Menu Commands for configured superadmins
    admin_commands = [
        BotCommand(command="start", description="🚀 Main menu"),
        BotCommand(command="panel", description="🎛️ Real-time Admin Control Panel"),
        BotCommand(command="stats", description="📊 Live user & system analytics"),
        BotCommand(command="broadcast", description="📢 Mass announcement engine"),
        BotCommand(command="logs", description="📑 Real-time Logs & Topic setup"),
        BotCommand(command="admins", description="👑 Staff & role directory"),
        BotCommand(command="groups", description="👥 Registered communities"),
        BotCommand(command="export", description="📁 Export users database to CSV"),
        BotCommand(command="help", description="📖 View manual")
    ]

    for admin_id in config.bot.admins:
        try:
            await bot.set_my_commands(
                commands=admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception:
            pass

    # 3. Bot Description ("What can this bot do?" screen before /start)
    full_description = (
        "⚡ Welcome to TeleCore — a production-ready, modular Telegram Bot Framework!\n\n"
        "🚀 Features:\n"
        "• Multi-Language Support (English, Hindi)\n"
        "• SaaS Subscriptions & Entitlements Engine\n"
        "• Multi-Provider AI (OpenAI, Gemini, Anthropic)\n"
        "• High-Speed Flag-Based Mass Broadcasts\n"
        "• Multi-Database Support (SQLite, Postgres, MySQL, Mongo)\n\n"
        "👨‍💻 Created with ❤️ by Bipin (@bipinone)\n"
        "⭐ GitHub: https://github.com/bipinone/tg-bot-boilerplate\n"
        "📢 Channel: @BipinOne\n"
        "💬 Community: @BipinOneChat"
    )

    try:
        await bot.set_my_description(description=full_description)
        logger.info("Bot full description registered successfully.")
    except Exception as e:
        logger.warning("Failed setting bot description: %s", e)

    # 4. Short Description (Profile bio)
    short_description = "Production-ready Telegram Bot Framework crafted with ❤️ by @bipinone. Fast, modular & multi-database."

    try:
        await bot.set_my_short_description(short_description=short_description)
        logger.info("Bot short description registered successfully.")
    except Exception as e:
        logger.warning("Failed setting bot short description: %s", e)
