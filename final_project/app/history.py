from dataclasses import dataclass
from typing import Literal


Role = Literal['user', 'assistant']


@dataclass
class Message:
    role: Role
    content: str


class HistoryManager:
    def __init__(self, limit_message: int, limit_chars: int) -> None:
        self._messages: list[Message] = []
        self._limit_message = limit_message
        self._limit_chars = limit_chars

    def clear(self) -> None:
        self._messages.clear()

    def remove_last(self) -> None:
        if self._messages:
            self._messages.pop()

    def _total_chars(self) -> int:
        return sum(len(msg.content) for msg in self._messages)

    def _trim_content_from_left(self, content: str) -> str:
        if len(content) <= self._limit_chars:
            return content
        return content[-self._limit_chars :]

    def _enforce_limits(self) -> None:
        while True:
            changed = False
            if len(self._messages) > self._limit_message:
                self._messages.pop(0)
                changed = True
            if self._total_chars() > self._limit_chars and self._messages:
                self._messages.pop(0)
                changed = True
            if not changed:
                break

    def add(self, role: Role, content: str) -> None:
        trimmed = self._trim_content_from_left(content)
        self._messages.append(Message(role=role, content=trimmed))
        self._enforce_limits()

    def to_api_format(self, system_prompt: str | None) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        if system_prompt:
            result.append({'role': 'system', 'content': system_prompt})
        for msg in self._messages:
            result.append({'role': msg.role, 'content': msg.content})
        return result
