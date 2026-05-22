import os
import sys


def clear_screen() -> None:
    if os.name == 'nt':
        os.system('cls')
    else:
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()


def print_assistant(text: str) -> None:
    print(text)


def print_system(text: str) -> None:
    print(text)


def print_error(text: str) -> None:
    print(text, file=sys.stderr)


def prompt_line(label: str = '') -> str:
    if label:
        print(label)
    return input('>>> ').strip()
