from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_start_keyboard() -> InlineKeyboardMarkup:
    """Returns main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("Features", callback_data="menu_features"),
            InlineKeyboardButton("Help & Commands", callback_data="menu_help")
        ],
        [
            InlineKeyboardButton("Developer", url="https://t.me/BipinOne"),
            InlineKeyboardButton("Community", url="https://t.me/BipinOneChat")
        ],
        [
            InlineKeyboardButton("Source Code (GitHub)", url="https://github.com/bipinone/tg-bot-boilerplate")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Back button to return to main menu."""
    keyboard = [
        [InlineKeyboardButton("« Back to Main Menu", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)
