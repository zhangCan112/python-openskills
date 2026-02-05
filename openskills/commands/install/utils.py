"""
Install command utilities
"""

import os
from typing import Any


def get_repo_name(repo_url: str) -> str | None:
    """Extract repo name from a git URL"""
    cleaned = repo_url.replace('.git', '')
    last_part = cleaned.split('/')[-1]
    if not last_part:
        return None
    maybe_repo = last_part.split(':')[-1] if ':' in last_part else last_part
    return maybe_repo or None


def get_directory_size(dir_path: str) -> int:
    """Get directory size in bytes"""
    size = 0
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            size += os.path.getsize(file_path)
    return size


def format_size(bytes: int) -> str:
    """Format bytes to human-readable size"""
    if bytes < 1024:
        return f'{bytes}B'
    if bytes < 1024 * 1024:
        return f'{bytes / 1024:.1f}KB'
    return f'{bytes / (1024 * 1024):.1f}MB'


def print_post_install_hints(is_project: bool) -> None:
    """Print post install hints"""
    import click
    click.echo(f"\n{click.style('Read skill:', dim=True)} {click.style('openskills read <skill-name>', fg='cyan')}")
    if is_project:
        click.echo(f"{click.style('Sync to AGENTS.md:', dim=True)} {click.style('openskills sync', fg='cyan')}")