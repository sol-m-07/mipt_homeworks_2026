from app.history import HistoryManager


def test_add_and_api_format() -> None:
    history = HistoryManager(limit_message=10, limit_chars=500)
    history.add('user', 'Привет')
    history.add('assistant', 'Ответ')

    messages = history.to_api_format('System prompt')
    assert messages[0] == {'role': 'system', 'content': 'System prompt'}
    assert messages[1]['role'] == 'user'
    assert messages[2]['role'] == 'assistant'


def test_limit_message_trims_oldest() -> None:
    history = HistoryManager(limit_message=2, limit_chars=10_000)
    history.add('user', '1')
    history.add('assistant', '2')
    history.add('user', '3')

    messages = history.to_api_format(None)
    assert [item['content'] for item in messages] == ['2', '3']
    assert [item['role'] for item in messages] == ['assistant', 'user']


def test_limit_chars_trims_oldest() -> None:
    history = HistoryManager(limit_message=20, limit_chars=5)
    history.add('user', '12345')
    history.add('assistant', '67890')

    messages = history.to_api_format(None)
    assert len(messages) == 1
    assert messages[0]['content'] == '67890'


def test_long_message_trimmed_from_left() -> None:
    history = HistoryManager(limit_message=10, limit_chars=4)
    history.add('user', 'abcdef')

    messages = history.to_api_format(None)
    assert messages[0]['content'] == 'cdef'


def test_clear_and_remove_last() -> None:
    history = HistoryManager(limit_message=5, limit_chars=100)
    history.add('user', 'x')
    history.remove_last()
    assert history.to_api_format(None) == []

    history.add('user', 'y')
    history.clear()
    assert history.to_api_format(None) == []
