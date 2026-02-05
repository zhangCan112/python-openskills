# Skill Market Usage Guide

## Overview

The Skill Market feature allows maintainers to collect skill information from remote repositories and enables users to install these skills with simple commands.

## Maintainer Guide

### 1. Configure Source Repositories

Edit `market_sources.yaml` file to add repositories to collect from:

```yaml
sources:
  - repo: "https://github.com/owner/repo1"
    branch: "main"
  - repo: "https://github.com/owner/repo2"
    branch: "master"
```

**Important**: Repository URLs must be complete URLs. Short formats like `owner/repo` are not supported.

### 2. Collect Skills

Run the collection script to gather skill information from configured repositories:

```bash
python scripts/collect_market_skills.py
```

The script will:
- Clone configured repositories to a temporary directory
- Parse SKILL.md files from each repository
- Extract skill information (name, description, version, author, tags, etc.)
- Save to `marketskills/owner_repo.json` files

### 3. Update Market Data

When repositories have updates, simply rerun the collection script to update market data.

## User Guide

### 1. View Available Skills

#### List All Skills

```bash
openskills market list
```

#### Filter by Tags

Filter skills by tags:

```bash
# Single tag filter
openskills market list -t development

# Multiple tag filter (AND logic)
openskills market list -t development -t workflow
```

**Notes:**
- `-t` or `--tag` option can be used multiple times
- Multiple tags use AND logic (skill must contain all specified tags)
- Tag filtering is case-insensitive

### 2. Search Skills

Search for skills by keyword:

```bash
openskills market search <keyword>
```

Search scope includes: skill name, description, tags

### 3. Install Skills

#### Method 1: Install by Skill Name

If you know the skill name, use it directly:

```bash
openskills install <skill-name>
```

The system will:
- Search for the skill in the market
- If a unique skill is found, install it directly
- If multiple skills with the same name are found, display options for you to choose

#### Method 2: Install by URL

The original installation methods are still supported:

```bash
openskills install https://github.com/owner/repo
openskills install https://github.com/owner/repo/skill-path
openskills install git@github.com:owner/repo.git
```

**Important**: Git repository URLs must be complete. Short formats like `owner/repo` or `github.com/owner/repo` are not supported.

## File Structure

```
python-openskills/
├── market_sources.yaml           # Market source configuration (edited by maintainer)
├── marketskills/                  # Market data directory
│   ├── owner_repo1.json          # Skills from repository 1
│   └── owner_repo2.json          # Skills from repository 2
├── scripts/
│   └── collect_market_skills.py  # Collection script (used by maintainer)
└── openskills/
    ├── utils/
    │   └── market.py            # Market data management
    └── commands/
        └── market.py             # Market commands
```

## Important Notes

1. **Market Data Updates**: Maintainers need to rerun the collection script after repository updates
2. **Duplicate Skills**: When multiple repositories have skills with the same name, installation will display options for user selection
3. **Git Requirement**: The collection script requires git to be installed on the system
4. **Temporary Files**: The collection process creates temporary directories which are automatically cleaned up by the script

## Examples

### Maintainer Operations

```bash
# 1. Edit market_sources.yaml to add repositories
vim market_sources.yaml

# 2. Run collection script
python scripts/collect_market_skills.py

# Output example:
# ============================================================
# Market Skills Collector
# ============================================================
#
# Found 2 source(s) to process
#
# 📦 Collecting from: owner/repo1
#   Found 3 skill(s):
#     - skill-a (root)
#     - skill-b (at 'skills/skill-b')
#     - skill-c (at 'skills/skill-c')
#   ✓ Saved 3 skill(s) to owner_repo1.json
#
# ============================================================
# Collection complete: 2/2 source(s) processed
# Market skills saved to: marketskills/
# ============================================================
```

### User Operations

```bash
# 1. View all available skills
openskills market list

# 2. Search for a specific skill
openskills market search pdf

# 3. Install skill
openskills install pdf-reader

# 4. If there are skills with the same name, options will be displayed:
# Found multiple skills named 'pdf-reader':
#
# 1. pdf-reader
#    Source: owner/repo1
#    Description: A skill for reading PDF files
#    Author: Author1
#
# 2. pdf-reader
#    Source: owner/repo2
#    Description: Another PDF reading skill
#    Author: Author2
#
# Select which skill to install [1-2]: 1
```

## Troubleshooting

### Collection Script Fails

- Ensure git is installed on the system
- Check if repository URLs are correct
- Check network connection

### Skill Not Found

- Run `openskills market list` to confirm the skill exists in the market
- Check spelling of skill name
- Try using the search function

### Installation Fails

- Ensure write permissions
- Check disk space
- View error messages for more details