from collections.abc import Generator
from typing import Any

from app.llm_client import LLMClient


class _FakeDelta:
    def __init__(self, content: str | None) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str | None) -> None:
        self.delta = _FakeDelta(content)


class _FakeChunk:
    def __init__(self, content: str | None) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeCompletionChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeCompletion:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeCompletionChoice(content)]


class _FakeCompletions:
    def __init__(self, content: str, stream_parts: list[str]) -> None:
        self._content = content
        self._stream_parts = stream_parts

    def create(self, **kwargs: Any) -> Any:
        if kwargs.get('stream'):
            return (_FakeChunk(part) for part in self._stream_parts)
        return _FakeCompletion(self._content)


class _FakeChat:
    def __init__(self, content: str, stream_parts: list[str]) -> None:
        self.completions = _FakeCompletions(content, stream_parts)


class _FakeOpenAI:
    def __init__(self, content: str = 'full', stream_parts: list[str] | None = None) -> None:
        self.chat = _FakeChat(content, stream_parts or ['Hel', 'lo'])


def test_send_returns_content(sample_config: Any) -> None:
    client = LLMClient(sample_config)
    client._client = _FakeOpenAI('Ответ модели')
    result = client.send([{'role': 'user', 'content': 'Hi'}])
    assert result == 'Ответ модели'


def test_send_stream_yields_parts(sample_config: Any) -> None:
    client = LLMClient(sample_config)
    client._client = _FakeOpenAI(stream_parts=['A', 'B', 'C'])
    parts = list(client.send_stream([{'role': 'user', 'content': 'Hi'}]))
    assert parts == ['A', 'B', 'C']


def test_send_chunk_builds_messages(sample_config: Any) -> None:
    client = LLMClient(sample_config)
    client._client = _FakeOpenAI('chunk-ok')
    result = client.send_chunk('Summarize', 'text part')
    assert result == 'chunk-ok'


def test_send_stream_chunk(sample_config: Any) -> None:
    client = LLMClient(sample_config)
    client._client = _FakeOpenAI(stream_parts=['x', 'y'])
    parts = list(client.send_stream_chunk('Do', 'chunk'))
    assert ''.join(parts) == 'xy'
