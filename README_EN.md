# OpenSkills Python Version

OpenSkills Python implementation - A universal AI coding agent skill loader for installing and managing Anthropic SKILL.md format skills.

## Installation

This project provides two installation methods:

### Method 1: Install to Target Project (Recommended) ⭐

Install OpenSkills to any target project. It automatically creates a virtual environment and configures it without affecting the target project's git:

```bash
# Windows
install_to_project.bat C:\path\to\your\project

# Linux/Mac
bash install_to_project.sh /path/to/your/project
```

**The script will automatically complete the following:**
1. Create a virtual environment `.venv` in the target project
2. Install OpenSkills into the virtual environment
3. Automatically add `.venv` to `.gitignore` (won't be committed to git)
4. Create a convenient startup script `openskills.bat` (Windows) or `openskills.sh` (Linux/Mac)

**Usage:**
```bash
# Method 1: Use after activating virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
openskills --help

# Method 2: Use quick script (more convenient)
openskills.bat --help  # Windows
./openskills.sh --help  # Linux/Mac
```

**Advantages:**
- ✅ Environment isolation, doesn't affect other projects
- ✅ Automatically configures .gitignore, won't commit to git
- ✅ Provides convenient startup script
- ✅ Independent dependency management for each project

### Method 2: Direct Use (No Installation Required)

No installation needed. Use Python module directly, suitable for quick testing:

```bash
# View help
python -m openskills.cli --help

# List installed skills
python -m openskills.cli list

# Install skill
python -m openskills.cli install anthropics/skills
```

**Suitable for:**
- Quick experience and testing
- Temporary usage
- Don't want to create virtual environment

## Dependencies

- Python 3.8+
- click >= 8.1.0
- questionary >= 2.0.0

## Usage

The command format varies slightly depending on your chosen installation method:

- **Method 1 (Install to Project)**: Use `openskills` command after activating virtual environment, or use quick script
- **Method 2 (Direct Use)**: Use `python -m openskills.cli` prefix

The following examples use the `openskills` command. If using Method 2, add `python -m openskills.cli` before the command.

### List Installed Skills

```bash
openskills list

# If using Method 2, use:
python -m openskills.cli list
```

### Install Skills

Install from GitHub repository:

```bash
# Install to project directory (default)
openskills install anthropics/skills

# Install to global directory
openskills install owner/skill --global

# Install to .agent/skills (for universal AGENTS.md)
openskills install owner/skill --universal

# Skip interactive selection, install all found skills
openskills install owner/skill --yes

# If using Method 2, add python -m openskills.cli before command
# Example: python -m openskills.cli install anthropics/skills
```

Install from local path:

```bash
openskills install ./local-skill
openskills install ~/my-skills/skill-name
```

Install from full Git URL:

```bash
openskills install https://github.com/owner/repo.git
openskills install git@github.com:owner/repo.git
```

### Read Skill Content

```bash
# Read single skill
openskills read skill-name

# Read multiple skills
openskills read skill-one skill-two

# Use comma separation
openskills read skill-one,skill-two

# If using Method 2, add python -m openskills.cli before command
```

### Update Skills

```bash
# Update all installed skills
openskills update

# Update specific skills
openskills update skill-name skill-two

# If using Method 2, add python -m openskills.cli before command
```

### Sync to AGENTS.md

```bash
# Interactive sync (pre-select current status)
openskills sync

# Skip interaction, sync all skills
openskills sync --yes

# Specify output file
openskills sync --output CUSTOM.md

# If using Method 2, add python -m openskills.cli before command
```

### Manage Skills (Interactive Delete)

```bash
openskills manage

# If using Method 2, add python -m openskills.cli before command
```

### Remove Specific Skill

```bash
openskills remove skill-name

# Or use alias
openskills rm skill-name

# If using Method 2, add python -m openskills.cli before command
```

## Skill Directory Structure

OpenSkills looks for skills in the following locations (in priority order):

1. `./.agent/skills` - Project universal (.agent)
2. `~/.agent/skills` - Global universal (.agent)
3. `./.claude/skills` - Project Claude
4. `~/.claude/skills` - Global Claude

## Quick Reference

| Operation | Install to Project (Method 1) | Direct Use (Method 2) |
|-----------|------------------------------|----------------------|
| View Help | `openskills.bat --help`<br>`./openskills.sh --help` | `python -m openskills.cli --help` |
| List Skills | `openskills.bat list`<br>`./openskills.sh list` | `python -m openskills.cli list` |
| Install Skill | `openskills.bat install <skill>`<br>`./openskills.sh install <skill>` | `python -m openskills.cli install <skill>` |
| Read Skill | `openskills.bat read <skill>`<br>`./openskills.sh read <skill>` | `python -m openskills.cli read <skill>` |
| Update Skills | `openskills.bat update`<br>`./openskills.sh update` | `python -m openskills.cli update` |
| Sync Skills | `openskills.bat sync`<br>`./openskills.sh sync` | `python -m openskills.cli sync` |
| Manage Skills | `openskills.bat manage`<br>`./openskills.sh manage` | `python -m openskills.cli manage` |
| Remove Skill | `openskills.bat remove <skill>`<br>`./openskills.sh remove <skill>` | `python -m openskills.cli remove <skill>` |

## Differences from TypeScript Version

The Python version implements the same core functionality as the TypeScript version but uses a different tech stack:

- **CLI Framework**: Uses Click (Python) instead of Commander (TypeScript)
- **Interactive Prompts**: Uses questionary (Python) instead of @inquirer/prompts (TypeScript)
- **Terminal Styling**: Uses Click's styling features instead of chalk (TypeScript)

All command parameters and behaviors remain consistent, ensuring seamless migration.

## Development

### Run Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run CLI
python -m openskills.cli --help
```

### Project Structure

```
python-openskills/
├── openskills/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── types.py            # Type definitions
│   ├── commands/           # Command modules
│   │   ├── install.py
│   │   ├── list.py
│   │   ├── read.py
│   │   ├── remove.py
│   │   ├── update.py
│   │   ├── sync.py
│   │   └── manage.py
│   └── utils/             # Utility modules
│       ├── dirs.py
│       ├── yaml.py
│       ├── skills.py
│       ├── skill_metadata.py
│       ├── agents_md.py
│       └── marketplace_skills.py
├── install_to_project.bat  # Install to project script (Windows)
├── install_to_project.sh   # Install to project script (Linux/Mac)
├── setup.py
└── README.md
```

## License

Apache License 2.0

## Contributing

Contributions welcome! Please refer to the main project's CONTRIBUTING.md file.

## Original Project

This is the Python implementation of the [OpenSkills](https://github.com/numman-ali/openskills) project.