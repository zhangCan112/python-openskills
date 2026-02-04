"""
Market commands for listing and searching skills
"""

import click
from openskills.utils.market import (
    list_all_skills,
    search_skills,
    find_skill_by_name
)


def market_list(tags=None):
    """List all market skills (optional: filter by tags)"""
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
    
    click.echo(click.style(f"Found {len(skills)} skill(s) in market\n", bold=True))
    
    # Group skills by name
    from collections import defaultdict
    skills_by_name = defaultdict(list)
    for skill in skills:
        skills_by_name[skill.name].append(skill)
    
    # Display each skill (with duplicates grouped)
    for skill_name, skill_variants in sorted(skills_by_name.items()):
        click.echo(click.style(f"{skill_name}", fg='cyan', bold=True))
        
        for i, skill in enumerate(skill_variants):
            if len(skill_variants) > 1:
                # Show variant number if there are duplicates
                variant_label = f"  [{i+1}] "
            else:
                variant_label = "      "
            
            # Description
            if skill.description:
                click.echo(f"{variant_label}{skill.description}")
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


def market_search(keyword: str):
    """Search market skills by keyword"""
    skills = search_skills(keyword)
    
    if not skills:
        click.echo(click.style(f"No skills found matching '{keyword}'", fg='yellow'))
        return
    
    click.echo(click.style(f"Found {len(skills)} skill(s) matching '{keyword}'\n", bold=True))
    
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
            
            # Highlight matching keyword in description
            if skill.description:
                description = skill.description
                # Highlight matches
                import re
                highlighted = re.sub(
                    f'({keyword})',
                    click.style(r'\1', fg='yellow', bold=True),
                    description,
                    flags=re.IGNORECASE
                )
                click.echo(f"{variant_label}{highlighted}")
            else:
                click.echo(f"{variant_label}No description")
            
            click.echo(f"      Source: {skill.source}")
            
            if skill.tags:
                click.echo(f"      Tags: {', '.join(skill.tags)}")
            
            click.echo()