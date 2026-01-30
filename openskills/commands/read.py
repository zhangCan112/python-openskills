"""
Read skill to stdout command (for AI agents)
"""

import os
import sys
import click

from openskills.utils import find_skill


def normalize_skill_names(skill_names: str | list[str]) -> list[str]:
    """
    Normalize skill names to a list
    
    Args:
        skill_names: Single skill name or list of skill names
        
    Returns:
        List of skill names
    """
    if isinstance(skill_names, str):
        # Handle comma-separated names
        if ',' in skill_names:
            return [name.strip() for name in skill_names.split(',')]
        return [skill_names]
    return skill_names


def read_skill(skill_names: str | list[str]) -> None:
    """
    Read skill to stdout (for AI agents)
    
    Args:
        skill_names: Single skill name or list of skill names
    """
    names = normalize_skill_names(skill_names)
    
    if not names:
        click.echo('Error: No skill names provided', err=True)
        sys.exit(1)
    
    resolved = []
    missing = []
    
    for name in names:
        skill = find_skill(name)
        if not skill:
            missing.append(name)
            continue
        resolved.append({'name': name, 'skill': skill})
    
    if missing:
        click.echo(f"Error: Skill(s) not found: {', '.join(missing)}", err=True)
        click.echo('\nSearched:', err=True)
        click.echo('  .agent/skills/ (project universal)', err=True)
        click.echo('  ~/.agent/skills/ (global universal)', err=True)
        click.echo('  .claude/skills/ (project)', err=True)
        click.echo('  ~/.claude/skills/ (global)', err=True)
        click.echo('\nInstall skills: openskills install owner/repo', err=True)
        sys.exit(1)
    
    for item in resolved:
        name = item['name']
        skill = item['skill']
        
        with open(skill.path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Output in Claude Code format
        click.echo(f"Reading: {name}")
        click.echo(f"Base directory: {skill.base_dir}")
        click.echo('')
        click.echo(content)
        click.echo('')
        click.echo(f"Skill read: {name}")