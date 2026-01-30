"""
Update installed skills command
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
import click

from openskills.commands.read import normalize_skill_names
from openskills.utils import find_all_skills, read_skill_metadata, write_skill_metadata
from openskills.utils.yaml import has_valid_frontmatter


async def update_skills(skill_names: str | list[str] | None) -> None:
    """
    Update installed skills from their recorded source metadata
    
    Args:
        skill_names: Skill names to update (None for all)
    """
    requested = normalize_skill_names(skill_names) if skill_names else []
    skills = find_all_skills()
    
    if not skills:
        click.echo("No skills installed.\n")
        click.echo("Install skills:")
        click.echo(f"  {click.style('npx openskills install anthropics/skills', fg='cyan')}         {click.style('# Project (default)', dim=True)}")
        click.echo(f"  {click.style('npx openskills install owner/skill --global', fg='cyan')}     {click.style('# Global (advanced)', dim=True)}")
        return
    
    targets = skills
    
    if requested:
        requested_set = set(requested)
        targets = [s for s in skills if s.name in requested_set]
        
        missing = [name for name in requested if not any(s.name == name for s in skills)]
        if missing:
            click.echo(click.style(f"Skipping missing skills: {', '.join(missing)}", fg='yellow'))
    else:
        # Default to updating all installed skills
        targets = skills
    
    if not targets:
        click.echo(click.style("No matching skills to update.", fg='yellow'))
        return
    
    updated = 0
    skipped = 0
    
    missing_metadata = []
    missing_local_source = []
    missing_local_skill_file = []
    missing_repo_url = []
    missing_repo_skill_file = []
    clone_failures = []
    
    for skill in targets:
        metadata = read_skill_metadata(skill.path)
        
        if not metadata:
            click.echo(click.style(f"Skipped: {skill.name} (no source metadata; re-install once to enable updates)", fg='yellow'))
            missing_metadata.append(skill.name)
            skipped += 1
            continue
        
        if metadata.source_type == 'local':
            local_path = metadata.local_path
            if not local_path or not os.path.exists(local_path):
                click.echo(click.style(f"Skipped: {skill.name} (local source missing)", fg='yellow'))
                missing_local_source.append(skill.name)
                skipped += 1
                continue
            
            skill_md_path = os.path.join(local_path, 'SKILL.md')
            if not os.path.exists(skill_md_path):
                click.echo(click.style(f"Skipped: {skill.name} (SKILL.md missing at local source)", fg='yellow'))
                missing_local_skill_file.append(skill.name)
                skipped += 1
                continue
            
            update_skill_from_dir(skill.path, local_path)
            write_skill_metadata(skill.path, metadata)
            click.echo(click.style(f"✅ Updated: {skill.name}", fg='green'))
            updated += 1
            continue
        
        if not metadata.repo_url:
            click.echo(click.style(f"Skipped: {skill.name} (missing repo URL metadata)", fg='yellow'))
            missing_repo_url.append(skill.name)
            skipped += 1
            continue
        
        with tempfile.TemporaryDirectory() as temp_dir:
            click.echo(f"Updating {skill.name}...")
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
                    click.echo(click.style(f"Skipped: {skill.name} (SKILL.md not found in repo at {subpath or '.'})", fg='yellow'))
                    missing_repo_skill_file.append({'name': skill.name, 'subpath': subpath or '.'})
                    skipped += 1
                    continue
                
                update_skill_from_dir(skill.path, source_dir)
                write_skill_metadata(skill.path, metadata)
                click.echo(click.style(f"✅ Updated: {skill.name}", fg='green'))
                updated += 1
            except subprocess.CalledProcessError as e:
                click.echo(click.style(f"Skipped: {skill.name} (git clone failed)", fg='yellow'))
                if e.stderr:
                    click.echo(click.style(e.stderr.decode().strip(), dim=True))
                clone_failures.append(skill.name)
                skipped += 1
    
    click.echo(click.style(f"Summary: {updated} updated, {skipped} skipped ({len(targets)} total)", dim=True))
    
    if missing_metadata:
        click.echo(click.style(f"Missing source metadata ({len(missing_metadata)}): {', '.join(missing_metadata)}", fg='yellow'))
        click.echo(click.style("Re-install these skills once to enable updates (e.g., `npx openskills install <source>`).", dim=True))
    if missing_local_source:
        click.echo(click.style(f"Local source missing ({len(missing_local_source)}): {', '.join(missing_local_source)}", fg='yellow'))
    if missing_local_skill_file:
        click.echo(click.style(f"Local SKILL.md missing ({len(missing_local_skill_file)}): {', '.join(missing_local_skill_file)}", fg='yellow'))
    if missing_repo_url:
        click.echo(click.style(f"Missing repo URL metadata ({len(missing_repo_url)}): {', '.join(missing_repo_url)}", fg='yellow'))
    if missing_repo_skill_file:
        formatted = ', '.join([f"{item['name']} ({item['subpath']})" for item in missing_repo_skill_file])
        click.echo(click.style(f"Repo SKILL.md missing ({len(missing_repo_skill_file)}): {formatted}", fg='yellow'))
    if clone_failures:
        click.echo(click.style(f"Clone failed ({len(clone_failures)}): {', '.join(clone_failures)}", fg='yellow'))


def update_skill_from_dir(target_path: str, source_dir: str) -> None:
    """Update skill from source directory"""
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)
    
    if not is_path_inside(target_path, target_dir):
        click.echo(click.style("Security error: Installation path outside target directory", fg='red'))
        sys.exit(1)
    
    shutil.rmtree(target_path, ignore_errors=True)
    shutil.copytree(source_dir, target_path, dirs_exist_ok=True)


def is_path_inside(target_path: str, target_dir: str) -> bool:
    """Ensure target path stays within target directory"""
    resolved_target = os.path.abspath(target_path)
    resolved_dir = os.path.abspath(target_dir)
    resolved_dir_sep = resolved_dir if resolved_dir.endswith(os.sep) else resolved_dir + os.sep
    return resolved_target.startswith(resolved_dir_sep)