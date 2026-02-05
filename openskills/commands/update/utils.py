"""
Update command utilities
"""

import os
import shutil
import sys
import click
from openskills.commands.update.validators import is_path_inside


def update_skill_from_dir(target_path: str, source_dir: str) -> None:
    """Update skill from source directory"""
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)
    
    if not is_path_inside(target_path, target_dir):
        click.echo(click.style("Security error: Installation path outside target directory", fg='red'))
        sys.exit(1)
    
    shutil.rmtree(target_path, ignore_errors=True)
    shutil.copytree(source_dir, target_path, dirs_exist_ok=True)