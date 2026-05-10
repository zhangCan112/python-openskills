import os
import shutil
import subprocess
import sys
import tempfile
import click
from openskills.models import Skill, SkillSourceType, SkillSourceMetadata
from openskills.finder import find_all_skills, normalize_skill_names
from openskills.metadata import read_skill_metadata, write_skill_metadata
from openskills.yaml_utils import has_valid_frontmatter


def _is_path_inside(target_path: str, target_dir: str) -> bool:
    resolved_target = os.path.abspath(target_path)
    resolved_dir = os.path.abspath(target_dir)
    resolved_dir_sep = resolved_dir if resolved_dir.endswith(os.sep) else resolved_dir + os.sep
    return resolved_target.startswith(resolved_dir_sep)


def _update_skill_from_dir(target_path: str, source_dir: str) -> None:
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)

    if not _is_path_inside(target_path, target_dir):
        click.echo(click.style("Security error: Installation path outside target directory", fg='red'))
        sys.exit(1)

    local_meta_path = os.path.join(target_path, '.openskills.json')
    local_meta_backup = None
    if os.path.exists(local_meta_path):
        with open(local_meta_path, 'r', encoding='utf-8') as f:
            local_meta_backup = f.read()

    shutil.rmtree(target_path, ignore_errors=True)
    shutil.copytree(source_dir, target_path, dirs_exist_ok=True)

    source_meta_path = os.path.join(source_dir, '.openskills.json')
    if not os.path.exists(source_meta_path) and local_meta_backup is not None:
        with open(local_meta_path, 'w', encoding='utf-8') as f:
            f.write(local_meta_backup)


def _update_skill_from_local(target_path: str, metadata: SkillSourceMetadata, skill_name: str) -> tuple[bool, str]:
    local_path = metadata.local_path
    if not local_path or not os.path.exists(local_path):
        return False, 'Local source missing'

    skill_md_path = os.path.join(local_path, 'SKILL.md')
    if not os.path.exists(skill_md_path):
        return False, 'SKILL.md missing at local source'

    _update_skill_from_dir(target_path, local_path)
    write_skill_metadata(target_path, metadata)
    return True, ''


def _update_skill_from_git(target_path: str, metadata: SkillSourceMetadata, skill_name: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', '--quiet', metadata.repo_url, os.path.join(temp_dir, 'repo')],
                check=True,
                capture_output=True
            )

            repo_dir = os.path.join(temp_dir, 'repo')
            subpath = metadata.subpath if metadata.subpath and metadata.subpath != '.' else ''
            source_dir = os.path.join(repo_dir, subpath) if subpath else repo_dir

            skill_md_path = os.path.join(source_dir, 'SKILL.md')
            if not os.path.exists(skill_md_path):
                return False, f"SKILL.md not found in repo at {subpath or '.'}"

            _update_skill_from_dir(target_path, source_dir)
            write_skill_metadata(target_path, metadata)
            return True, ''
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else 'Unknown error'
            return False, f"git clone failed: {error_msg}"


def _is_local_path(source: str) -> bool:
    return (
        source.startswith('/') or
        source.startswith('./') or
        source.startswith('../') or
        source.startswith('~/')
    )


def _is_git_url(source: str) -> bool:
    return (
        source.startswith('git@') or
        source.startswith('git://') or
        source.startswith('http://') or
        source.startswith('https://') or
        source.endswith('.git')
    )


def _parse_git_source(source: str) -> dict:
    repo_url = source
    subpath = ''

    if source.startswith('http://') or source.startswith('https://'):
        parts = source.split('/')
        if len(parts) >= 5:
            repo_url = '/'.join(parts[:5])
            if len(parts) > 5:
                subpath = '/'.join(parts[5:])

    return {
        'source': source,
        'source_type': 'git',
        'repo_url': repo_url,
        'subpath': subpath,
    }


def _prompt_add_source(skill: Skill) -> bool:
    click.echo(f"\n  {click.style(skill.name, bold=True)} at {click.style(skill.path, dim=True)}")

    if not click.confirm(f"  Add source metadata for '{skill.name}'?", default=True):
        click.echo(click.style("  Skipped.", dim=True))
        return False

    source = click.prompt("  Source (git URL or local path)", type=str, default="").strip()
    if not source:
        click.echo(click.style("  Skipped (empty source).", dim=True))
        return False

    if _is_local_path(source):
        from pathlib import Path
        if source.startswith('~/'):
            local_path = os.path.join(str(Path.home()), source[2:])
        else:
            local_path = os.path.abspath(source)

        if not os.path.exists(local_path):
            click.echo(click.style(f"  Error: path does not exist: {local_path}", fg='red'))
            return False

        metadata = SkillSourceMetadata(
            source=source,
            source_type=SkillSourceType.LOCAL,
            local_path=local_path,
        )
    elif _is_git_url(source):
        parsed = _parse_git_source(source)
        metadata = SkillSourceMetadata(
            source=parsed['source'],
            source_type=SkillSourceType.GIT,
            repo_url=parsed['repo_url'],
            subpath=parsed['subpath'] or None,
        )
    else:
        click.echo(click.style("  Error: unrecognized source format (expected git URL or local path)", fg='red'))
        return False

    write_skill_metadata(skill.path, metadata)
    click.echo(click.style(f"  Metadata saved for '{skill.name}'.", fg='green'))
    return True


