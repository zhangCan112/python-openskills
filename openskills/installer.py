import os
import sys
import shutil
import subprocess
import hashlib
from pathlib import Path
from typing import Any

import click

from openskills.models import SkillSourceType, SkillSourceMetadata, InstallOptions
from openskills.yaml_utils import has_valid_frontmatter, extract_yaml_field
from openskills.metadata import write_skill_metadata
from openskills.dirs import get_skills_dir, get_cache_dir
from openskills.market import find_skill_by_name

ANTHROPIC_MARKETPLACE_SKILLS = [
    'xlsx',
    'docx',
    'pptx',
    'pdf',
    'algorithmic-art',
    'artifacts-builder',
    'brand-guidelines',
    'canvas-design',
    'internal-comms',
    'mcp-builder',
    'skill-creator',
    'slack-gif-creator',
    'template-skill',
    'theme-factory',
    'webapp-testing',
]


def is_local_path(source: str) -> bool:
    return (
        source.startswith('/') or
        source.startswith('./') or
        source.startswith('../') or
        source.startswith('~/')
    )


def is_git_url(source: str) -> bool:
    return (
        source.startswith('git@') or
        source.startswith('git://') or
        source.startswith('http://') or
        source.startswith('https://') or
        source.endswith('.git')
    )


def is_path_inside(target_path: str, target_dir: str) -> bool:
    resolved_target = os.path.abspath(target_path)
    resolved_dir = os.path.abspath(target_dir)
    resolved_dir_sep = resolved_dir if resolved_dir.endswith(os.sep) else resolved_dir + os.sep
    return resolved_target.startswith(resolved_dir_sep)


def expand_path(source: str) -> str:
    if source.startswith('~/'):
        return os.path.join(str(Path.home()), source[2:])
    return os.path.abspath(source)


def warn_if_conflict(skill_name: str, target_path: str, is_project: bool, skip_prompt: bool = False) -> bool:
    if os.path.exists(target_path):
        if skip_prompt:
            click.echo(click.style(f"Overwriting: {skill_name}", dim=True))
            return True

        if not click.confirm(click.style(f"Skill '{skill_name}' already exists. Overwrite?", fg='yellow'), default=False):
            return False

    if not is_project and skill_name in ANTHROPIC_MARKETPLACE_SKILLS:
        click.echo(click.style(f"\n⚠️  Warning: '{skill_name}' matches an Anthropic marketplace skill", fg='yellow'))
        click.echo(click.style('   Installing globally may conflict with Claude Code plugins.', dim=True))
        click.echo(click.style('   If you re-enable Claude plugins, this will be overwritten.', dim=True))
        click.echo(click.style('   Recommend: Use --project flag for conflict-free installation.\n', dim=True))

    return True


def get_repo_name(repo_url: str) -> str | None:
    cleaned = repo_url.replace('.git', '')
    last_part = cleaned.split('/')[-1]
    if not last_part:
        return None
    maybe_repo = last_part.split(':')[-1] if ':' in last_part else last_part
    return maybe_repo or None


def get_directory_size(dir_path: str) -> int:
    size = 0
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            size += os.path.getsize(file_path)
    return size


def format_size(bytes: int) -> str:
    if bytes < 1024:
        return f'{bytes}B'
    if bytes < 1024 * 1024:
        return f'{bytes / 1024:.1f}KB'
    return f'{bytes / (1024 * 1024):.1f}MB'


def print_post_install_hints(is_project: bool) -> None:
    click.echo(f"\n{click.style('Use', dim=True)} {click.style('openskills list', fg='cyan')} {click.style('to see installed skills', dim=True)}")


def get_cache_key(repo_url: str) -> str:
    return hashlib.sha256(repo_url.encode()).hexdigest()[:16]


def clone_to_cache(repo_url: str, cache_path: str) -> str:
    try:
        click.echo(click.style(f"Cloning repository to cache...", dim=True))
        subprocess.run(
            ['git', 'clone', '--depth', '1', '--quiet', repo_url, cache_path],
            check=True,
            capture_output=True
        )
        click.echo(click.style(f"Repository cloned to cache", fg='green'))
        return cache_path
    except subprocess.CalledProcessError as e:
        click.echo(click.style("Failed to clone repository", fg='red'))
        if e.stderr:
            click.echo(click.style(e.stderr.decode().strip(), dim=True))
        sys.exit(1)


def get_cached_repo(repo_url: str) -> str:
    cache_dir = get_cache_dir()
    cache_key = get_cache_key(repo_url)
    cache_path = os.path.join(cache_dir, cache_key)

    if os.path.exists(cache_path):
        try:
            click.echo(click.style(f"Updating cached repository...", dim=True))
            subprocess.run(
                ['git', 'fetch', '--quiet'],
                cwd=cache_path,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ['git', 'checkout', '--quiet', 'main'],
                cwd=cache_path,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ['git', 'pull', '--quiet'],
                cwd=cache_path,
                check=True,
                capture_output=True
            )
            click.echo(click.style(f"Cache updated", fg='green'))
        except subprocess.CalledProcessError:
            click.echo(click.style("Cache update failed, recloning...", fg='yellow'))
            shutil.rmtree(cache_path, ignore_errors=True)
            return clone_to_cache(repo_url, cache_path)

        return cache_path
    else:
        return clone_to_cache(repo_url, cache_path)


def prompt_for_selection(message: str, choices: list[dict[str, Any]]) -> list[str]:
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


