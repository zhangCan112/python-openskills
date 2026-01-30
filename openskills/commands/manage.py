"""
Interactively manage (remove) installed skills command
"""

import os
import shutil
import sys
from typing import Any
import click

from openskills.utils import find_all_skills, find_skill


def prompt_for_selection(message: str, choices: list[dict[str, Any]]) -> list[str]:
    """Prompt user to select from choices"""
    try:
        from questionary import checkbox as q_checkbox
        result = q_checkbox(message, choices=choices).ask()
        return result if result else []
    except ImportError:
        # Fallback to simple input if questionary not available
        click.echo(message)
        for i, choice in enumerate(choices, 1):
            click.echo(f"  {i}. {choice['name']}")
        
        indices_input = click.prompt("Enter numbers (comma-separated, or 'all')", default='all')
        
        if indices_input.strip().lower() == 'all':
            return [choice['value'] for choice in choices]
        
        try:
            indices = [int(x.strip()) for x in indices_input.split(',')]
            return [choices[i-1]['value'] for i in indices if 1 <= i <= len(choices)]
        except ValueError:
            click.echo(click.style("Invalid input. Selecting all skills.", fg='yellow'))
            return [choice['value'] for choice in choices]


async def manage_skills() -> None:
    """
    Interactively manage (remove) installed skills
    """
    skills = find_all_skills()
    
    if not skills:
        click.echo("No skills installed.")
        return
    
    try:
        # Sort: project first
        sorted_skills = sorted(skills, key=lambda s: (s.location != 'project', s.name))
        
        choices = [
            {
                'name': f"{click.style(skill.name.ljust(25), bold=True)} {click.style('(project)' if skill.location == 'project' else '(global)', fg='blue' if skill.location == 'project' else 'dim')}",
                'value': skill.name,
                'checked': False  # Nothing checked by default
            }
            for skill in sorted_skills
        ]
        
        to_remove = prompt_for_selection('Select skills to remove', choices)
        
        if not to_remove:
            click.echo(click.style("No skills selected for removal.", fg='yellow'))
            return
        
        # Remove selected skills
        for skill_name in to_remove:
            skill = find_skill(skill_name)
            if skill:
                shutil.rmtree(skill.base_dir, ignore_errors=True)
                location = 'project' if os.getcwd() in skill.source else 'global'
                click.echo(click.style(f"✅ Removed: {skill_name} ({location})", fg='green'))
        
        click.echo(click.style(f"\n✅ Removed {len(to_remove)} skill(s)", fg='green'))
    except (EOFError, KeyboardInterrupt):
        click.echo(click.style("\n\nCancelled by user", fg='yellow'))
        sys.exit(0)