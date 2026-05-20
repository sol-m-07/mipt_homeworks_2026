from pathlib import Path

import pytest

from app.files import (
    ChunkOptions,
    expand_file_references,
    parse_file_chunk_args,
    read_text_file,
    split_into_chunks,
)


def test_expand_file_reference(tmp_path: Path) -> None:
    file_path = tmp_path / 'code.py'
    file_path.write_text('print(1)', encoding='utf-8')
    text = f'Ошибка? @::{file_path}::'
    result = expand_file_references(text)
    assert result == 'Ошибка? print(1)'


def test_read_file_too_large(tmp_path: Path) -> None:
    file_path = tmp_path / 'big.txt'
    file_path.write_bytes(b'x' * (5 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match='слишком большой'):
        read_text_file(str(file_path))


def test_read_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        read_text_file('/no/such/file.txt')


def test_parse_file_chunk_args() -> None:
    options = parse_file_chunk_args('paragraph=3 -y')
    assert options.paragraph_count == 3
    assert options.auto_advance is True
    assert options.mode == 'paragraph'

    options_len = parse_file_chunk_args('len=10')
    assert options_len.mode == 'len'
    assert options_len.char_len == 10


def test_split_by_paragraphs() -> None:
    text = 'line1\nline2\n\nline3'
    chunks = split_into_chunks(text, ChunkOptions(paragraph_count=2))
    assert len(chunks) == 2
    assert chunks[0] == 'line1\nline2'


def test_split_by_length() -> None:
    text = 'abcdefghij'
    chunks = split_into_chunks(
        text,
        ChunkOptions(mode='len', char_len=4),
    )
    assert chunks == ['abcd', 'efgh', 'ij']
