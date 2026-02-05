"""
Read skill command handlers
"""

import click
from openskills.commands.read.validators import (
    normalize_skill_names,
    validate_and_resolve_skills,
    print_missing_skills_error
)


def read_skill(skill_names: str | list[str]) -> None:
    """
    Read skill to stdout (for AI agents)
    
    Args:
        skill_names: Single skill name or list of skill names
    """
    names = normalize_skill_names(skill_names)
    
    if not names:
        click.echo('Error: No skill names provided', err=True)
        import sys
        sys.exit(1)
    
    resolved, missing = validate_and_resolve_skills(names)
    
    if missing:
        print_missing_skills_error(missing)
    
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