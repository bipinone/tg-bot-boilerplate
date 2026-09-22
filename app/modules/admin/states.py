# TeleCore Telegram Bot Framework - Admin FSM States
# Author: bipinone (https://github.com/bipinone)
# Repository: https://github.com/bipinone/tg-bot-boilerplate

from aiogram.fsm.state import State, StatesGroup

class AdminLogState(StatesGroup):
    waiting_for_chat = State()
