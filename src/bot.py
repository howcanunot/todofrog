from enum import Enum
from importlib.resources import files
import os
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.database import get_session
from src.settings import get_settings
from src.models.user import User
from src.utils import delete_message
from src.messages import START_MESSAGE, TASK_REPLY_MESSAGE
from src.user_manager import update_user_list_message_id
from src.task_manager import TaskManager
from src.logger import logger


TASK_LIST_IMAGE: bytes = Path(files("assets").joinpath("tasks_list.jpg")).read_bytes()

class CreateTaskConversation(Enum):
    FAILED = 0
    DESCRIPTION = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[['📋 Список Задач', '✏️ Создать Задачу']],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    await update.message.reply_text(START_MESSAGE, reply_markup=keyboard)
    await update.message.reply_text("🐸")


async def create_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.debug(f"Creating task for user {update.effective_user.id}")
    async with get_session() as session:
        task_manager = TaskManager(session)
        if await task_manager.get_task_count(update.message.from_user.id) >= 5:
            await update.message.reply_text("Кажется, у тебя накопилось слишком много задач")
            return CreateTaskConversation.FAILED
        else:
            await update.message.reply_text("Напиши описание для своей задачи")
            return CreateTaskConversation.DESCRIPTION
        

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Создание задачи отменено")
    return ConversationHandler.END


async def silent_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Silent cancel")
    return ConversationHandler.END


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with get_session() as session:
        logger.debug(f"Creating task for user %d", update.message.from_user.id)
        task_manager = TaskManager(session)
        await task_manager.create_task(
            user_id=update.message.from_user.id,
            username=update.message.from_user.username,
            description=update.message.text,
        )

        logger.debug(f"Successfully created task for user {update.message.from_user.id}")
        await update.message.reply_text("Задача создана! 👋")
        await get_list_tasks(update, context, disable_delete=True, message_id_offset=1)

        return ConversationHandler.END
    

async def get_list_tasks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    disable_delete: bool = False,
    message_id_offset: int = 0,
) -> None:
    user_id = update.effective_user.id
    message_id = update.effective_message.message_id
    async with get_session() as session:
        task_manager = TaskManager(session)
        tasks = await task_manager.get_pending_user_tasks(user_id)
        
        if not tasks:
            await update.message.reply_text("You don't have any tasks yet!")
            return
        
        logger.debug("Found %d for user %d", len(tasks), user_id)

        keyboard = []
        for task in tasks:
            keyboard.append([InlineKeyboardButton(task.emoji + " " + task.description, callback_data=str(task.id))])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_photo(
            update.effective_chat.id,
            TASK_LIST_IMAGE,
            reply_markup=reply_markup
        )
        
        if not disable_delete:
            await delete_message(update, context, message_id)

        user = await session.get(User, user_id)
        if user and user.list_message_id and user.list_message_id != message_id:
            logger.debug("Deleting last list message %d for user %d", user.list_message_id, user_id)
            await delete_message(update, context, user.list_message_id)

        # +1 because we delete the message after user sending
        # and may add more if command called from another command
        # in this case message id will be previous bot message
        await update_user_list_message_id(session, user, user_id, message_id + message_id_offset + 1)


async def task_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    task_id = int(query.data)
    logger.debug("Pressed task button for task %d", task_id)

    keyboard = [
        [
            InlineKeyboardButton("✅ Готово!", callback_data=f"complete_{task_id}"),
            InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{task_id}"),
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_list")],
    ]

    async with get_session() as session:
        task = await TaskManager(session).get_task(task_id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TASK_REPLY_MESSAGE.format(description=task.description),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    await delete_message(update, context, query.message.message_id)


async def back_to_list_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await get_list_tasks(update, context)


async def change_task_status_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    action, task_id = query.data.split("_")

    async with get_session() as session:
        task_manager = TaskManager(session)
        await task_manager.change_task_status(int(task_id), action)

    await query.answer("Задача выполнена, так держать!")
    await back_to_list_button_callback(update, context)


def start_bot():
    app = Application.builder().token(get_settings().bot_token) \
        .get_updates_read_timeout(10.0) \
        .get_updates_write_timeout(10.0) \
        .get_updates_pool_timeout(30.0) \
        .get_updates_connection_pool_size(50) \
        .concurrent_updates(5) \
        .build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('create_task', create_task),
            MessageHandler(filters.Regex(r"^✏️ Создать Задачу$"), create_task),
        ],
        states={
            CreateTaskConversation.DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, description)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
        ],
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('list_tasks', get_list_tasks))

    app.add_handler(MessageHandler(filters.Regex(r"^📋 Список Задач$"), get_list_tasks))

    app.add_handler(CallbackQueryHandler(task_button_callback, pattern="^[0-9]+$"))
    app.add_handler(CallbackQueryHandler(back_to_list_button_callback, pattern="^back_to_list$"))
    app.add_handler(CallbackQueryHandler(change_task_status_button_callback, pattern="^(complete|delete)_[0-9]+$"))

    app.add_handler(conv_handler)

    if not get_settings().dev_mode or get_settings().use_webhook:
        port = os.environ.get("PORT", 8080)
        logger.info("Running bot with webhook on port %s...", port)
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook",
            webhook_url=get_settings().webhook_url,
            drop_pending_updates=False,
        )
    else:
        logger.info("Running bot with long polling...")
        app.run_polling(
            drop_pending_updates=True,
        )
