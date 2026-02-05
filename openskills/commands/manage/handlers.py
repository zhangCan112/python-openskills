"""
Manage command handlers
"""

import os
import shutil
import sys
from openskills.utils import find_all_skills, find_skill
from openskills.commands.manage.prompts import prompt_for_selection


def manage_skills() -> None:
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