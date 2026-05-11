import click

from openskills.models import InstallOptions
from openskills.finder import find_all_skills, find_skill
from openskills.installer import install_skill
from openskills.updater import update_skills
from openskills.remover import remove_skill, manage_skills
from openskills.market import market_list, market_search
from openskills.recommends import resolve_recommendation_tree, check_recommendations


def _terminal_link(url: str, text: str | None = None) -> str:
    label = text or url
    return f"\x1b]8;;{url}\x1b\\{label}\x1b]8;;\x1b\\"


def _format_source(source: str) -> str:
    if not source:
        return "(unknown)"
    if source.startswith("https://github.com/"):
        parts = source.replace("https://github.com/", "").split("/")
        return f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else source
    if source.startswith("git@github.com:"):
        cleaned = source.replace("git@github.com:", "").replace(".git", "")
        parts = cleaned.split("/")
        return f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else source
    if source.startswith("http://") or source.startswith("https://"):
        from urllib.parse import urlparse
        parsed = urlparse(source)
        return parsed.netloc + parsed.path
    return source


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
@click.option('--html', is_flag=True, help='Display in browser')
def market_list_cmd(html):
    """List all available skills in market"""
    market_list(html=html)


@market.command()
@click.argument('keyword')
def search(keyword):
    """Search market skills by keyword"""
    market_search(keyword)


@cli.group()
def recommends():
    """Manage skill recommendations"""
    pass


@recommends.command('check')
@click.argument('skill_name', required=False)
def recommends_check(skill_name):
    """Check recommendation satisfaction"""
    if skill_name:
        skill = find_skill(skill_name)
        if not skill:
            click.echo(f"Error: Skill '{skill_name}' not found")
            return
        results = check_recommendations(skill.base_dir)
        if results["missing"]:
            click.echo(click.style(f"✗ {skill_name} has uninstalled recommendations:", fg='red'))
            for rec in results["missing"]:
                link = _terminal_link(rec.source, _format_source(rec.source))
                click.echo(f"    - {click.style(rec.name, bold=True)} ({link})")
        elif results["satisfied"]:
            click.echo(click.style(f"✓ {skill_name} - all recommendations satisfied", fg='green'))
        else:
            click.echo(f"  {skill_name} has no recommendations")
    else:
        skills = find_all_skills()
        issues = 0
        ok = 0
        for skill in skills:
            results = check_recommendations(skill.path)
            if results["missing"]:
                issues += 1
                click.echo(click.style(f"✗ {skill.name} has uninstalled recommendations:", fg='red'))
                for rec in results["missing"]:
                    link = _terminal_link(rec.source, _format_source(rec.source))
                    click.echo(f"    - {click.style(rec.name, bold=True)} ({link})")
            elif results["satisfied"]:
                ok += 1
                click.echo(click.style(f"✓ {skill.name} - all recommendations satisfied", fg='green'))
        click.echo(click.style(f"\nSummary: {issues} skill(s) with uninstalled recommendations, {ok} skill(s) OK", dim=True))


@recommends.command('tree')
@click.argument('skill_name', required=False)
def recommends_tree(skill_name):
    """Display recommendation tree"""
    if skill_name:
        skill = find_skill(skill_name)
        if not skill:
            click.echo(f"Error: Skill '{skill_name}' not found")
            return
        tree = resolve_recommendation_tree(skill.base_dir)
        click.echo(_format_tree(tree))
    else:
        skills = find_all_skills()
        for skill in sorted(skills, key=lambda s: s.name):
            tree = resolve_recommendation_tree(skill.path)
            click.echo(_format_tree(tree))


