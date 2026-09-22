import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Logs the error and notifies admin if critical."""
    logger.error("Exception while handling an update: %s", context.error)

    # Format traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    logger.debug("Traceback:\n%s", tb_string)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An unexpected error occurred while processing your request. Please try again later."
            )
        except Exception:
            pass
