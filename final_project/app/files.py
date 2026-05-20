import re
from dataclasses import dataclass
from pathlib import Path

MAX_FILE_SIZE = 5 * 1024 * 1024
FILE_REF_PATTERN = re.compile(r'@::(.+?)::')


@dataclass
class ChunkOptions:
    mode: str = 'paragraph'
    paragraph_count: int = 1
    char_len: int = 150
    auto_advance: bool = False


def read_text_file(path_str: str) -> str:
    path = Path(path_str.strip())
    if not path.is_file():
        raise FileNotFoundError(f'Файл не найден: {path}')
    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        raise ValueError(
            f'Файл {path} слишком большой ({size} байт). Лимит: {MAX_FILE_SIZE} байт.'
        )
    return path.read_text(encoding='utf-8')


def expand_file_references(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return read_text_file(match.group(1))

    return FILE_REF_PATTERN.sub(replace, text)


def parse_file_chunk_args(arg_line: str) -> ChunkOptions:
    options = ChunkOptions()
    for part in arg_line.split():
        if part == '-y':
            options.auto_advance = True
        elif part.startswith('paragraph='):
            options.mode = 'paragraph'
            options.paragraph_count = max(1, int(part.split('=', 1)[1]))
        elif part == 'paragraph' or part == '/filechunk':
            options.mode = 'paragraph'
        elif part.startswith('len='):
            options.mode = 'len'
            options.char_len = max(1, int(part.split('=', 1)[1]))
    return options


def split_into_chunks(text: str, options: ChunkOptions) -> list[str]:
    if options.mode == 'len':
        chunks: list[str] = []
        step = options.char_len
        for index in range(0, len(text), step):
            piece = text[index : index + step]
            if piece:
                chunks.append(piece)
        return chunks

    paragraphs = [line for line in text.splitlines() if line.strip()]
    if not paragraphs:
        return []
    count = options.paragraph_count
    chunks = []
    for index in range(0, len(paragraphs), count):
        chunks.append('\n'.join(paragraphs[index : index + count]))
    return chunks
