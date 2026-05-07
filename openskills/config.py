import os
from pathlib import Path

import yaml


CONFIG_FILE_NAME = "market_sources.yaml"


def get_config_file_path() -> str | None:
    cwd = Path.cwd()
    config_path = cwd / CONFIG_FILE_NAME
    if config_path.exists():
        return str(config_path)

    current = cwd
    for _ in range(5):
        parent = current.parent
        if parent == current:
            break
        config_path = parent / CONFIG_FILE_NAME
        if config_path.exists():
            return str(config_path)
        current = parent

    home_config = Path.home() / CONFIG_FILE_NAME
    if home_config.exists():
        return str(home_config)

    return None


def load_config() -> dict:
    config_file = get_config_file_path()

    if not config_file or not os.path.exists(config_file):
        return {'sources': []}

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        return config
    except Exception:
        return {'sources': []}
