import os
from pathlib import Path


def get_skills_dir(global_install: bool = False) -> str:
    if global_install:
        return os.path.join(str(Path.home()), '.claude/skills')
    return os.path.join(os.getcwd(), '.claude/skills')


def get_search_dirs() -> list[str]:
    return [
        os.path.join(os.getcwd(), '.agent/skills'),
        os.path.join(os.getcwd(), '.claude/skills'),
        os.path.join(str(Path.home()), '.agent/skills'),
        os.path.join(str(Path.home()), '.claude/skills'),
    ]


def get_cache_dir() -> str:
    cache_dir = os.path.join(str(Path.home()), '.openskills', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir
