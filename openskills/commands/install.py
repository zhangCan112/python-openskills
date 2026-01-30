"""
Install skill from GitHub or local path command
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
import click

from openskills.types import SkillSourceType, SkillSourceMetadata, InstallOptions
from openskills.utils import (
    get_skills_dir,
    has_valid_frontmatter,
    extract_yaml_field,
    write_skill_metadata,
)
from openskills.utils.marketplace_skills import ANTHROPIC_MARKETPLACE_SKILLS
from openskills.utils.yaml import has_valid_frontmatter, extract_yaml_field


def is_local_path(source: str) -> bool:
    """Check if source is a local path"""
    return (
        source.startswith('/') or
        source.startswith('./') or
        source.startswith('../') or
        source.startswith('~/')
    )


def is_git_url(source: str) -> bool:
    """Check if source is a git URL"""
    return (
        source.startswith('git@') or
        source.startswith('git://') or
        source.startswith('http://') or
        source.startswith('https://') or
        source.endswith('.git')
    )


def get_repo_name(repo_url: str) -> str | None:
    """Extract repo name from a git URL"""
    cleaned = repo_url.replace('.git', '')
    last_part = cleaned.split('/')[-1]
    if not last_part:
        return None
    maybe_repo = last_part.split(':')[-1] if ':' in last_part else last_part
    return maybe_repo or None


def expand_path(source: str) -> str:
    """Expand ~ to home directory"""
    if source.startswith('~/'):
        return os.path.join(str(Path.home()), source[2:])
    return os.path.abspath(source)


def is_path_inside(target_path: str, target_dir: str) -> bool:
    """Ensure target path stays within target directory"""
    resolved_target = os.path.abspath(target_path)
    resolved_dir = os.path.abspath(target_dir)
    resolved_dir_sep = resolved_dir if resolved_dir.endswith(os.sep) else resolved_dir + os.sep
    return resolved_target.startswith(resolved_dir_sep)


def warn_if_conflict(skill_name: str, target_path: str, is_project: bool, skip_prompt: bool = False) -> bool:
    """Warn if installing could conflict with marketplace. Returns True if should proceed."""
    from openskills.utils.marketplace_skills import ANTHROPIC_MARKETPLACE_SKILLS
    
    # Check if overwriting existing skill
    if os.path.exists(target_path):
        if skip_prompt:
            click.echo(click.style(f"Overwriting: {skill_name}", dim=True))
            return True
        
        if not click.confirm(click.style(f"Skill '{skill_name}' already exists. Overwrite?", fg='yellow'), default=False):
            return False
    
    # Warn about marketplace conflicts (global install only)
    if not is_project and skill_name in ANTHROPIC_MARKETPLACE_SKILLS:
        click.echo(click.style(f"\n⚠️  Warning: '{skill_name}' matches an Anthropic marketplace skill", fg='yellow'))
        click.echo(click.style('   Installing globally may conflict with Claude Code plugins.', dim=True))
        click.echo(click.style('   If you re-enable Claude plugins, this will be overwritten.', dim=True))
        click.echo(click.style('   Recommend: Use --project flag for conflict-free installation.\n', dim=True))
    
    return True


def get_directory_size(dir_path: str) -> int:
    """Get directory size in bytes"""
    size = 0
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            size += os.path.getsize(file_path)
    return size


def format_size(bytes: int) -> str:
    """Format bytes to human-readable size"""
    if bytes < 1024:
        return f'{bytes}B'
    if bytes < 1024 * 1024:
        return f'{bytes / 1024:.1f}KB'
    return f'{bytes / (1024 * 1024):.1f}MB'


def install_from_local(
    local_path: str,
    target_dir: str,
    options: InstallOptions,
    source_info: dict[str, Any]
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
        is_project = os.getcwd() in target_dir
        install_single_local_skill(local_path, target_dir, is_project, options, source_info)
    else:
        # Directory containing multiple skills - find all skills
        install_from_repo(local_path, target_dir, options, None, source_info)


def install_single_local_skill(
    skill_dir: str,
    target_dir: str,
    is_project: bool,
    options: InstallOptions,
    source_info: dict[str, Any]
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
    
    click.echo(click.style(f"✅ Installed: {skill_name}", fg='green'))
    click.echo(f"   Location: {target_path}")


def find_skills_in_repo(repo_dir: str) -> list[dict[str, Any]]:
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
    options: InstallOptions,
    repo_name: str | None,
    source_info: dict[str, Any]
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
        
        click.echo(click.style(f"✅ Installed: {skill_name}", fg='green'))
        installed_count += 1
    
    click.echo(click.style(f"\n✅ Installation complete: {installed_count} skill(s) installed", fg='green'))


def prompt_for_selection(message: str, choices: list[dict[str, Any]]) -> list[str]:
    """Prompt user to select from choices (simplified version)"""
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


def install_skill(source: str, options: InstallOptions) -> None:
    """
    Install skill from local path, GitHub, or Git URL
    
    Args:
        source: Source to install from (URL or local path)
        options: Installation options
    """
    folder = '.agent/skills' if options.universal else '.claude/skills'
    is_project = not options.global_install  # Default to project unless --global specified
    target_dir = os.path.join(os.getcwd(), folder) if is_project else os.path.join(str(Path.home()), folder)
    
    location = click.style(f"project ({folder})", fg="blue") if is_project else click.style(f"global (~/{folder})", dim=True)
    
    click.echo(f"Installing from: {click.style(source, fg='cyan')}")
    click.echo(f"Location: {location}")
    
    project_location = f"./{folder}"
    global_location = f"~/{folder}"
    
    if is_project:
        click.echo(click.style(f"Default install is project-local ({project_location}). Use --global for {global_location}.", dim=True))
    else:
        click.echo(click.style(f"Global install selected ({global_location}). Omit --global for {project_location}.", dim=True))
    click.echo('')
    
    # Handle local path installation
    if is_local_path(source):
        local_path = expand_path(source)
        source_info = {
            'source': source,
            'sourceType': 'local',
            'localRoot': local_path
        }
        install_from_local(local_path, target_dir, options, source_info)
        print_post_install_hints(is_project)
        return
    
    # Parse git source
    repo_url: str
    skill_subpath = ''
    
    if is_git_url(source):
        # Full git URL (SSH, HTTPS, git://)
        repo_url = source
    else:
        # GitHub shorthand: owner/repo or owner/repo/skill-path
        parts = source.split('/')
        if len(parts) == 2:
            repo_url = f"https://github.com/{source}"
        elif len(parts) > 2:
            repo_url = f"https://github.com/{parts[0]}/{parts[1]}"
            skill_subpath = '/'.join(parts[2:])
        else:
            click.echo(click.style("Error: Invalid source format", fg='red'))
            click.echo("Expected: owner/repo, owner/repo/skill-name, git URL, or local path")
            sys.exit(1)
    
    # Clone and install from git
    with tempfile.TemporaryDirectory() as temp_dir:
        source_info = {
            'source': source,
            'sourceType': 'git',
            'repoUrl': repo_url
        }
        
        try:
            click.echo("Cloning repository...")
            subprocess.run(
                ['git', 'clone', '--depth', '1', '--quiet', repo_url, os.path.join(temp_dir, 'repo')],
                check=True,
                capture_output=True
            )
            click.echo("Repository cloned")
        except subprocess.CalledProcessError as e:
            click.echo(click.style("Failed to clone repository", fg='red'))
            if e.stderr:
                click.echo(click.style(e.stderr.decode().strip(), dim=True))
            click.echo(click.style("\nTip: For private repos, ensure git SSH keys or credentials are configured", fg='yellow'))
            sys.exit(1)
        
        repo_dir = os.path.join(temp_dir, 'repo')
        
        if skill_subpath:
            # Install specific skill from subpath
            skill_dir = os.path.join(repo_dir, skill_subpath)
            skill_md_path = os.path.join(skill_dir, 'SKILL.md')
            
            if not os.path.exists(skill_md_path):
                click.echo(click.style(f"Error: SKILL.md not found at {skill_subpath}", fg='red'))
                sys.exit(1)
            
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not has_valid_frontmatter(content):
                click.echo(click.style("Error: Invalid SKILL.md (missing YAML frontmatter)", fg='red'))
                sys.exit(1)
            
            skill_name = os.path.basename(skill_subpath)
            target_path = os.path.join(target_dir, skill_name)
            
            should_install = warn_if_conflict(skill_name, target_path, is_project, options.yes)
            if not should_install:
                click.echo(click.style(f"Skipped: {skill_name}", fg='yellow'))
                return
            
            os.makedirs(target_dir, exist_ok=True)
            
            if not is_path_inside(target_path, target_dir):
                click.echo(click.style("Security error: Installation path outside target directory", fg='red'))
                sys.exit(1)
            
            shutil.copytree(skill_dir, target_path, dirs_exist_ok=True)
            
            metadata = SkillSourceMetadata(
                source=source_info['source'],
                source_type=SkillSourceType.GIT,
                repo_url=repo_url,
                subpath=skill_subpath,
                installed_at=None
            )
            write_skill_metadata(target_path, metadata)
            
            click.echo(click.style(f"✅ Installed: {skill_name}", fg='green'))
            click.echo(f"   Location: {target_path}")
        else:
            # Install from repo (may be multiple skills)
            repo_name = get_repo_name(repo_url)
            install_from_repo(repo_dir, target_dir, options, repo_name, source_info)
    
    print_post_install_hints(is_project)


def print_post_install_hints(is_project: bool) -> None:
    """Print post-install hints"""
    click.echo(f"\n{click.style('Read skill:', dim=True)} {click.style('npx openskills read <skill-name>', fg='cyan')}")
    if is_project:
        click.echo(f"{click.style('Sync to AGENTS.md:', dim=True)} {click.style('npx openskills sync', fg='cyan')}")