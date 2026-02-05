"""
Install command validators
"""

import os
import sys
from pathlib import Path
import click
from openskills.utils.marketplace_skills import ANTHROPIC_MARKETPLACE_SKILLS


def is_local_path(source: str) -> bool:
    """Check if source is a local path"""
    return (
        source.startswith('/') or
        source.startswith('./') or
        source.startswith('../') or
        source.startswith('~/')
    )


def is_git_url(source: str) -> bool:
    """Check if source is a git URL"""
    return (
        source.startswith('git@') or
        source.startswith('git://') or
        source.startswith('http://') or
        source.startswith('https://') or
        source.endswith('.git')
    )


def is_path_inside(target_path: str, target_dir: str) -> bool:
    """Ensure target path stays within target directory"""
    resolved_target = os.path.abspath(target_path)
    resolved_dir = os.path.abspath(target_dir)
    resolved_dir_sep = resolved_dir if resolved_dir.endswith(os.sep) else resolved_dir + os.sep
    return resolved_target.startswith(resolved_dir_sep)


def expand_path(source: str) -> str:
    """Expand ~ to home directory"""
    if source.startswith('~/'):
        return os.path.join(str(Path.home()), source[2:])
    return os.path.abspath(source)


def warn_if_conflict(skill_name: str, target_path: str, is_project: bool, skip_prompt: bool = False) -> bool:
    """Warn if installing could conflict with marketplace. Returns True if should proceed."""
    # Check if overwriting existing skill
    if os.path.exists(target_path):
        if skip_prompt:
            click.echo(click.style(f"Overwriting: {skill_name}", dim=True))
            return True
        
        if not click.confirm(click.style(f"Skill '{skill_name}' already exists. Overwrite?", fg='yellow'), default=False):
            return False
    
    # Warn about marketplace conflicts (global install only)
    if not is_project and skill_name in ANTHROPIC_MARKETPLACE_SKILLS:
        click.echo(click.style(f"\n⚠️  Warning: '{skill_name}' matches an Anthropic marketplace skill", fg='yellow'))
        click.echo(click.style('   Installing globally may conflict with Claude Code plugins.', dim=True))
        click.echo(click.style('   If you re-enable Claude plugins, this will be overwritten.', dim=True))
        click.echo(click.style('   Recommend: Use --project flag for conflict-free installation.\n', dim=True))
    
    return True