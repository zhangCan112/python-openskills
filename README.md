# OpenSkills

A Python CLI tool for managing AI coding agent skills (SKILL.md format). Handles the full lifecycle: discover, install, update, and remove.

## Installation

```bash
pip install .
# or from git
pip install git+https://github.com/zhangCan112/python-openskills
```

Requires Python 3.8+.

## CLI Commands

```
openskills list                          # List all installed skills
openskills install <source>              # Install from git URL / local path / market name
       [--global]                        #   Install to global directory
       [--yes / -y]                      #   Skip interactive confirmation
openskills update [skill1 skill2 ...]    # Update skills (default: all)
openskills remove <skill>                # Remove a single skill
openskills rm <skill>                    # Alias for remove
openskills manage                        # Interactive batch management (remove)
openskills market list [--tag <tag>]     # List market skills
                        [--html]         #   HTML format (open in browser)
openskills market search <keyword>       # Search market skills
openskills --version                     # Show version
```

Install sources:

```bash
# From git URL (HTTPS or SSH)
openskills install https://github.com/owner/repo
openskills install git@github.com:owner/repo.git

# From local path
openskills install ./local-skill

# From market name
openskills install <market-name>
```

## Skill Search Directories

Skills are discovered in this priority order:

1. `.agent/skills` (project)
2. `.claude/skills` (project)
3. `~/.agent/skills` (global)
4. `~/.claude/skills` (global)

## Project Structure

```
openskills/
├── __init__.py          # Package version
├── __main__.py          # python -m openskills entry point
├── cli.py               # Click CLI group + all command definitions
├── models.py            # All data types
├── finder.py            # Skill discovery
├── installer.py         # Install logic (git, local, market)
├── updater.py           # Update logic
├── remover.py           # Remove + interactive manage
├── market.py            # Market data model + search + HTML generation
├── metadata.py          # .openskills.json read/write
├── dirs.py              # Skill directory paths
├── config.py            # market_sources.yaml loading
├── yaml_utils.py        # YAML frontmatter parsing
└── data/marketskills/   # Cached market skill data
```

## Breaking Changes from v1

- Removed `sync`, `compat`, `read` commands
- Removed `--universal` install option
- Removed `.cline/skills` and `.clinerules/skills` from search paths
- Removed installer scripts (install_to_project.bat/sh, setup_env.bat/sh)

## License

Apache License 2.0
