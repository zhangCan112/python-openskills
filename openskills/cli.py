import click

from openskills.models import InstallOptions
from openskills.finder import find_all_skills
from openskills.installer import install_skill
from openskills.updater import update_skills
from openskills.remover import remove_skill, manage_skills
from openskills.market import market_list, market_search


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version and exit')
@click.pass_context
def cli(ctx, version):
    """Universal skills manager for AI coding agents"""
    if version:
        try:
            from importlib.metadata import version as get_version
            v = get_version('openskills')
        except Exception:
            v = '2.0.0'
        click.echo(f'OpenSkills v{v}')
        ctx.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def list():
    """List all installed skills"""
    _list_skills()


@cli.command()
@click.argument('source')
@click.option('--global', 'global_install', is_flag=True, help='Install globally (default: project)')
@click.option('--yes', '-y', is_flag=True, help='Skip interactive selection, install all')
def install(source, global_install, yes):
    """Install skill from git URL, local path, or market name"""
    options = InstallOptions(global_install=global_install, yes=yes)
    install_skill(source, options)


@cli.command()
@click.argument('skill_name')
def remove(skill_name):
    """Remove a specific skill"""
    remove_skill(skill_name)


@cli.command()
@click.argument('skill_name')
def rm(skill_name):
    """Remove a specific skill (alias)"""
    remove_skill(skill_name)


@cli.command()
@click.argument('skill_names', nargs=-1)
def update(skill_names):
    """Update installed skills from their source (default: all)"""
    update_skills(list(skill_names) if skill_names else None)


@cli.command()
def manage():
    """Interactively manage (remove) installed skills"""
    manage_skills()


@cli.group()
def market():
    """Market commands for browsing available skills"""
    pass


@market.command('list')
@click.option('--tag', '-t', multiple=True, help='Filter by tag (can be used multiple times)')
@click.option('--html', is_flag=True, help='Display in browser')
def market_list_cmd(tag, html):
    """List all available skills in market"""
    market_list(tags=tag if tag else None, html=html)


@market.command()
@click.argument('keyword')
def search(keyword):
    """Search market skills by keyword"""
    market_search(keyword)


def _list_skills():
    click.echo(click.style('Available Skills:\n', bold=True))

    skills = find_all_skills()

    if not skills:
        _display_empty_state()
        return

    sorted_skills = sorted(skills, key=lambda s: (s.location != 'project', s.name))

    for skill in sorted_skills:
        if skill.location == 'project':
            location_label = click.style('(project)', fg='blue')
        else:
            location_label = click.style('(global)', dim=True)

        click.echo(f"  {click.style(skill.name.ljust(25), bold=True)} {location_label}")
        click.echo(f"    {click.style(skill.description, dim=True)}\n")

    project_count = len([s for s in skills if s.location == 'project'])
    global_count = len([s for s in skills if s.location == 'global'])
    click.echo(click.style(f'Summary: {project_count} project, {global_count} global ({len(skills)} total)', dim=True))


def _display_empty_state():
    click.echo('No skills installed.\n')
    click.echo('Install skills:')
    click.echo(f"  {click.style('openskills install anthropics/skills', fg='cyan')}         {click.style('# Project (default)', dim=True)}")
    click.echo(f"  {click.style('openskills install owner/skill --global', fg='cyan')}     {click.style('# Global', dim=True)}")


if __name__ == '__main__':
    cli()
