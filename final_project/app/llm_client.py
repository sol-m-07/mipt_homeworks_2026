from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from app.config import AppConfig


class LLMClient:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_host,
        )

    def send(self, messages: list[ChatCompletionMessageParam]) -> str:
        response = self._client.chat.completions.create(
            model=self._config.model,
            messages=messages,
            temperature=self._config.temperature,
        )
        content = response.choices[0].message.content
        return content or ''

    def send_chunk(self, user_prompt: str, chunk_text: str) -> str:
        return self.send(self._chunk_messages(user_prompt, chunk_text))

    def _chunk_messages(
        self, user_prompt: str, chunk_text: str
    ) -> list[ChatCompletionMessageParam]:
        user_content = f'{user_prompt}\n\n{chunk_text}'
        messages: list[ChatCompletionMessageParam] = []
        if self._config.system_prompt:
            messages.append(
                ChatCompletionSystemMessageParam(
                    role='system',
                    content=self._config.system_prompt,
                )
            )
        messages.append(
            ChatCompletionUserMessageParam(role='user', content=user_content)
        )
        return messages
