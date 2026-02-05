"""
Install command market operations
"""

import click
from openskills.utils.market import find_skill_by_name


def try_install_from_market(skill_name: str, options, install_func) -> bool:
    """
    Try to install skill from market by name
    
    Args:
        skill_name: Name of skill to install
        options: Installation options
        install_func: Function to call for installation
        
    Returns:
        True if skill was found and installed, False otherwise
    """
    # Search for skill in market
    matched_skills = find_skill_by_name(skill_name)
    
    if not matched_skills:
        return False
    
    if len(matched_skills) == 1:
        # Unique skill found - install it directly
        skill = matched_skills[0]
        click.echo(f"Found skill in market: {click.style(skill.name, fg='green')}")
        click.echo(f"Description: {skill.description}")
        click.echo(f"Source: {skill.source}")
        click.echo()
        
        # Install using the skill's source
        install_func(skill.source, options)
        return True
    else:
        # Multiple skills with same name - let user choose
        click.echo(click.style(f"Found multiple skills named '{skill_name}':\n", fg='yellow'))
        
        for i, skill in enumerate(matched_skills, 1):
            click.echo(f"{click.style(str(i), bold=True)}. {skill.name}")
            click.echo(f"   Source: {skill.source}")
            if skill.description:
                click.echo(f"   Description: {skill.description}")
            if skill.author:
                click.echo(f"   Author: {skill.author}")
            if skill.version:
                click.echo(f"   Version: {skill.version}")
            click.echo()
        
        # Prompt for selection
        while True:
            try:
                choice = click.prompt(
                    f"Select which skill to install [1-{len(matched_skills)}]",
                    type=int
                )
                if 1 <= choice <= len(matched_skills):
                    selected_skill = matched_skills[choice - 1]
                    click.echo()
                    install_func(selected_skill.source, options)
                    return True
                else:
                    click.echo(click.style("Invalid selection. Please try again.", fg='red'))
            except click.exceptions.Abort:
                click.echo("\nInstallation cancelled.")
                return False