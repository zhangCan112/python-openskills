"""
Install command repository operations
"""

import os
import shutil
import sys
import click
from openskills.utils import has_valid_frontmatter, extract_yaml_field, write_skill_metadata
from openskills.types import SkillSourceType, SkillSourceMetadata
from openskills.commands.install.validators import warn_if_conflict, is_path_inside
from openskills.commands.install.utils import get_repo_name, get_directory_size, format_size
from openskills.commands.install.prompts import prompt_for_selection


def find_skills_in_repo(repo_dir: str) -> list[dict]:
    """Find all skills in a repository"""
    skill_infos = []
    
    # Check for root skill
    root_skill_path = os.path.join(repo_dir, 'SKILL.md')
    if os.path.exists(root_skill_path):
        with open(root_skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if has_valid_frontmatter(content):
            frontmatter_name = extract_yaml_field(content, 'name')
            skill_name = frontmatter_name or get_repo_name(repo_dir) or os.path.basename(repo_dir)
            
            skill_infos.append({
                'skill_dir': repo_dir,
                'skill_name': skill_name,
                'description': extract_yaml_field(content, 'description'),
                'size': get_directory_size(repo_dir)
            })
    
    # Recursively find skills
    for root, dirs, files in os.walk(repo_dir):
        if 'SKILL.md' in files and root != repo_dir:
            skill_md_path = os.path.join(root, 'SKILL.md')
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if has_valid_frontmatter(content):
                skill_name = os.path.basename(root)
                description = extract_yaml_field(content, 'description')
                
                skill_infos.append({
                    'skill_dir': root,
                    'skill_name': skill_name,
                    'description': description,
                    'size': get_directory_size(root)
                })
    
    return skill_infos


def install_from_repo(
    repo_dir: str,
    target_dir: str,
    options,
    repo_name: str | None,
    source_info: dict
) -> None:
    """Install from repository (with interactive selection unless -y flag)"""
    skill_infos = find_skills_in_repo(repo_dir)
    
    if not skill_infos:
        click.echo(click.style("Error: No valid SKILL.md files found", fg='red'))
        sys.exit(1)
    
    click.echo(click.style(f"Found {len(skill_infos)} skill(s)\n", dim=True))
    
    # Interactive selection (unless -y flag or single skill)
    skills_to_install = skill_infos
    
    if not options.yes and len(skill_infos) > 1:
        choices = [
            {
                'name': f"{click.style(info['skill_name'].ljust(25), bold=True)} {click.style(format_size(info['size']), dim=True)}",
                'value': info['skill_name'],
                'checked': True  # Check all by default
            }
            for info in skill_infos
        ]
        
        selected = prompt_for_selection('Select skills to install', choices)
        
        if not selected:
            click.echo(click.style("No skills selected. Installation cancelled.", fg='yellow'))
            return
        
        skills_to_install = [info for info in skill_infos if info['skill_name'] in selected]
    
    # Install selected skills
    is_project = os.getcwd() in target_dir
    installed_count = 0
    
    for info in skills_to_install:
        skill_name = info['skill_name']
        target_path = os.path.join(target_dir, skill_name)
        
        # Warn about conflicts
        should_install = warn_if_conflict(skill_name, target_path, is_project, options.yes)
        if not should_install:
            click.echo(click.style(f"Skipped: {skill_name}", fg='yellow'))
            continue
        
        os.makedirs(target_dir, exist_ok=True)
        
        # Security: ensure target path stays within target directory
        if not is_path_inside(target_path, target_dir):
            click.echo(click.style("Security error: Installation path outside target directory", fg='red'))
            continue
        
        shutil.copytree(info['skill_dir'], target_path, dirs_exist_ok=True)
        
        # Build metadata
        if source_info['sourceType'] == 'local':
            metadata = SkillSourceMetadata(
                source=source_info['source'],
                source_type=SkillSourceType.LOCAL,
                local_path=info['skill_dir'],
                installed_at=None
            )
        else:
            subpath = os.path.relpath(info['skill_dir'], repo_dir)
            subpath = '' if subpath == '.' else subpath
            metadata = SkillSourceMetadata(
                source=source_info['source'],
                source_type=SkillSourceType.GIT,
                repo_url=source_info.get('repoUrl'),
                subpath=subpath,
                installed_at=None
            )
        
        write_skill_metadata(target_path, metadata)
        
        click.echo(click.style(f"[OK] Installed: {skill_name}", fg='green'))
        installed_count += 1
    
    click.echo(click.style(f"\n[OK] Installation complete: {installed_count} skill(s) installed", fg='green'))