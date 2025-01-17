from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.logger import logger


async def send_or_edit_message(
    update: Update,
    text: str,
    context: ContextTypes.DEFAULT_TYPE | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str = "MarkdownV2",
) -> None:
    """Send new message or edit existing one based on update type"""
    kwargs = {
        "text": text,
        "reply_markup": reply_markup,
        "parse_mode": parse_mode,
    }
    if update.callback_query:
        await update.callback_query.edit_message_text(**kwargs)
    else:
        if context:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
            )
        else:
            await update.message.reply_text(**kwargs)


async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int) -> None:
    """Deletes the message if it exists"""
    try:
        # if update.callback_query and update.callback_query.message.message_id == message_id:
        #     message = update.callback_query.message
        #     if message.from_user.id != context.bot.id:
        #         logging.debug("Skipping deletion of user message %d", message_id)
        #         return
        logger.debug("Deleting message %d for user %d", message_id, update.effective_user.id)
        await context.bot.delete_message(update.effective_chat.id, message_id)
        logger.debug("Successfully deleted message %d", message_id)
    except Exception as e:
        logger.error("Failed to delete message %d: %s", message_id, e)
