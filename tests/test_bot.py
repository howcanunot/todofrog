import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot import description, start, create_task, get_list_tasks, task_button_callback
from src.bot import CreateTaskConversation
from src.messages import START_MESSAGE


@pytest.fixture(autouse=True)
def mock_settings(mocker):
    mock_settings = MagicMock()
    mock_settings.BOT_TOKEN = "test_token"
    mock_settings.DB_URL = "test_db_url"
    mock_settings.YANDEXGPT_API_KEY = "test_api_key"
    mock_settings.YANDEX_CLOUD_FOLDER = "test_folder"
    mock_settings.SSL_CERT_BASE64 = "test_cert"
    mock_settings.DEV_MODE = True
    
    mocker.patch('src.bot.get_settings', return_value=mock_settings)


@pytest.fixture
def update():
    update = MagicMock(spec=Update)
    update.effective_user.id = 12345
    update.message = AsyncMock()
    update.effective_message = AsyncMock()
    update.effective_chat = AsyncMock()
    update.message.from_user.id = 12345
    return update


@pytest.fixture
def context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_start_command(update, context):
    await start(update, context)
    
    # Verify that reply_text was called twice (for message and emoji)
    assert update.message.reply_text.call_count == 2
    
    # Verify the first call had the START_MESSAGE
    first_call_args = update.message.reply_text.call_args_list[0]
    assert first_call_args.args[0] == START_MESSAGE


@pytest.mark.asyncio
async def test_create_task_command_limit_reached(update, context, mocker):
    # Mock the session and TaskManager
    session_mock = AsyncMock()
    task_manager_mock = AsyncMock()
    task_manager_mock.get_task_count.return_value = 5  # Simulate reaching task limit
    
    mocker.patch('src.bot.get_session', return_value=AsyncMock(__aenter__=AsyncMock(return_value=session_mock)))
    mocker.patch('src.bot.TaskManager', return_value=task_manager_mock)

    result = await create_task(update, context)
    
    # Verify the result and message
    assert result == CreateTaskConversation.FAILED
    update.message.reply_text.assert_called_once_with("Кажется, у тебя накопилось слишком много задач")


@pytest.mark.asyncio
async def test_get_list_tasks_empty(update, context, mocker):
    # Mock the session and TaskManager
    session_mock = AsyncMock()
    task_manager_mock = AsyncMock()
    task_manager_mock.get_pending_user_tasks.return_value = []  # Return empty task list
    
    mocker.patch('src.bot.get_session', return_value=AsyncMock(__aenter__=AsyncMock(return_value=session_mock)))
    mocker.patch('src.bot.TaskManager', return_value=task_manager_mock)

    await get_list_tasks(update, context)
    
    # Verify the "no tasks" message was sent
    update.message.reply_text.assert_called_once_with("You don't have any tasks yet!")


@pytest.mark.asyncio
async def test_create_task_success(update, context, mocker):
    # Mock the session and TaskManager
    session_mock = AsyncMock()
    task_manager_mock = AsyncMock()
    tasks_list_mock = AsyncMock()
    task_manager_mock.get_task_count.return_value = 2  # Below limit
    
    mocker.patch('src.bot.get_session', return_value=AsyncMock(__aenter__=AsyncMock(return_value=session_mock)))
    mocker.patch('src.bot.TaskManager', return_value=task_manager_mock)
    mocker.patch('src.bot.get_list_tasks', return_value=tasks_list_mock)

    result = await create_task(update, context)
    
    # Verify we moved to description state
    assert result == CreateTaskConversation.DESCRIPTION
    update.message.reply_text.assert_called_once_with("Напиши описание для своей задачи")

    update.message.text = "test_description"
    result = await description(update, context)
    assert result == ConversationHandler.END
    assert update.message.reply_text.call_args_list[-1].args[0] == "Задача создана! 👋"


@pytest.mark.asyncio
async def test_task_button_callback(update, context, mocker):
    # Mock the callback query
    update.callback_query = AsyncMock()
    update.callback_query.data = "123"  # Task ID
    
    # Mock the session and TaskManager
    session_mock = AsyncMock()
    task_manager_mock = AsyncMock()
    task_manager_mock.get_task.return_value = MagicMock(description="Test task")
    
    mocker.patch('src.bot.get_session', return_value=AsyncMock(__aenter__=AsyncMock(return_value=session_mock)))
    mocker.patch('src.bot.TaskManager', return_value=task_manager_mock)

    await task_button_callback(update, context)
    
    # Verify the callback was answered
    update.callback_query.answer.assert_called_once()
    # Verify the message was sent with buttons
    context.bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_delete_last_tasks_list_message(update, context, mocker):
    user_mock = AsyncMock()
    user_mock.list_message_id = 1

    session_mock = AsyncMock()
    session_mock.get.return_value = user_mock
    
    task_manager_mock = AsyncMock()
    
    mocker.patch('src.bot.get_session', return_value=AsyncMock(__aenter__=AsyncMock(return_value=session_mock)))
    mocker.patch('src.bot.TaskManager', return_value=task_manager_mock)

    await get_list_tasks(update, context)
    
    assert context.bot.delete_message.call_count == 2
    assert context.bot.delete_message.call_args_list[1].args[1] == 1


@pytest.mark.asyncio
async def test_delete_last_tasks_list_message_after_task_created(update, context, mocker):
    session_mock = AsyncMock()
    task_manager_mock = AsyncMock()
    update_user_list_message_id_mock = AsyncMock()
    user_mock = AsyncMock()
    
    mocker.patch('src.bot.get_session', return_value=AsyncMock(__aenter__=AsyncMock(return_value=session_mock)))
    mocker.patch('src.bot.TaskManager', return_value=task_manager_mock)
    mocker.patch('src.bot.update_user_list_message_id', update_user_list_message_id_mock)

    update.effective_message.message_id = 1
    session_mock.get.return_value = None

    await get_list_tasks(update, context)
    
    update_user_list_message_id_mock.assert_called_once()

    context.bot.delete_message.assert_called_once()
    # delete message after user write command
    assert update_user_list_message_id_mock.call_args[0][3] == update.effective_message.message_id + 1

    update.effective_message.message_id = 3
    task_manager_mock.get_task_count.return_value = 0

    result = await create_task(update, context)

    assert result == CreateTaskConversation.DESCRIPTION
    assert update.message.reply_text.call_args_list[-1].args[0] == "Напиши описание для своей задачи"

    update.effective_message.message_id = 5
    # set last list message id to user
    user_mock.list_message_id = update.message.effective_id
    session_mock.get.return_value = user_mock

    result = await description(update, context)

    assert result == ConversationHandler.END
    assert update.message.reply_text.call_args_list[-1].args[0] == "Задача создана! 👋"    
    assert update_user_list_message_id_mock.call_args[0][3] == update.effective_message.message_id + 2
    assert context.bot.delete_message.call_args_list[1].args[1] == user_mock.list_message_id
