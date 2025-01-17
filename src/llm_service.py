from yandex_cloud_ml_sdk import AsyncYCloudML

from settings import get_settings


GENERATE_EMOJI_PROMPT = {
    "role": "system",
    "text": """
Твоя задача: по описанию задачи сгенерировать подходищий по смыслу эмодзи.
Если подходит несколько эмодзи, выбери одно.
НЕ ОТВЕЧАЙ НИЧЕМ, КРОМЕ САМОГО ПОДХОДЯЩЕГО ЭМОДЗИ.
Если ни один эмодзи не подходит по смыслу, отвечай любым нейтральным эмодзи.
""",
}


class LLMService:
    def __init__(self):
        self.model = AsyncYCloudML(
            folder_id=get_settings().YANDEX_CLOUD_FOLDER,
            auth=get_settings().YANDEXGPT_API_KEY,
        ).models.completions("yandexgpt").configure(temperature=0.3)

    async def generate_task_title(self, description: str) -> str:
        messages = [
            None,  # Todo
            {
                "role": "user",
                "text": description,
            },
        ]
        response = await self.model.run(messages)
        return response.alternatives[0].text
    
    async def generate_task_emoji(self, description: str) -> str:
        messages = [
            GENERATE_EMOJI_PROMPT,
            {
                "role": "user",
                "text": description,
            },
        ]
        response = await self.model.run(messages)
        return response.alternatives[0].text


llm_service = LLMService()
