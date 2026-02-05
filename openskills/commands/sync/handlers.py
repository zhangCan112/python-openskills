"""
Sync command handlers
"""

import os
import sys
import click
from openskills.skill_types import Skill
from openskills.utils import (
    find_all_skills,
    parse_current_skills,
    generate_skills_xml,
    replace_skills_section,
    remove_skills_section
)
from openskills.commands.sync.prompts import prompt_for_selection
from openskills.commands.compat import sync_to_targets


def sync_agents_md(yes: bool = False, output: str | None = None) -> None:
    """
    Sync installed skills to a markdown file
    
    Args:
        yes: Skip interactive selection
        output: Output file path (default: AGENTS.md)
    """
    output_path = output or 'AGENTS.md'
    output_name = os.path.basename(output_path)
    
    # Validate output file is markdown
    if not output_path.endswith('.md'):
        click.echo(click.style("Error: Output file must be a markdown file (.md)", fg='red'))
        sys.exit(1)
    
    # Create file if it doesn't exist
    if not os.path.exists(output_path):
        dir_name = os.path.dirname(output_path)
        if dir_name and dir_name != '.' and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {output_name.replace('.md', '')}\n\n")
        
        click.echo(click.style(f"Created {output_path}", dim=True))
    
    skills = find_all_skills()
    
    if not skills:
        click.echo("No skills installed. Install skills first:")
        click.echo(f"  {click.style('openskills install anthropics/skills --project', fg='cyan')}")
        return
    
    # Interactive mode by default (unless -y flag)
    if not yes:
        try:
            skills = _interactive_selection(skills, output_path, output_name)
        except (EOFError, KeyboardInterrupt):
            click.echo(click.style("\n\nCancelled by user", fg='yellow'))
            sys.exit(0)
    
    xml = generate_skills_xml(skills)
    
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated = replace_skills_section(content, xml)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(updated)
    
    had_markers = '<skills_system' in content or '<!-- SKILLS_TABLE_START -->' in content
    
    if had_markers:
        click.echo(click.style(f"[OK] Synced {len(skills)} skill(s) to {output_name}", fg='green'))
    else:
        click.echo(click.style(f"[OK] Added skills section to {output_name} ({len(skills)} skill(s))", fg='green'))
    
    # Sync to active target tools (copilot, cline, etc.)
    sync_to_targets(skills, updated)


def _interactive_selection(skills: list[Skill], output_path: str, output_name: str) -> list[Skill]:
    """
    Handle interactive skill selection
    
    Args:
        skills: List of all available skills
        output_path: Path to output file
        output_name: Name of output file
        
    Returns:
        List of selected skills
    """
    # Parse what's currently in output file
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    current_skills = parse_current_skills(content)
    
    # Sort: project first
    sorted_skills = sorted(skills, key=lambda s: (s.location != 'project', s.name))
    
    choices = [
        {
            'name': f"{skill.name.ljust(25)} {'(project)' if skill.location == 'project' else '(global)'}",
            'value': skill.name,
            'checked': skill.name in current_skills
        }
        for skill in sorted_skills
    ]
    
    selected = prompt_for_selection(f"Select skills to sync to {output_name}", choices)
    
    if not selected:
        # User unchecked everything - ask for confirmation
        click.echo(click.style("\nNo skills selected. This will remove all skills from the file.", fg='yellow'))
        if click.confirm(click.style("Do you want to continue?", fg='yellow'), default=False):
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            updated = remove_skills_section(content)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(updated)
            
            click.echo(click.style(f"[OK] Removed all skills from {output_name}", fg='green'))
            return []
        else:
            # User cancelled - keep current skills
            click.echo(click.style("Cancelled. No changes made.", fg='yellow'))
            sys.exit(0)
    
    # Filter skills to selected ones
    return [s for s in skills if s.name in selected]