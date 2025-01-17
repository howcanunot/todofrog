from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.task import Task, TaskStatus
from database import get_session
from src.llm_service import llm_service


MAX_DESCRIPTION_LENGTH = 35

class TaskManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_user_tasks(self, user_id: int):
        tasks = await self.session.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.status == TaskStatus.PENDING)
        )
        return tasks

    async def create_task(self, user_id: int, username: str, description: str) -> None:
        emoji = await llm_service.generate_task_emoji(description)
        new_task = Task(
            user_id=user_id,
            username=username,
            description=description,
            emoji=emoji,
        )
        self.session.add(new_task)
        await self.session.commit()

    async def get_pending_user_tasks(self, user_id: int) -> list[Task]:
        tasks = await self._get_user_tasks(user_id)
        return tasks.scalars().all()

    async def get_task_count(self, user_id: int) -> int:
        tasks = await self._get_user_tasks(user_id)
        return len(tasks.all())

    async def get_task(self, task_id: int) -> Task:
        return await self.session.get(Task, task_id)
    
    async def change_task_status(self, task_id: int, action: str) -> None:
        task = await self.get_task(task_id)
        if action == "complete":
            task.status = TaskStatus.COMPLETED
        elif action == "delete":
            await self.session.delete(task)
        await self.session.commit()
