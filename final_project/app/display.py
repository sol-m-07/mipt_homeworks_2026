import os
import sys
from collections.abc import Callable, Generator


def clear_screen() -> None:
    if os.name == 'nt':
        os.system('cls')
    else:
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()


def print_assistant(text: str) -> None:
    print(text)


def print_assistant_stream(
    chunks: Generator[str, None, None],
    write: Callable[[str], None] | None = None,
) -> str:
    output = write if write is not None else sys.stdout.write
    full_response = ''
    for chunk in chunks:
        output(chunk)
        if write is None:
            sys.stdout.flush()
        full_response += chunk
    if write is None:
        print()
    return full_response


def print_system(text: str) -> None:
    print(text)


def print_error(text: str) -> None:
    print(text, file=sys.stderr)


def prompt_line(label: str = '') -> str:
    if label:
        print(label)
    return input('>>> ').strip()