@recommends.command('install')
@click.argument('skill_name')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def recommends_install(skill_name, yes):
    """Install missing recommendations for a skill"""
    from openskills.installer import prompt_for_selection
    skill = find_skill(skill_name)
    if not skill:
        click.echo(f"Error: Skill '{skill_name}' not found")
        return
    results = check_recommendations(skill.base_dir)
    if not results["missing"]:
        click.echo(click.style("All recommendations already satisfied.", fg='green'))
        return

    click.echo(click.style("Missing recommendations:", bold=True))
    for rec in results["missing"]:
        link = _terminal_link(rec.source, _format_source(rec.source))
        click.echo(f"  - {click.style(rec.name, bold=True)} ({link})")

    satisfied = results.get("satisfied", [])
    if satisfied:
        click.echo(click.style("Already installed:", fg='green'))
        for rec in satisfied:
            click.echo(f"  ✓ {rec.name}")

    if yes:
        to_install = [rec.name for rec in results["missing"]]
    else:
        choices = [
            {
                'name': f"{rec.name} ({_format_source(rec.source)})",
                'value': rec.name,
                'checked': True
            }
            for rec in results["missing"]
        ]
        to_install = prompt_for_selection('Select recommendations to install', choices)

    if not to_install:
        click.echo(click.style("No recommendations selected.", fg='yellow'))
        return

    options = InstallOptions(yes=yes)
    source_map = {rec.name: rec.source for rec in results["missing"]}
    for name in to_install:
        source = source_map.get(name, "")
        click.echo(f"  Installing: {click.style(name, bold=True)}")
        install_skill(source, options)


@recommends.command('add')
@click.argument('skill_name')
def recommends_add(skill_name):
    """Interactively add recommended companion skills"""
    from openskills.recommends import add_recommendation
    from openskills.models import SkillRecommendation
    from openskills.metadata import read_skill_metadata

    skill = find_skill(skill_name)
    if not skill:
        click.echo(f"Error: Skill '{skill_name}' not found")
        return

    click.echo(click.style(f"Adding recommendations for: {skill_name}", bold=True))

    metadata = read_skill_metadata(skill.base_dir)
    if metadata and metadata.recommends:
        click.echo(click.style("Current recommendations:", dim=True))
        for rec in metadata.recommends:
            click.echo(f"  - {rec.name} ({_format_source(rec.source)})")
    else:
        click.echo(click.style("No current recommendations.", dim=True))

    added = []
    try:
        while True:
            click.echo()
            rec_name = click.prompt("  Recommended skill name", default="", show_default=False)
            stripped = rec_name.strip()
            if not stripped:
                click.echo(click.style("  No name entered, finishing.", fg='yellow'))
                if not added:
                    click.echo(click.style("  No recommendations added.", fg='yellow'))
                break

            rec_source = click.prompt("  Source (git URL or leave empty)", default="", show_default=False)

            recommendation = SkillRecommendation(name=stripped, source=rec_source.strip())
            result = add_recommendation(skill.base_dir, recommendation)

            if result:
                added.append(stripped)
                click.echo(click.style(f"  ✓ Added '{stripped}'", fg='green'))
            else:
                click.echo(click.style(f"  ⚠ '{stripped}' already in recommendations, skipped", fg='yellow'))

            more = click.prompt("  Add another? (y/N)", default="n").strip().lower()
            if more != 'y':
                break
    except KeyboardInterrupt:
        click.echo()

    if added:
        click.echo(click.style(f"\n✓ Added {len(added)} recommendation(s) to {skill_name}", fg='green'))
        for name in added:
            click.echo(f"  - {name}")


def _format_tree(node: dict, prefix: str = "", is_last: bool = True) -> str:
    lines = []
    connector = "└── " if is_last else "├── "
    if prefix:
        lines.append(f"{prefix}{connector}{node['name']}")
    else:
        lines.append(node['name'])

    child_prefix = prefix + ("    " if is_last else "│   ")
    if not prefix:
        child_prefix = "  "
        for i, rec in enumerate(node.get('recs', [])):
            last = (i == len(node.get('recs', [])) - 1)
            sub = _format_tree(rec, child_prefix, last)
            lines.append(sub)
    else:
        for i, rec in enumerate(node.get('recs', [])):
            last = (i == len(node.get('recs', [])) - 1)
            sub = _format_tree(rec, child_prefix, last)
            lines.append(sub)

    return "\n".join(lines)


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
