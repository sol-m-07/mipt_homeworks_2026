from collections.abc import Generator
from typing import Any

from app.chat import RESET_COMMAND, STREAM_COMMAND, ChatApp


class _StubLLM:
    def __init__(self) -> None:
        self.last_messages: list[dict[str, str]] = []

    def send(self, messages: list[dict[str, str]]) -> str:
        self.last_messages = messages
        return 'stub-response'

    def send_stream(
        self, messages: list[dict[str, str]]
    ) -> Generator[str, None, None]:
        self.last_messages = messages
        yield 'stream-'
        yield 'part'

    def send_chunk(self, user_prompt: str, chunk_text: str) -> str:
        return f'{user_prompt}:{chunk_text}'

    def send_stream_chunk(
        self, user_prompt: str, chunk_text: str
    ) -> Generator[str, None, None]:
        yield f'{user_prompt}-{chunk_text}'


def test_reset_clears_history(sample_config: Any) -> None:
    app = ChatApp(config=sample_config, client=_StubLLM())
    app._history.add('user', 'test')
    assert app._handle_command(RESET_COMMAND) is True
    assert app._history.to_api_format(None) == []


def test_stream_command_toggles(sample_config: Any) -> None:
    app = ChatApp(config=sample_config, client=_StubLLM())
    assert app._use_stream is False
    app._handle_command(STREAM_COMMAND)
    assert app._use_stream is True
    app._handle_command(STREAM_COMMAND)
    assert app._use_stream is False


def test_process_message_uses_stub(sample_config: Any) -> None:
    app = ChatApp(config=sample_config, client=_StubLLM())
    app._process_chat_message('Привет')
    messages = app._history.to_api_format(sample_config.system_prompt)
    assert messages[-1]['content'] == 'stub-response'


def test_process_message_stream_mode(
    sample_config: Any,
    monkeypatch: Any,
) -> None:
    app = ChatApp(config=sample_config, client=_StubLLM())
    app._use_stream = True

    def fake_stream(
        chunks: Generator[str, None, None],
        write: Any = None,
    ) -> str:
        return ''.join(list(chunks))

    monkeypatch.setattr('app.chat.print_assistant_stream', fake_stream)
    app._process_chat_message('Hi')
    messages = app._history.to_api_format(sample_config.system_prompt)
    assert messages[-1]['content'] == 'stream-part'
