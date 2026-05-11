# OpenSkills

A Python CLI tool for managing AI coding agent skills (SKILL.md format). Handles the full lifecycle: discover, install, update, and remove.

## Installation

```bash
pip install .
# or from git
pip install git+https://github.com/zhangCan112/python-openskills
```

Requires Python 3.11+.

## CLI Commands

```
openskills list                          # List all installed skills
openskills install <source>              # Install from git URL / local path / market name
        [--global]                       #   Install to global directory
        [--yes / -y]                     #   Skip interactive confirmation
openskills update [skill1 skill2 ...]    # Update skills (default: all)
openskills remove <skill>                # Remove a single skill
openskills rm <skill>                    # Alias for remove
openskills manage                        # Interactive batch management (remove)
openskills market list                   # List market skills
                    [--html]             #   HTML format (open in browser)
openskills market search <keyword>       # Search market skills
openskills recommends check [skill]      # Check recommendation satisfaction
openskills recommends tree [skill]       # Display recommendation tree
openskills recommends install <skill>    # Install missing recommendations
openskills recommends add <skill>        # Interactively add recommended companion skills
openskills --version                     # Show version
```

### Install Sources

```bash
# From git URL (HTTPS or SSH)
openskills install https://github.com/owner/repo
openskills install git@github.com:owner/repo.git

# From git URL with subpath (install a specific skill in the repo)
openskills install https://github.com/owner/repo/skills/my-skill

# From local path
openskills install ./local-skill

# From market name (look up in market database)
openskills install pdf
openskills install skill-creator
```

### Update

When updating, skills without `.openskills.json` metadata will be listed with an interactive prompt to add source information — just paste a full git URL or local path, and it will be automatically parsed.

```
$ openskills update
...
1 skill(s) have no source metadata. Add sources to enable future updates:

  my-skill at .agents/skills/my-skill
  Add source metadata for 'my-skill'? [Y/n] y
  Source (git URL or local path): https://github.com/owner/repo/skills/my-skill
  Metadata saved for 'my-skill'.
```

During update, local `.openskills.json` files are preserved if the source doesn't include one. If the source brings its own `.openskills.json`, the source version takes precedence.

### Recommendations

Skills can declare recommended companion skills via `recommends` in their `.openskills.json`:

```json
{
  "recommends": [
    {"name": "pdf", "source": "https://github.com/anthropics/skills/skills/pdf"}
  ]
}
```

- `openskills recommends check` — see which recommendations are satisfied or missing (with clickable source links)
- `openskills recommends tree` — display the full recommendation tree
- `openskills recommends install <skill>` — interactively select and install missing recommendations

Recommendations are also checked automatically after `openskills install`.

## Skill Search Directories

Skills are discovered in this priority order:

1. `.agents/skills` (project)
2. `.claude/skills` (project, backward compatible)
3. `~/.agents/skills` (global)
4. `~/.claude/skills` (global, backward compatible)

Default install target is `.agents/skills/` (project level). Use `--global` to install to `~/.agents/skills/`.

## Project Structure

```
openskills/
├── cli.py               # Click CLI group + all command definitions
├── models.py            # All data types (Skill, SkillSourceMetadata, etc.)
├── finder.py            # Skill discovery across directories
├── installer.py         # Install logic (git, local, market) with caching
├── updater.py           # Update skills + interactive source metadata prompt
├── remover.py           # Remove + interactive batch manage
├── recommends.py        # Recommendation dependency management
├── market.py            # Market data model, search, terminal/HTML display
├── metadata.py          # .openskills.json read/write
├── dirs.py              # Skill directory paths and cache directory
├── config.py            # market_sources.yaml loading
├── yaml_utils.py        # YAML frontmatter parsing
└── data/marketskills/   # Cached market skill data (JSON)
```

## Development Scripts

```
scripts/collect_market_skills.py   # Collect skill metadata from configured GitHub repos
market_sources.yaml                # Market source configuration (repos to harvest skills from)
```

## Testing

```bash
pip install pytest
pytest tests/ -v
```

238 tests covering all modules.

## Breaking Changes from v1

- Removed `sync`, `compat`, `read` commands
- Removed `--universal` install option
- Removed `.cline/skills` and `.clinerules/skills` from search paths
- Removed installer scripts (install_to_project.bat/sh, setup_env.bat/sh)
- Default install directory changed from `.claude/skills` to `.agents/skills`
- Minimum Python version raised to 3.11

## License

Apache License 2.0
