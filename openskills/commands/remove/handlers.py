"""
Remove skill command handlers
"""

import os
import shutil
import sys
from pathlib import Path
import click

from openskills.utils import find_skill


def remove_skill(skill_name: str) -> None:
    """
    Remove installed skill
    
    Args:
        skill_name: Name of the skill to remove
    """
    skill = find_skill(skill_name)
    
    if not skill:
        click.echo(f"Error: Skill '{skill_name}' not found", err=True)
        sys.exit(1)
    
    shutil.rmtree(skill.base_dir, ignore_errors=True)
    
    location = 'global' if str(Path.home()) in skill.source else 'project'
    click.echo(f"✅ Removed: {skill_name}")
    click.echo(f"   From: {location} ({skill.source})")