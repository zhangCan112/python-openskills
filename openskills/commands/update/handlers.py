"""
Update command handlers
"""

import click
from openskills.commands.read.validators import normalize_skill_names
from openskills.utils import find_all_skills, read_skill_metadata
from openskills.commands.update.local import update_skill_from_local
from openskills.commands.update.git import update_skill_from_git


async def update_skills(skill_names: str | list[str] | None) -> None:
    """
    Update installed skills from their recorded source metadata
    
    Args:
        skill_names: Skill names to update (None for all)
    """
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
        # Default to updating all installed skills
        targets = skills
    
    if not targets:
        click.echo(click.style("No matching skills to update.", fg='yellow'))
        return
    
    updated = 0
    skipped = 0
    
    # Track different error categories
    error_categories = {
        'missing_metadata': [],
        'missing_local_source': [],
        'missing_local_skill_file': [],
        'missing_repo_url': [],
        'missing_repo_skill_file': [],
        'clone_failures': []
    }
    
    for skill in targets:
        metadata = read_skill_metadata(skill.path)
        
        if not metadata:
            click.echo(click.style(f"Skipped: {skill.name} (no source metadata; re-install once to enable updates)", fg='yellow'))
            error_categories['missing_metadata'].append(skill.name)
            skipped += 1
            continue
        
        if metadata.source_type == 'local':
            success, error = update_skill_from_local(skill.path, metadata, skill.name)
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
        
        success, error = update_skill_from_git(skill.path, metadata, skill.name)
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
    
    click.echo(click.style(f"Summary: {updated} updated, {skipped} skipped ({len(targets)} total)", dim=True))
    
    # Display error summaries
    _display_error_summaries(error_categories)


def _display_empty_state() -> None:
    """Display message when no skills are installed"""
    click.echo("No skills installed.\n")
    click.echo("Install skills:")
    click.echo(f"  {click.style('openskills install anthropics/skills', fg='cyan')}         {click.style('# Project (default)', dim=True)}")
    click.echo(f"  {click.style('openskills install owner/skill --global', fg='cyan')}     {click.style('# Global (advanced)', dim=True)}")


def _display_error_summaries(error_categories: dict) -> None:
    """
    Display summary of errors that occurred during update
    
    Args:
        error_categories: Dictionary of error categories to lists of affected skills
    """
    if error_categories['missing_metadata']:
        click.echo(click.style(f"Missing source metadata ({len(error_categories['missing_metadata'])}): {', '.join(error_categories['missing_metadata'])}", fg='yellow'))
        click.echo(click.style("Re-install these skills once to enable updates (e.g., `openskills install <source>`).", dim=True))
    
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