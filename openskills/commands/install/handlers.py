"""
Install command handlers
"""

import os
import sys
import shutil
from pathlib import Path
import click
from openskills.types import InstallOptions, SkillSourceType, SkillSourceMetadata
from openskills.utils import has_valid_frontmatter, write_skill_metadata, get_skills_dir
from openskills.utils.config import get_github_base_url
from openskills.commands.install.validators import is_local_path, is_git_url, expand_path
from openskills.commands.install.utils import get_repo_name, print_post_install_hints
from openskills.commands.install.cache import get_cached_repo
from openskills.commands.install.local import install_from_local
from openskills.commands.install.repo import install_from_repo
from openskills.commands.install.market import try_install_from_market


def install_skill(source: str, options: InstallOptions) -> None:
    """
    Install skill from local path, GitHub, or Git URL
    
    Args:
        source: Source to install from (URL, local path, or skill name)
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
    
    # Try to install from market first if source is not a URL or local path
    if not is_local_path(source) and not is_git_url(source):
        # Pass install_skill as a parameter to avoid circular import
        if try_install_from_market(source, options, install_skill):
            return
    
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
    
    # Check if source is an existing local path (without prefix)
    expanded_source = expand_path(source)
    if os.path.isdir(expanded_source):
        source_info = {
            'source': source,
            'sourceType': 'local',
            'localRoot': expanded_source
        }
        install_from_local(expanded_source, target_dir, options, source_info)
        print_post_install_hints(is_project)
        return
    
    # Parse git source
    _install_from_git(source, target_dir, is_project, options)
    print_post_install_hints(is_project)


def _install_from_git(source: str, target_dir: str, is_project: bool, options: InstallOptions) -> None:
    """
    Handle installation from Git source
    
    Args:
        source: Source string
        target_dir: Target installation directory
        is_project: Whether this is a project install
        options: Installation options
    """
    repo_url: str
    skill_subpath = ''
    
    if is_git_url(source):
        # Check if it's a GitHub HTTPS URL with subpath
        # Format: https://github.com/owner/repo[/skill-path]
        github_base = get_github_base_url()
        
        if source.startswith(f'{github_base}/'):
            # Remove 'https://host/' prefix
            path_part = source[len(f'{github_base}/'):]
            parts = path_part.split('/')
            
            if len(parts) >= 2:
                # First two parts are owner/repo
                repo_url = f"{github_base}/{parts[0]}/{parts[1]}"
                
                # Remaining parts (if any) are the subpath
                if len(parts) > 2:
                    skill_subpath = '/'.join(parts[2:])
            else:
                click.echo(click.style("Error: Invalid GitHub URL format", fg='red'))
                click.echo(f"Expected: {github_base}/owner/repo[/skill-path]")
                sys.exit(1)
        else:
            # Full git URL (SSH, other HTTPS, git://)
            # For non-GitHub URLs, we assume the URL points to the repo root
            repo_url = source
    else:
        # GitHub shorthand: owner/repo or owner/repo/skill-path
        # Or market format: github.com/owner/repo or github.com/owner/repo/skill-path
        github_base = get_github_base_url()
        parts = source.split('/')
        
        # Check if it's market format (starts with github.com/)
        if parts[0] == 'github.com' and len(parts) >= 2:
            # Market format: github.com/owner/repo or github.com/owner/repo/skill-path
            if len(parts) >= 3:
                repo_url = f"{github_base}/{parts[1]}/{parts[2]}"
                if len(parts) > 3:
                    skill_subpath = '/'.join(parts[3:])
            else:
                click.echo(click.style("Error: Invalid market source format", fg='red'))
                click.echo("Expected: github.com/owner/repo or github.com/owner/repo/skill-path")
                sys.exit(1)
        elif len(parts) == 2:
            # Standard shorthand: owner/repo
            repo_url = f"{github_base}/{source}"
        elif len(parts) > 2:
            # Standard shorthand with subpath: owner/repo/skill-path
            repo_url = f"{github_base}/{parts[0]}/{parts[1]}"
            skill_subpath = '/'.join(parts[2:])
        else:
            click.echo(click.style("Error: Invalid source format", fg='red'))
            click.echo("Expected: owner/repo, owner/repo/skill-name, github.com/owner/repo, git URL, or local path")
            sys.exit(1)
    
    # Get or clone repository from cache
    repo_dir = get_cached_repo(repo_url)
    
    source_info = {
        'source': source,
        'sourceType': 'git',
        'repoUrl': repo_url
    }
    
    if skill_subpath:
        # Install specific skill from subpath
        _install_from_subpath(skill_subpath, repo_dir, target_dir, is_project, options, source_info)
    else:
        # Install from repo (may be multiple skills)
        repo_name = get_repo_name(repo_url)
        install_from_repo(repo_dir, target_dir, options, repo_name, source_info)


def _install_from_subpath(
    skill_subpath: str,
    repo_dir: str,
    target_dir: str,
    is_project: bool,
    options: InstallOptions,
    source_info: dict
) -> None:
    """
    Install a specific skill from a repository subpath
    
    Args:
        skill_subpath: Path to skill within repository
        repo_dir: Path to repository
        target_dir: Target installation directory
        is_project: Whether this is a project install
        options: Installation options
        source_info: Source information dictionary
    """
    from openskills.commands.install.validators import warn_if_conflict, is_path_inside
    
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
        repo_url=source_info['repoUrl'],
        subpath=skill_subpath,
        installed_at=None
    )
    write_skill_metadata(target_path, metadata)
    
    click.echo(click.style(f"[OK] Installed: {skill_name}", fg='green'))
    click.echo(f"   Location: {target_path}")