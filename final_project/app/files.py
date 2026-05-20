import re
from dataclasses import dataclass
from pathlib import Path

MAX_FILE_SIZE = 5 * 1024 * 1024
FILE_REF_PATTERN = re.compile(r'@::(.+?)::')
MODE_PARAGRAPH = 'paragraph'
MODE_LEN = 'len'


@dataclass
class ChunkOptions:
    mode: str = MODE_PARAGRAPH
    paragraph_count: int = 1
    char_len: int = 150
    auto_advance: bool = False


def read_text_file(path_str: str) -> str:
    path = Path(path_str.strip())
    if not path.is_file():
        raise FileNotFoundError(f'Файл не найден: {path}')
    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        raise ValueError(f'Файл {path} слишком большой ({size} байт). Лимит: {MAX_FILE_SIZE} байт.')
    return path.read_text(encoding='utf-8')


def expand_file_references(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return read_text_file(match.group(1))

    return FILE_REF_PATTERN.sub(replace, text)


def _parse_int_option(part: str) -> int:
    _, value = part.split('=', 1)
    return max(1, int(value))


def _apply_chunk_flag(options: ChunkOptions, part: str) -> None:
    if part == '-y':
        options.auto_advance = True
        return
    if part.startswith('paragraph='):
        options.mode = MODE_PARAGRAPH
        options.paragraph_count = _parse_int_option(part)
        return
    if part in {MODE_PARAGRAPH, '/filechunk'}:
        options.mode = MODE_PARAGRAPH
        return
    if part.startswith('len='):
        options.mode = MODE_LEN
        options.char_len = _parse_int_option(part)


def parse_file_chunk_args(arg_line: str) -> ChunkOptions:
    options = ChunkOptions()
    for part in arg_line.split():
        _apply_chunk_flag(options, part)
    return options


def _split_by_length(text: str, step: int) -> list[str]:
    chunks: list[str] = []
    for index in range(0, len(text), step):
        piece = text[index : index + step]
        if piece:
            chunks.append(piece)
    return chunks


def _split_by_paragraphs(text: str, count: int) -> list[str]:
    paragraphs = [line for line in text.splitlines() if line.strip()]
    if not paragraphs:
        return []
    chunks: list[str] = []
    for index in range(0, len(paragraphs), count):
        end = index + count
        chunks.append('\n'.join(paragraphs[index:end]))
    return chunks


def split_into_chunks(text: str, options: ChunkOptions) -> list[str]:
    if options.mode == MODE_LEN:
        return _split_by_length(text, options.char_len)
    return _split_by_paragraphs(text, options.paragraph_count)
