"""
Read skill command validators
"""

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


def validate_and_resolve_skills(skill_names: list[str]) -> tuple[list[dict[str, any]], list[str]]:
    """
    Validate skill names and resolve to skill objects
    
    Args:
        skill_names: List of skill names to validate
        
    Returns:
        Tuple of (resolved skills list, missing skills list)
    """
    resolved = []
    missing = []
    
    for name in skill_names:
        skill = find_skill(name)
        if not skill:
            missing.append(name)
            continue
        resolved.append({'name': name, 'skill': skill})
    
    return resolved, missing


def print_missing_skills_error(missing: list[str]) -> None:
    """
    Print error message for missing skills and exit
    
    Args:
        missing: List of missing skill names
    """
    click.echo(f"Error: Skill(s) not found: {', '.join(missing)}", err=True)
    click.echo('\nSearched:', err=True)
    click.echo('  .agent/skills/ (project universal)', err=True)
    click.echo('  ~/.agent/skills/ (global universal)', err=True)
    click.echo('  .claude/skills/ (project)', err=True)
    click.echo('  ~/.claude/skills/ (global)', err=True)
    click.echo('\nInstall skills: openskills install owner/repo', err=True)
    sys.exit(1)