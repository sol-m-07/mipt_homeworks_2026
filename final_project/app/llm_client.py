from collections.abc import Generator

from openai import OpenAI

from app.config import AppConfig


class LLMClient:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_host,
        )

    def send(self, messages: list[dict[str, str]]) -> str:
        response = self._client.chat.completions.create(
            model=self._config.model,
            messages=messages,
            temperature=self._config.temperature,
        )
        content = response.choices[0].message.content
        return content if content is not None else ''

    def send_stream(
        self, messages: list[dict[str, str]]
    ) -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=self._config.model,
            messages=messages,
            temperature=self._config.temperature,
            stream=True,
        )
        for chunk in stream:
            piece = chunk.choices[0].delta.content
            if piece:
                yield piece

    def send_chunk(self, user_prompt: str, chunk_text: str) -> str:
        return self.send(self._chunk_messages(user_prompt, chunk_text))

    def send_stream_chunk(
        self, user_prompt: str, chunk_text: str
    ) -> Generator[str, None, None]:
        yield from self.send_stream(self._chunk_messages(user_prompt, chunk_text))

    def _chunk_messages(
        self, user_prompt: str, chunk_text: str
    ) -> list[dict[str, str]]:
        user_content = f'{user_prompt}\n\n{chunk_text}'
        messages: list[dict[str, str]] = []
        if self._config.system_prompt:
            messages.append({'role': 'system', 'content': self._config.system_prompt})
        messages.append({'role': 'user', 'content': user_content})
        return messages