def find_skills_in_repo(repo_dir: str) -> list[dict]:
    skill_infos = []

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
    skill_infos = find_skills_in_repo(repo_dir)

    if not skill_infos:
        click.echo(click.style("Error: No valid SKILL.md files found", fg='red'))
        sys.exit(1)

    click.echo(click.style(f"Found {len(skill_infos)} skill(s)\n", dim=True))

    skills_to_install = skill_infos

    if not options.yes and len(skill_infos) > 1:
        choices = [
            {
                'name': f"{click.style(info['skill_name'].ljust(25), bold=True)} {click.style(format_size(info['size']), dim=True)}",
                'value': info['skill_name'],
                'checked': True
            }
            for info in skill_infos
        ]

        selected = prompt_for_selection('Select skills to install', choices)

        if not selected:
            click.echo(click.style("No skills selected. Installation cancelled.", fg='yellow'))
            return

        skills_to_install = [info for info in skill_infos if info['skill_name'] in selected]

    is_project = os.getcwd() in target_dir
    installed_count = 0

    for info in skills_to_install:
        skill_name = info['skill_name']
        target_path = os.path.join(target_dir, skill_name)

        should_install = warn_if_conflict(skill_name, target_path, is_project, options.yes)
        if not should_install:
            click.echo(click.style(f"Skipped: {skill_name}", fg='yellow'))
            continue

        os.makedirs(target_dir, exist_ok=True)

        if not is_path_inside(target_path, target_dir):
            click.echo(click.style("Security error: Installation path outside target directory", fg='red'))
            continue

        shutil.copytree(info['skill_dir'], target_path, dirs_exist_ok=True)

        if source_info['source_type'] == 'local':
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
                repo_url=source_info.get('repo_url'),
                subpath=subpath,
                installed_at=None
            )

        write_skill_metadata(target_path, metadata)

        click.echo(click.style(f"[OK] Installed: {skill_name}", fg='green'))
        installed_count += 1

    click.echo(click.style(f"\n[OK] Installation complete: {installed_count} skill(s) installed", fg='green'))


def install_single_local_skill(
    skill_dir: str,
    target_dir: str,
    is_project: bool,
    options,
    source_info: dict
) -> None:
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
    if not os.path.exists(local_path):
        click.echo(click.style(f"Error: Path does not exist: {local_path}", fg='red'))
        sys.exit(1)

    if not os.path.isdir(local_path):
        click.echo(click.style("Error: Path must be a directory", fg='red'))
        sys.exit(1)

    skill_md_path = os.path.join(local_path, 'SKILL.md')

    if os.path.exists(skill_md_path):
        is_project = os.getcwd() in target_dir
        install_single_local_skill(local_path, target_dir, is_project, options, source_info)
    else:
        install_from_repo(local_path, target_dir, options, None, source_info)


def try_install_from_market(skill_name: str, options, install_func) -> bool:
    matched_skills = find_skill_by_name(skill_name)

    if not matched_skills:
        return False

    if len(matched_skills) == 1:
        skill = matched_skills[0]
        click.echo(f"Found skill in market: {click.style(skill.name, fg='green')}")
        click.echo(f"Description: {skill.description}")
        click.echo(f"Source: {skill.source}")
        click.echo()

        install_func(skill.source, options)
        return True
    else:
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


def install_skill(source: str, options: InstallOptions) -> None:
    folder = '.claude/skills'
    is_project = not options.global_install
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

    if not is_local_path(source) and not is_git_url(source):
        if try_install_from_market(source, options, install_skill):
            return

    if is_local_path(source):
        local_path = expand_path(source)
        source_info = {
            'source': source,
            'source_type': 'local',
            'local_root': local_path
        }
        install_from_local(local_path, target_dir, options, source_info)
        print_post_install_hints(is_project)
        return

    expanded_source = expand_path(source)
    if os.path.isdir(expanded_source):
        source_info = {
            'source': source,
            'source_type': 'local',
            'local_root': expanded_source
        }
        install_from_local(expanded_source, target_dir, options, source_info)
        print_post_install_hints(is_project)
        return

    _install_from_git(source, target_dir, is_project, options)
    print_post_install_hints(is_project)


def _install_from_git(source: str, target_dir: str, is_project: bool, options: InstallOptions) -> None:
    repo_url: str
    skill_subpath = ''

    if not is_git_url(source):
        click.echo(click.style("Error: Invalid source format", fg='red'))
        click.echo("Expected: complete git URL (e.g., https://github.com/owner/repo) or local path")
        sys.exit(1)

    if source.startswith('http://') or source.startswith('https://'):
        parts = source.split('/')

        if len(parts) < 5:
            click.echo(click.style("Error: Invalid URL format", fg='red'))
            click.echo("Expected: https://domain.com/owner/repo[/skill-path]")
            sys.exit(1)

        repo_url = '/'.join(parts[:5])

        if len(parts) > 5:
            skill_subpath = '/'.join(parts[5:])
    elif source.startswith('git@'):
        repo_url = source
    else:
        repo_url = source

    repo_dir = get_cached_repo(repo_url)

    source_info = {
        'source': source,
        'source_type': 'git',
        'repo_url': repo_url
    }

    if skill_subpath:
        _install_from_subpath(skill_subpath, repo_dir, target_dir, is_project, options, source_info)
    else:
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
        repo_url=source_info['repo_url'],
        subpath=skill_subpath,
        installed_at=None
    )
    write_skill_metadata(target_path, metadata)

    click.echo(click.style(f"[OK] Installed: {skill_name}", fg='green'))
    click.echo(f"   Location: {target_path}")
