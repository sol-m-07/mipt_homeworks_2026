import sys
from pathlib import Path

import pytest
import yaml

from app.config import build_config, load_config


def test_build_config_from_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('API_KEY', raising=False)
    data = {
        'api_key': 'key',
        'api_host': 'http://localhost:11434/v1',
        'limit_message': 10,
        'limit_chars': 200,
        'temperature': 0.3,
    }
    config = build_config(data)
    assert config.api_key == 'key'
    assert config.limit_message == 10
    assert config.temperature == 0.3


def test_env_overrides_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('API_KEY', 'from-env')
    monkeypatch.setenv('API_HOST', 'http://env-host/v1')
    monkeypatch.setenv('LIMIT_MESSAGE', '7')
    monkeypatch.setenv('LIMIT_CHARS', '300')
    monkeypatch.setenv('TEMPERATURE', '0.9')

    config = build_config({
        'api_key': 'from-yaml',
        'api_host': 'http://yaml/v1',
        'limit_message': 1,
        'limit_chars': 1,
        'temperature': 0.1,
    })
    assert config.api_key == 'from-env'
    assert config.api_host == 'http://env-host/v1'
    assert config.limit_message == 7


def test_invalid_temperature_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('API_KEY', raising=False)
    with pytest.raises(SystemExit):
        build_config({
            'api_key': 'k',
            'api_host': 'http://localhost/v1',
            'limit_message': 1,
            'limit_chars': 1,
            'temperature': 2,
        })


def test_missing_fields_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('API_KEY', raising=False)
    with pytest.raises(SystemExit):
        build_config({'api_key': 'only-key'})


def test_load_config_from_yaml_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('API_KEY', raising=False)
    config_dir = Path('config')
    config_dir.mkdir()
    config_data = {
        'api_key': 'file-key',
        'api_host': 'http://localhost:11434/v1',
        'limit_message': 5,
        'limit_chars': 50,
        'temperature': 0.2,
        'system_prompt': 'Test prompt',
    }
    (config_dir / 'config.yaml').write_text(
        yaml.dump(config_data),
        encoding='utf-8',
    )
    config = load_config()
    assert config.api_key == 'file-key'
    assert config.system_prompt == 'Test prompt'


def test_load_config_exits_without_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    for name in ('API_KEY', 'API_HOST', 'LIMIT_MESSAGE', 'LIMIT_CHARS', 'TEMPERATURE'):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(SystemExit):
        load_config()
