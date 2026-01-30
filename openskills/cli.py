"""
CLI interface for OpenSkills
"""

import click
from openskills.commands import (
    list_skills,
    install_skill,
    read_skill,
    remove_skill,
    update_skills,
    sync_agents_md,
    manage_skills
)
from openskills.types import InstallOptions


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version and exit')
@click.pass_context
def cli(ctx, version):
    """Universal skills loader for AI coding agents"""
    if version:
        click.echo('OpenSkills Python version 1.0.0')
        ctx.exit(0)
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def list():
    """List all installed skills"""
    list_skills()


@cli.command()
@click.argument('source')
@click.option('--global', 'global_install', is_flag=True, help='Install globally (default: project install)')
@click.option('--universal', is_flag=True, help='Install to .agent/skills/ (for universal AGENTS.md usage)')
@click.option('--yes', '-y', is_flag=True, help='Skip interactive selection, install all skills found')
def install(source, global_install, universal, yes):
    """Install skill from GitHub or Git URL"""
    options = InstallOptions(
        global_install=global_install,
        universal=universal,
        yes=yes
    )
    install_skill(source, options)


@cli.command()
@click.argument('skill_names', nargs=-1, required=True)
def read(skill_names):
    """Read skill(s) to stdout (for AI agents)"""
    if len(skill_names) == 1:
        read_skill(skill_names[0])
    else:
        read_skill(list(skill_names))


@cli.command()
@click.argument('skill_name')
def remove(skill_name):
    """Remove specific skill (for scripts, use manage for interactive)"""
    remove_skill(skill_name)


@cli.command()
@click.argument('skill_names', nargs=-1)
def update(skill_names):
    """Update installed skills from their source (default: all)"""
    if skill_names:
        update_skills(list(skill_names))
    else:
        update_skills(None)


@cli.command()
@click.option('--yes', '-y', is_flag=True, help='Skip interactive selection, sync all skills')
@click.option('--output', '-o', help='Output file path (default: AGENTS.md)')
def sync(yes, output):
    """Update AGENTS.md with installed skills (interactive, pre-selects current state)"""
    sync_agents_md(yes=yes, output=output)


@cli.command()
def manage():
    """Interactively manage (remove) installed skills"""
    manage_skills()


@cli.command()
@click.argument('skill_name')
def rm(skill_name):
    """Remove specific skill"""
    remove_skill(skill_name)


if __name__ == '__main__':
    cli()