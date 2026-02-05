"""
List skills command handlers
"""

import click
from openskills.utils import find_all_skills


def list_skills() -> None:
    """
    List all installed skills
    """
    click.echo(click.style('Available Skills:\n', bold=True))
    
    skills = find_all_skills()
    
    if not skills:
        _display_empty_state()
        return
    
    # Sort: project skills first, then global, alphabetically within each
    sorted_skills = sorted(skills, key=lambda s: (s.location != 'project', s.name))
    
    # Display with inline location labels
    for skill in sorted_skills:
        if skill.location == 'project':
            location_label = click.style('(project)', fg='blue')
        else:
            location_label = click.style('(global)', dim=True)
        
        click.echo(f"  {click.style(skill.name.ljust(25), bold=True)} {location_label}")
        click.echo(f"    {click.style(skill.description, dim=True)}\n")
    
    # Summary
    _display_summary(skills)


def _display_empty_state() -> None:
    """Display message when no skills are installed"""
    click.echo('No skills installed.\n')
    click.echo('Install skills:')
    click.echo(f"  {click.style('openskills install anthropics/skills', fg='cyan')}         {click.style('# Project (default)', dim=True)}")
    click.echo(f"  {click.style('openskills install owner/skill --global', fg='cyan')}     {click.style('# Global (advanced)', dim=True)}")


def _display_summary(skills: list) -> None:
    """Display summary statistics of installed skills"""
    project_count = len([s for s in skills if s.location == 'project'])
    global_count = len([s for s in skills if s.location == 'global'])
    
    click.echo(click.style(f'Summary: {project_count} project, {global_count} global ({len(skills)} total)', dim=True))