def _display_empty_state() -> None:
    click.echo("No skills installed.\n")
    click.echo("Install skills:")
    click.echo(f"  {click.style('openskills install anthropics/skills', fg='cyan')}         {click.style('# Project (default)', dim=True)}")
    click.echo(f"  {click.style('openskills install owner/skill --global', fg='cyan')}     {click.style('# Global (advanced)', dim=True)}")


def _display_error_summaries(error_categories: dict) -> None:
    if error_categories['missing_local_source']:
        click.echo(click.style(f"Local source missing ({len(error_categories['missing_local_source'])}): {', '.join(error_categories['missing_local_source'])}", fg='yellow'))

    if error_categories['missing_local_skill_file']:
        click.echo(click.style(f"Local SKILL.md missing ({len(error_categories['missing_local_skill_file'])}): {', '.join(error_categories['missing_local_skill_file'])}", fg='yellow'))

    if error_categories['missing_repo_url']:
        click.echo(click.style(f"Missing repo URL metadata ({len(error_categories['missing_repo_url'])}): {', '.join(error_categories['missing_repo_url'])}", fg='yellow'))

    if error_categories['missing_repo_skill_file']:
        formatted = ', '.join([f"{item['name']} ({item['subpath']})" for item in error_categories['missing_repo_skill_file']])
        click.echo(click.style(f"Repo SKILL.md missing ({len(error_categories['missing_repo_skill_file'])}): {formatted}", fg='yellow'))

    if error_categories['clone_failures']:
        click.echo(click.style(f"Clone failed ({len(error_categories['clone_failures'])}): {', '.join(error_categories['clone_failures'])}", fg='yellow'))


def update_skills(skill_names: str | list[str] | None) -> None:
    requested = normalize_skill_names(skill_names) if skill_names else []
    skills = find_all_skills()

    if not skills:
        _display_empty_state()
        return

    targets = skills

    if requested:
        requested_set = set(requested)
        targets = [s for s in skills if s.name in requested_set]

        missing = [name for name in requested if not any(s.name == name for s in skills)]
        if missing:
            click.echo(click.style(f"Skipping missing skills: {', '.join(missing)}", fg='yellow'))
    else:
        targets = skills

    if not targets:
        click.echo(click.style("No matching skills to update.", fg='yellow'))
        return

    updated = 0
    skipped = 0

    error_categories = {
        'missing_metadata': [],
        'missing_local_source': [],
        'missing_local_skill_file': [],
        'missing_repo_url': [],
        'missing_repo_skill_file': [],
        'clone_failures': []
    }

    skills_without_metadata: list[Skill] = []

    for skill in targets:
        metadata = read_skill_metadata(skill.path)

        if not metadata:
            click.echo(click.style(f"Skipped: {skill.name} (no source metadata)", fg='yellow'))
            error_categories['missing_metadata'].append(skill.name)
            skills_without_metadata.append(skill)
            skipped += 1
            continue

        if metadata.source_type == 'local':
            success, error = _update_skill_from_local(skill.path, metadata, skill.name)
            if success:
                click.echo(click.style(f"✅ Updated: {skill.name}", fg='green'))
                updated += 1
            else:
                click.echo(click.style(f"Skipped: {skill.name} ({error})", fg='yellow'))
                if 'source missing' in error:
                    error_categories['missing_local_source'].append(skill.name)
                elif 'SKILL.md' in error:
                    error_categories['missing_local_skill_file'].append(skill.name)
                skipped += 1
            continue

        if not metadata.repo_url:
            click.echo(click.style(f"Skipped: {skill.name} (missing repo URL metadata)", fg='yellow'))
            error_categories['missing_repo_url'].append(skill.name)
            skipped += 1
            continue

        success, error = _update_skill_from_git(skill.path, metadata, skill.name)
        if success:
            click.echo(click.style(f"✅ Updated: {skill.name}", fg='green'))
            updated += 1
        else:
            click.echo(click.style(f"Skipped: {skill.name} ({error})", fg='yellow'))
            if 'SKILL.md' in error:
                subpath = metadata.subpath if metadata.subpath and metadata.subpath != '.' else '.'
                error_categories['missing_repo_skill_file'].append({'name': skill.name, 'subpath': subpath})
            elif 'clone' in error:
                error_categories['clone_failures'].append(skill.name)
            skipped += 1

    click.echo(click.style(f"\nSummary: {updated} updated, {skipped} skipped ({len(targets)} total)", dim=True))

    _display_error_summaries(error_categories)

    if skills_without_metadata:
        click.echo(click.style(f"\n{len(skills_without_metadata)} skill(s) have no source metadata. Add sources to enable future updates:", bold=True))
        for skill in skills_without_metadata:
            _prompt_add_source(skill)
