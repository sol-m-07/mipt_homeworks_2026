import pytest

from app.config import AppConfig


@pytest.fixture
def sample_config() -> AppConfig:
    return AppConfig(
        api_key='test-key',
        api_host='http://localhost:11434/v1',
        limit_message=5,
        limit_chars=100,
        temperature=0.5,
        model='test-model',
        system_prompt='You are a test assistant.',
    )
