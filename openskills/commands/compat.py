"""
Compatibility export command for AI tools that don't support AGENTS.md
"""

import os
import click
from typing import Any


# Define target configurations
TARGETS = {
    'copilot': {
        'path': '.github/instructions/openskills.instructions.md',
        'description': 'GitHub Copilot',
        'format': 'markdown'
    },
    'cline': {
        'path': '.clinerules/agents.md',
        'description': 'Cline',
        'format': 'text'
    }
}


def compat_export(target: str, source: str | None = None) -> None:
    """
    Export AGENTS.md content to target tool's configuration file
    
    Args:
        target: Target tool name (copilot, cline)
        source: Source file path (default: AGENTS.md)
    """
    # Validate target
    if target not in TARGETS:
        available = ', '.join(TARGETS.keys())
        click.echo(click.style(f"Error: Invalid target '{target}'. Available targets: {available}", fg='red'))
        return
    
    source_path = source or 'AGENTS.md'
    target_config = TARGETS[target]
    target_path = target_config['path']
    
    # Check if source file exists
    if not os.path.exists(source_path):
        click.echo(click.style(f"Error: Source file '{source_path}' not found.", fg='red'))
        click.echo(f"Please run: {click.style('openskills sync', fg='cyan')}")
        return
    
    # Read source content
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create target directory if needed
    target_dir = os.path.dirname(target_path)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        click.echo(click.style(f"Created directory: {target_dir}", dim=True))
    
    # Check if target file exists
    exists = os.path.exists(target_path)
    if exists:
        with open(target_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        if existing_content == content:
            click.echo(click.style(f"[OK] {target_config['description']} configuration is already up to date", fg='green'))
            return
    
    # Write to target file
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    if exists:
        click.echo(click.style(f"[OK] Updated {target_config['description']} configuration: {target_path}", fg='green'))
    else:
        click.echo(click.style(f"[OK] Created {target_config['description']} configuration: {target_path}", fg='green'))
    
    # Show usage hint
    click.echo(f"\n{target_config['description']} will now use the skills defined in AGENTS.md")


def list_active_targets() -> list[str]:
    """
    List targets that have been previously configured
    
    Returns:
        List of target names that have configuration files
    """
    active_targets = []
    for target_name, config in TARGETS.items():
        if os.path.exists(config['path']):
            active_targets.append(target_name)
    return active_targets


def sync_to_targets(skills: list[Any], source_content: str) -> None:
    """
    Sync skills to all active target configurations
    
    Args:
        skills: List of skills (unused but kept for interface consistency)
        source_content: The updated content to write to targets
    """
    active_targets = list_active_targets()
    
    if not active_targets:
        return
    
    click.echo(click.style(f"\nSyncing to {len(active_targets)} target tool(s)...", dim=True))
    
    for target in active_targets:
        target_config = TARGETS[target]
        target_path = target_config['path']
        
        # Ensure directory exists
        target_dir = os.path.dirname(target_path)
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        # Write updated content
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(source_content)
        
        click.echo(click.style(f"  [OK] Updated {target_config['description']}: {target_path}", fg='green'))
