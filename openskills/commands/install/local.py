"""
Install command local source operations
"""

import os
import sys
import shutil
import click
from openskills.utils import has_valid_frontmatter, write_skill_metadata
from openskills.types import SkillSourceType, SkillSourceMetadata
from openskills.commands.install.validators import warn_if_conflict, is_path_inside
from openskills.commands.install.utils import format_size


def install_single_local_skill(
    skill_dir: str,
    target_dir: str,
    is_project: bool,
    options,
    source_info: dict
) -> None:
    """Install a single local skill directory"""
    skill_md_path = os.path.join(skill_dir, 'SKILL.md')
    
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not has_valid_frontmatter(content):
        click.echo(click.style("Error: Invalid SKILL.md (missing YAML frontmatter)", fg='red'))
        sys.exit(1)
    
    skill_name = os.path.basename(skill_dir)
    target_path = os.path.join(target_dir, skill_name)
    
    should_install = warn_if_conflict(skill_name, target_path, is_project, options.yes)
    if not should_install:
        click.echo(click.style(f"Skipped: {skill_name}", fg='yellow'))
        return
    
    os.makedirs(target_dir, exist_ok=True)
    
    # Security: ensure target path stays within target directory
    if not is_path_inside(target_path, target_dir):
        click.echo(click.style("Security error: Installation path outside target directory", fg='red'))
        sys.exit(1)
    
    shutil.copytree(skill_dir, target_path, dirs_exist_ok=True)
    
    metadata = SkillSourceMetadata(
        source=source_info['source'],
        source_type=SkillSourceType.LOCAL,
        local_path=skill_dir,
        installed_at=None
    )
    write_skill_metadata(target_path, metadata)
    
    click.echo(click.style(f"[OK] Installed: {skill_name}", fg='green'))
    click.echo(f"   Location: {target_path}")


def install_from_local(
    local_path: str,
    target_dir: str,
    options,
    source_info: dict
) -> None:
    """Install from local path (directory containing skills or single skill)"""
    if not os.path.exists(local_path):
        click.echo(click.style(f"Error: Path does not exist: {local_path}", fg='red'))
        sys.exit(1)
    
    if not os.path.isdir(local_path):
        click.echo(click.style("Error: Path must be a directory", fg='red'))
        sys.exit(1)
    
    # Check if this is a single skill (has SKILL.md) or directory of skills
    skill_md_path = os.path.join(local_path, 'SKILL.md')
    
    if os.path.exists(skill_md_path):
        # Single skill directory
        from openskills.commands.install.repo import install_from_repo
        is_project = os.getcwd() in target_dir
        install_single_local_skill(local_path, target_dir, is_project, options, source_info)
    else:
        # Directory containing multiple skills - find all skills
        from openskills.commands.install.repo import install_from_repo
        install_from_repo(local_path, target_dir, options, None, source_info)