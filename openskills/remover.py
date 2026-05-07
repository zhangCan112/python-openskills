import os
import shutil
import sys
from pathlib import Path
from typing import Any

import click

from openskills.finder import find_skill, find_all_skills


def _prompt_for_selection(message: str, choices: list[dict[str, Any]]) -> list[str]:
    try:
        from questionary import checkbox as q_checkbox
        result = q_checkbox(message, choices=choices).ask()
        return result if result else []
    except ImportError:
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


def remove_skill(skill_name: str) -> None:
    skill = find_skill(skill_name)

    if not skill:
        click.echo(f"Error: Skill '{skill_name}' not found", err=True)
        sys.exit(1)

    shutil.rmtree(skill.base_dir, ignore_errors=True)

    location = 'global' if str(Path.home()) in skill.source else 'project'
    click.echo(f"✅ Removed: {skill_name}")
    click.echo(f"   From: {location} ({skill.source})")


def manage_skills() -> None:
    skills = find_all_skills()

    if not skills:
        click.echo("No skills installed.")
        return

    try:
        sorted_skills = sorted(skills, key=lambda s: (s.location != 'project', s.name))

        choices = [
            {
                'name': f"{click.style(skill.name.ljust(25), bold=True)} {click.style('(project)' if skill.location == 'project' else '(global)', fg='blue' if skill.location == 'project' else 'dim')}",
                'value': skill.name,
                'checked': False
            }
            for skill in sorted_skills
        ]

        to_remove = _prompt_for_selection('Select skills to remove', choices)

        if not to_remove:
            click.echo(click.style("No skills selected for removal.", fg='yellow'))
            return

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
