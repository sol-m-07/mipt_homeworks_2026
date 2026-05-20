import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_CANDIDATES = (
    Path('config/config.yaml'),
    Path('config.yaml'),
)

ENV_API_KEY = 'API_KEY'
ENV_API_HOST = 'API_HOST'
ENV_LIMIT_MESSAGE = 'LIMIT_MESSAGE'
ENV_LIMIT_CHARS = 'LIMIT_CHARS'
ENV_TEMPERATURE = 'TEMPERATURE'
ENV_MODEL = 'MODEL'


@dataclass
class AppConfig:
    api_key: str
    api_host: str
    limit_message: int
    limit_chars: int
    temperature: float
    model: str = 'gpt-3.5-turbo'
    system_prompt: str | None = None


def _has_env_config() -> bool:
    return any(
        os.environ.get(name)
        for name in (
            ENV_API_KEY,
            ENV_API_HOST,
            ENV_LIMIT_MESSAGE,
            ENV_LIMIT_CHARS,
            ENV_TEMPERATURE,
            ENV_MODEL,
        )
    )


def _find_config_path(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        return explicit if explicit.is_file() else None
    for candidate in CONFIG_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data if isinstance(data, dict) else {}


def _parse_int(value: str | int | None, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    return int(str(value).strip())


def _parse_float(value: str | float | None, name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).strip())


def _missing_required_fields(
    api_key: object,
    api_host: object,
    limit_message: int | None,
    limit_chars: int | None,
    temperature: float | None,
) -> list[str]:
    missing: list[str] = []
    if not api_key:
        missing.append('api_key / API_KEY')
    if not api_host:
        missing.append('api_host / API_HOST')
    if limit_message is None:
        missing.append('limit_message / LIMIT_MESSAGE')
    if limit_chars is None:
        missing.append('limit_chars / LIMIT_CHARS')
    if temperature is None:
        missing.append('temperature / TEMPERATURE')
    return missing


def _merge_config(yaml_data: dict[str, Any]) -> AppConfig:
    api_key = os.environ.get(ENV_API_KEY) or yaml_data.get('api_key')
    api_host = os.environ.get(ENV_API_HOST) or yaml_data.get('api_host')
    limit_message = _parse_int(
        os.environ.get(ENV_LIMIT_MESSAGE) or yaml_data.get('limit_message'),
        ENV_LIMIT_MESSAGE,
    )
    limit_chars = _parse_int(
        os.environ.get(ENV_LIMIT_CHARS) or yaml_data.get('limit_chars'),
        ENV_LIMIT_CHARS,
    )
    temperature = _parse_float(
        os.environ.get(ENV_TEMPERATURE) or yaml_data.get('temperature'),
        ENV_TEMPERATURE,
    )
    model = os.environ.get(ENV_MODEL) or yaml_data.get('model') or 'gpt-3.5-turbo'
    system_prompt = yaml_data.get('system_prompt')
    if system_prompt is not None:
        system_prompt = str(system_prompt)

    missing = _missing_required_fields(api_key, api_host, limit_message, limit_chars, temperature)
    if missing:
        print(
            '?? ?????? ???????????? ????????? ????????????:\n'
            + '\n'.join(f'  - {item}' for item in missing)
        )
        sys.exit(1)

    if limit_message is None or limit_chars is None or temperature is None:
        sys.exit(1)

    if not 0 <= temperature <= 1:
        print('temperature ?????? ???? ? ????????? ?? 0 ?? 1.')
        sys.exit(1)

    return AppConfig(
        api_key=str(api_key),
        api_host=str(api_host).rstrip('/'),
        limit_message=limit_message,
        limit_chars=limit_chars,
        temperature=temperature,
        model=str(model),
        system_prompt=system_prompt,
    )


def build_config(yaml_data: dict[str, Any] | None = None) -> AppConfig:
    return _merge_config(yaml_data or {})


def load_config(config_path: Path | None = None) -> AppConfig:
    path = _find_config_path(config_path)
    has_yaml = path is not None
    has_env = _has_env_config()

    if not has_yaml and not has_env:
        print(
            '???????????? ?? ???????.\n'
            '???????? config/config.yaml (??. config/config.yaml.example) '
            '??? ??????? ?????????? ?????????.'
        )
        sys.exit(1)

    yaml_data: dict[str, Any] = _load_yaml(path) if path else {}
    return build_config(yaml_data)
