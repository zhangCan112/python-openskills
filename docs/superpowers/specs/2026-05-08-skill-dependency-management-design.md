# Skill Dependency Management Design

## Goal

Add dependency management to OpenSkills, enabling skills to declare dependencies on other skills. The system handles: automatic dependency installation, safe deletion with dependency checks, and dependency visualization.

## Design Decision: `.openskills.json` Extension

Dependencies are declared in `.openskills.json` (the existing installation metadata file). Skill authors optionally include a `.openskills.json` in the skill source with only `depends_on`. During installation, the installer preserves `depends_on` and fills in installation metadata.

**Why this approach:** No changes to SKILL.md format. Existing skills without `.openskills.json` are unaffected (treated as having no dependencies). Reuses the existing metadata read/write infrastructure in `metadata.py`.

---

## Data Model Changes

### `models.py` — New Types

```python
@dataclass
class SkillDependency:
    name: str
    source: str  # git URL, market name, or local path (same formats as `install` command)
```

### `models.py` — Extended `SkillSourceMetadata`

```python
@dataclass
class SkillSourceMetadata:
    source: str
    source_type: SkillSourceType
    repo_url: str | None = None
    subpath: str | None = None
    local_path: str | None = None
    installed_at: str | None = None
    depends_on: list[SkillDependency] | None = None  # NEW
```

### `.openskills.json` — Skill Author Format (source)

Skill authors create this file in the skill source directory with only the dependency declaration:

```json
{
  "depends_on": [
    {"name": "brainstorming", "source": "https://github.com/anthropics/skills/skills/brainstorming"}
  ]
}
```

`source` supports the same formats as the `install` command: git URL (with optional subpath), market name, or local path.

### `.openskills.json` — After Installation (runtime)

The installer preserves `depends_on` and adds installation metadata:

```json
{
  "source": "https://github.com/owner/repo/skills/writing-plans",
  "source_type": "git",
  "repo_url": "https://github.com/owner/repo",
  "subpath": "skills/writing-plans",
  "local_path": null,
  "installed_at": "2026-05-08T10:00:00.000000",
  "depends_on": [
    {"name": "brainstorming", "source": "https://github.com/anthropics/skills/skills/brainstorming"}
  ]
}
```

### Backwards Compatibility

- Existing skills without `.openskills.json` → no dependencies, fully compatible
- Existing skills with `.openskills.json` but no `depends_on` → `depends_on` field is `None`, fully compatible
- Old versions of OpenSkills ignore the unknown `depends_on` field when reading JSON

---

## Feature 1: Install with Auto-Dependency Pull

### Flow

Added as a post-install step in `installer.py`:

```
install_skill(source, options)
  │
  ├─ ... existing install flow ...
  │
  └─ After skill is installed:
      ├─ Read .openskills.json from installed skill
      ├─ If has depends_on:
      │   ├─ Resolve full dependency tree (recursive)
      │   │   ├─ For each dependency, check if installed (find_skill)
      │   │   ├─ If not installed, read its source .openskills.json for sub-dependencies
      │   │   └─ Detect circular dependencies (track "installing" set)
      │   │
      │   ├─ Collect all missing dependencies (flatten tree)
      │   ├─ If missing deps exist:
      │   │   ├─ Display confirmation:
      │   │   │   "The following dependencies will be installed:"
      │   │   │    - dep-name (from source)
      │   │   │   "Already installed:"
      │   │   │    - already-installed-dep
      │   │   │   "Install these dependencies? [Y/n]"
      │   │   │
      │   │   ├─ User confirms (or -y flag skips confirmation)
      │   │   │   ├─ Yes: recursively install each missing dependency
      │   │   │   └─ No: warn about unsatisfied dependencies, continue
      │   │   └─ No missing deps: "All dependencies satisfied."
      │   └─ Write full .openskills.json (install metadata + preserved depends_on)
```

### Confirmation Prompt Behavior

- List all dependencies that need to be newly installed
- List already-installed dependencies separately
- Default answer is `Y` (install)
- `-y` flag skips the prompt entirely
- If user declines, output warning: `Warning: skill "X" has unsatisfied dependencies. Run 'openskills deps check X' to see details.`

### Recursive Dependency Handling

- Dependencies of dependencies are resolved before confirmation
- All missing dependencies are shown in a single confirmation prompt
- Circular dependency detection: maintain a set of skills currently being installed; if a skill appears again, error out with a clear message

### Output Example

