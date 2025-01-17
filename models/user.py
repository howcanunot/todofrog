from datetime import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime, text

class User(SQLModel, table=True):
    __tablename__ = "users"

    telegram_id: int = Field(default=None, primary_key=True)
    list_message_id: int = Field(nullable=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP")
        )
    )
