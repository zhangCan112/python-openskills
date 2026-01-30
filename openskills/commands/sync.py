"""
Sync installed skills to AGENTS.md command
"""

import os
import sys
import click
from typing import Any

from openskills.types import Skill
from openskills.utils import (
    find_all_skills,
    parse_current_skills,
    generate_skills_xml,
    replace_skills_section,
    remove_skills_section
)


def prompt_for_selection(message: str, choices: list[dict[str, Any]]) -> list[str]:
    """Prompt user to select from choices"""
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
            # Parse what's currently in output file
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            current_skills = parse_current_skills(content)
            
            # Sort: project first
            sorted_skills = sorted(skills, key=lambda s: (s.location != 'project', s.name))
            
            choices = [
                {
                    'name': f"{click.style(skill.name.ljust(25), bold=True)} {click.style('(project)' if skill.location == 'project' else '(global)', fg='blue' if skill.location == 'project' else 'dim')}",
                    'value': skill.name,
                    'checked': skill.name in current_skills or (len(current_skills) == 0 and skill.location == 'project')
                }
                for skill in sorted_skills
            ]
            
            selected = prompt_for_selection(f"Select skills to sync to {output_name}", choices)
            
            if not selected:
                # User unchecked everything - remove skills section
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                updated = remove_skills_section(content)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(updated)
                
                click.echo(click.style(f"✅ Removed all skills from {output_name}", fg='green'))
                return
            
            # Filter skills to selected ones
            skills = [s for s in skills if s.name in selected]
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
        click.echo(click.style(f"✅ Synced {len(skills)} skill(s) to {output_name}", fg='green'))
    else:
        click.echo(click.style(f"✅ Added skills section to {output_name} ({len(skills)} skill(s))", fg='green'))