from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def update_user_list_message_id(
        session: AsyncSession,
        user: User | None,
        user_id: int,
        message_id: int
) -> None:
    """Updates or creates a user's list message ID in the database.

    Args:
        session (AsyncSession): The database session
        user (User | None): The user object if it exists, None otherwise
        user_id (int): The Telegram user ID
        message_id (int): The message ID to store

    The function will:
    - Create a new user if one doesn't exist
    - Update the existing user's list_message_id if it differs
    - Do nothing if the message ID is the same as the current one
    """
    if not user:
        user = User(telegram_id=user_id, list_message_id=message_id+1)
        session.add(user)
        await session.commit()
    elif user.list_message_id != message_id:
        user.list_message_id = message_id
        await session.commit()
