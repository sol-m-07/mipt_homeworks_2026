import io
from collections.abc import Generator

from app.display import print_assistant_stream


def test_print_assistant_stream_collects_text() -> None:
    def chunks() -> Generator[str, None, None]:
        yield 'Hello'
        yield ' '
        yield 'world'

    buffer = io.StringIO()
    result = print_assistant_stream(chunks(), write=buffer.write)
    assert result == 'Hello world'
    assert buffer.getvalue() == 'Hello world'