```
$ openskills install writing-plans
Installing writing-plans from https://github.com/owner/repo...
✓ writing-plans installed

Checking dependencies...
The following dependencies will be installed:
  - brainstorming (from https://github.com/anthropics/skills/skills/brainstorming)
  - writing-skills (from https://github.com/anthropics/skills/skills/writing-skills)

Already installed:
  - verification-before-completion

Install these dependencies? [Y/n] y
  Installing dependency: brainstorming
  ✓ brainstorming installed
  Installing dependency: writing-skills
  ✓ writing-skills installed

All dependencies satisfied.
```

---

## Feature 2: Delete with Dependency Check

### Flow

Added as a pre-delete check in `remover.py`:

```
remove_skill(skill_name)
  │
  ├─ Existing: find_skill → found location
  │
  ├─ NEW: Check for dependents
  │   ├─ Scan all installed skills' .openskills.json files
  │   ├─ For each skill with depends_on, check if any entry matches skill_name
  │   └─ Collect list of skills that depend on skill_name
  │
  ├─ If dependents found:
  │   ├─ Display warning with dependent skill list
  │   ├─ Prompt: "Removing 'X' will break these skills. Continue anyway? [y/N]"
  │   └─ Default is N (safe); must explicitly confirm to proceed
  │
  └─ If no dependents:
      └─ Delete directly (existing behavior)
```

### Output Example

```
$ openskills remove brainstorming
Warning: The following skills depend on "brainstorming":
  - writing-plans (project)
  - executing-plans (project)

Removing "brainstorming" will break these skills.
Continue anyway? [y/N] n
Aborted. "brainstorming" was not removed.
```

### Integration with `manage` Command

The `manage_skills()` interactive batch delete also applies dependency checks. When a user selects skills to delete, any that are depended on by other selected or non-selected skills show a warning before deletion.

---

## Feature 3: Dependency Visualization and Commands

### New Module: `dependency.py`

Core dependency resolution and query functions:

| Function | Purpose |
|----------|---------|
| `resolve_dependency_tree(skill_name)` | Resolve full transitive dependency tree for a skill |
| `check_dependencies(skill_name=None)` | Check if all dependencies are satisfied (all or single skill) |
| `get_dependents(skill_name)` | Reverse lookup: which installed skills depend on the given skill |
| `install_missing_dependencies(skill_name, options)` | Install only missing dependencies for an installed skill |

### New CLI Commands

```bash
openskills deps check [skill-name]     # Check dependency satisfaction
openskills deps tree [skill-name]      # Display dependency tree
openskills deps install <skill-name>   # Install missing dependencies for a skill
```

#### `deps check`

Without argument — check all installed skills:
```
$ openskills deps check
Checking dependencies for all skills...

✗ writing-plans has unsatisfied dependencies:
    - brainstorming (not installed)
    - writing-skills (not installed)

✓ executing-plans - all dependencies satisfied

Summary: 1 skill with issues, 1 skill OK
```

With argument — check specific skill:
```
$ openskills deps check writing-plans
✗ writing-plans has unsatisfied dependencies:
    - brainstorming (not installed)
```

#### `deps tree`

Without argument — show all skills' dependency trees:
```
$ openskills deps tree
brainstorming
writing-plans
  └── brainstorming
executing-plans
  ├── using-git-worktrees
  ├── writing-plans
  │   └── brainstorming
  └── finishing-a-development-branch
verification-before-completion
```

With argument — show subtree for specific skill:
```
$ openskills deps tree executing-plans
executing-plans
  ├── using-git-worktrees
  ├── writing-plans
  │   └── brainstorming
  └── finishing-a-development-branch
```

#### `deps install`

Install missing dependencies for an already-installed skill:
```
$ openskills deps install writing-plans
The following dependencies will be installed:
  - brainstorming (from https://github.com/anthropics/skills/skills/brainstorming)

Install these dependencies? [Y/n]
```

---

## File Changes Summary

| File | Change |
|------|--------|
| `models.py` | Add `SkillDependency` dataclass, add `depends_on` field to `SkillSourceMetadata` |
| `metadata.py` | Update `read_skill_metadata` to parse `depends_on`, update `write_skill_metadata` to serialize it |
| `installer.py` | Add post-install dependency resolution and installation with confirmation |
| `remover.py` | Add pre-delete dependency check with confirmation prompt |
| `dependency.py` | New module with `resolve_dependency_tree`, `check_dependencies`, `get_dependents`, `install_missing_dependencies` |
| `cli.py` | Add `deps` command group with `check`, `tree`, `install` subcommands |

---

## Testing Strategy

- Unit tests for `dependency.py` functions with mock skill directories
- Unit tests for `metadata.py` with `depends_on` field
- Integration tests for install flow with dependencies
- Integration tests for remove flow with dependency checks
- CLI tests for `deps` commands
- Edge cases: circular dependencies, missing dependency sources, self-dependency
