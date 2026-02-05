"""
Market command handlers
"""

import click
from openskills.utils.market import list_all_skills, search_skills
from openskills.commands.market.html_generator import generate_market_html


def market_list(tags=None, html=False):
    """
    List all market skills (optional: filter by tags, display in HTML)
    
    Args:
        tags: Optional tuple of tags to filter by
        html: If True, display skills in an interactive HTML page
    """
    skills = list_all_skills()
    
    # Filter by tags if provided
    if tags:
        tags_list = list(tags)
        skills = [
            skill for skill in skills
            if all(tag.lower() in (t.lower() for t in skill.tags) for tag in tags_list)
        ]
    
    if not skills:
        click.echo(click.style("No skills found in market", fg='yellow'))
        click.echo("Use 'openskills market search <keyword>' to search")
        return
    
    # If HTML mode, generate and display HTML page
    if html:
        temp_path = generate_market_html(skills)
        click.echo(click.style("[OK] HTML page opened in browser", fg='green', bold=True))
        click.echo(click.style(f"  Temp file path: {temp_path}", fg='cyan'))
        return
    
    # Otherwise, display in terminal
    _display_terminal_output(skills)


def market_search(keyword: str):
    """
    Search market skills by keyword
    
    Args:
        keyword: Search keyword
    """
    skills = search_skills(keyword)
    
    if not skills:
        click.echo(click.style(f"No skills found matching '{keyword}'", fg='yellow'))
        return
    
    click.echo(click.style(f"Found {len(skills)} skill(s) matching '{keyword}'\n", bold=True))
    
    # Display each skill
    _display_terminal_output(skills, keyword)


def _display_terminal_output(skills, keyword: str | None = None):
    """
    Display skills in terminal format
    
    Args:
        skills: List of MarketSkill objects
        keyword: Optional keyword for highlighting
    """
    # Group skills by name
    from collections import defaultdict
    skills_by_name = defaultdict(list)
    for skill in skills:
        skills_by_name[skill.name].append(skill)
    
    # Display each skill
    for skill_name, skill_variants in sorted(skills_by_name.items()):
        click.echo(click.style(f"{skill_name}", fg='cyan', bold=True))
        
        for i, skill in enumerate(skill_variants):
            if len(skill_variants) > 1:
                variant_label = f"  [{i+1}] "
            else:
                variant_label = "      "
            
            # Description
            if skill.description:
                description = skill.description
                # Highlight matching keyword if provided
                if keyword:
                    import re
                    description = re.sub(
                        f'({keyword})',
                        click.style(r'\1', fg='yellow', bold=True),
                        description,
                        flags=re.IGNORECASE
                    )
                click.echo(f"{variant_label}{description}")
            else:
                click.echo(f"{variant_label}No description")
            
            # Metadata
            click.echo(f"      Source: {skill.source}")
            
            if skill.author:
                click.echo(f"      Author: {skill.author}")
            
            if skill.version:
                click.echo(f"      Version: {skill.version}")
            
            if skill.tags:
                click.echo(f"      Tags: {', '.join(skill.tags)}")
            
            click.echo()