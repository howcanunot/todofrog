from enum import Enum as EnumType
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Enum, DateTime, Text, text


class TaskStatus(EnumType):
    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(nullable=False)
    username: str = Field(max_length=255, nullable=False)
    description: str = Field(sa_column=Column(Text, nullable=False))
    emoji: str = Field(max_length=8, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP")
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP")
        )
    )
    status: TaskStatus = Field(
        sa_column=Column(
            Enum(TaskStatus),
            nullable=False,
            default=TaskStatus.PENDING
        )
    )
