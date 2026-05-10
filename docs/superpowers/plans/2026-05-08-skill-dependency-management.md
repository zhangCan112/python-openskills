# Skill Dependency Management Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dependency management to OpenSkills: auto-pull deps on install, safe deletion with dep checks, and `deps` CLI commands for visualization.

**Architecture:** Extend `.openskills.json` with `depends_on` field. New `dependency.py` module handles resolution and queries. Installer and remover get pre/post hooks. New `deps` CLI group exposes check/tree/install commands.

**Tech Stack:** Python 3.11+, Click, pytest, dataclasses

**Spec:** `docs/superpowers/specs/2026-05-08-skill-dependency-management-design.md`

---

## Chunk 1: Data Layer

### Task 1: Add SkillDependency model and extend SkillSourceMetadata

**Files:**
- Modify: `openskills/models.py:1-43`
- Modify: `tests/test_models.py:1-100`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
from openskills.models import SkillDependency


def test_skill_dependency_creation():
    dep = SkillDependency(name="brainstorming", source="https://github.com/owner/repo/skills/brainstorming")
    assert dep.name == "brainstorming"
    assert dep.source == "https://github.com/owner/repo/skills/brainstorming"


def test_skill_source_metadata_depends_on_default():
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
    )
    assert meta.depends_on is None


def test_skill_source_metadata_with_depends_on():
    deps = [
        SkillDependency(name="brainstorming", source="https://github.com/anthropics/skills/skills/brainstorming"),
        SkillDependency(name="writing-plans", source="superpowers"),
    ]
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
        depends_on=deps,
    )
    assert meta.depends_on is not None
    assert len(meta.depends_on) == 2
    assert meta.depends_on[0].name == "brainstorming"
    assert meta.depends_on[1].source == "superpowers"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py::test_skill_dependency_creation tests/test_models.py::test_skill_source_metadata_depends_on_default tests/test_models.py::test_skill_source_metadata_with_depends_on -v`
Expected: FAIL (ImportError: cannot import name 'SkillDependency')

- [ ] **Step 3: Write minimal implementation**

Add to `openskills/models.py` after line 13 (after `SkillSourceType` class):

```python
@dataclass
class SkillDependency:
    name: str
    source: str
```

Add `depends_on` field to `SkillSourceMetadata` (after line 37, before `installed_at`):

```python
    depends_on: list['SkillDependency'] | None = None
```

Update the import in `tests/test_models.py` line 1 to include `SkillDependency`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add openskills/models.py tests/test_models.py
git commit -m "feat: add SkillDependency model and depends_on to SkillSourceMetadata"
```

---

### Task 2: Update metadata.py to handle depends_on

**Files:**
- Modify: `openskills/metadata.py:1-37`
- Modify: `tests/test_metadata.py:1-97`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_metadata.py`:

```python
from openskills.models import SkillDependency


def test_read_skill_metadata_with_depends_on(tmp_path):
    data = {
        "source": "https://github.com/example/repo",
        "source_type": "git",
        "depends_on": [
            {"name": "brainstorming", "source": "https://github.com/anthropics/skills/skills/brainstorming"}
        ],
    }
    tmp_path.joinpath(".openskills.json").write_text(json.dumps(data))
    result = read_skill_metadata(str(tmp_path))
    assert result is not None
    assert result.depends_on is not None
    assert len(result.depends_on) == 1
    assert result.depends_on[0].name == "brainstorming"


def test_read_skill_metadata_without_depends_on(tmp_path):
    data = {
        "source": "https://github.com/example/repo",
        "source_type": "git",
    }
    tmp_path.joinpath(".openskills.json").write_text(json.dumps(data))
    result = read_skill_metadata(str(tmp_path))
    assert result is not None
    assert result.depends_on is None


def test_write_skill_metadata_with_depends_on(tmp_path):
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
        depends_on=[
            SkillDependency(name="brainstorming", source="https://github.com/anthropics/skills/skills/brainstorming"),
        ],
    )
    write_skill_metadata(str(tmp_path), meta)
    data = json.loads(tmp_path.joinpath(".openskills.json").read_text())
    assert "depends_on" in data
    assert data["depends_on"][0]["name"] == "brainstorming"


def test_write_skill_metadata_without_depends_on(tmp_path):
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
    )
    write_skill_metadata(str(tmp_path), meta)
    data = json.loads(tmp_path.joinpath(".openskills.json").read_text())
    assert data.get("depends_on") is None


def test_depends_on_roundtrip(tmp_path):
    deps = [
        SkillDependency(name="brainstorming", source="https://github.com/anthropics/skills/skills/brainstorming"),
        SkillDependency(name="writing-plans", source="superpowers"),
    ]
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
        depends_on=deps,
    )
    write_skill_metadata(str(tmp_path), meta)
    result = read_skill_metadata(str(tmp_path))
    assert result is not None
    assert result.depends_on is not None
    assert len(result.depends_on) == 2
    assert result.depends_on[0].name == "brainstorming"
    assert result.depends_on[1].source == "superpowers"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_metadata.py::test_read_skill_metadata_with_depends_on tests/test_metadata.py::test_write_skill_metadata_with_depends_on -v`
Expected: FAIL (depends_on not parsed/serialized)

- [ ] **Step 3: Write minimal implementation**

Update `openskills/metadata.py`:

In `read_skill_metadata`, after constructing `SkillSourceMetadata`, add depends_on parsing:

```python
def read_skill_metadata(skill_dir: str) -> SkillSourceMetadata | None:
    metadata_path = os.path.join(skill_dir, SKILL_METADATA_FILE)

    if not os.path.exists(metadata_path):
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
            depends_on = None
            if 'depends_on' in data and data['depends_on']:
                from openskills.models import SkillDependency
                depends_on = [SkillDependency(**d) for d in data['depends_on']]
            return SkillSourceMetadata(
                source=data['source'],
                source_type=data['source_type'],
                repo_url=data.get('repo_url'),
                subpath=data.get('subpath'),
                local_path=data.get('local_path'),
                installed_at=data.get('installed_at'),
                depends_on=depends_on,
            )
    except Exception:
        return None
```

In `write_skill_metadata`, add depends_on to the payload:

```python
def write_skill_metadata(skill_dir: str, metadata: SkillSourceMetadata) -> None:
    metadata_path = os.path.join(skill_dir, SKILL_METADATA_FILE)

    payload = {
        'source': metadata.source,
        'source_type': metadata.source_type,
        'repo_url': metadata.repo_url,
        'subpath': metadata.subpath,
        'local_path': metadata.local_path,
        'installed_at': metadata.installed_at or datetime.now().isoformat(),
    }

    if metadata.depends_on is not None:
        payload['depends_on'] = [
            {'name': d.name, 'source': d.source} for d in metadata.depends_on
        ]

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_metadata.py -v`
Expected: PASS

- [ ] **Step 5: Run all existing tests**

Run: `python -m pytest tests/ -v`
Expected: PASS (no regressions)

- [ ] **Step 6: Commit**

```bash
git add openskills/metadata.py tests/test_metadata.py
git commit -m "feat: handle depends_on in metadata read/write"
```

---

## Chunk 2: Dependency Resolution Core

### Task 3: Create dependency.py with core resolution functions

**Files:**
- Create: `openskills/dependency.py`
- Create: `tests/test_dependency.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_dependency.py`:

```python
import json
import os

import pytest

from openskills.dependency import (
    resolve_dependency_tree,
    check_dependencies,
    get_dependents,
)
from openskills.metadata import write_skill_metadata
from openskills.models import SkillDependency, SkillSourceMetadata, SkillSourceType


def _create_skill(base_dir, name, depends_on=None):
    skill_dir = os.path.join(base_dir, name)
    os.makedirs(skill_dir, exist_ok=True)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    skill_md_content = f"---\nname: {name}\ndescription: Test skill {name}\n---\n"
    with open(skill_md, 'w', encoding='utf-8') as f:
        f.write(skill_md_content)

    metadata = SkillSourceMetadata(
        source=f"https://github.com/test/repo/skills/{name}",
        source_type=SkillSourceType.GIT,
        depends_on=depends_on,
    )
    write_skill_metadata(skill_dir, metadata)
    return skill_dir


class TestResolveDependencyTree:
    def test_no_dependencies(self, tmp_path):
        _create_skill(str(tmp_path), "solo")
        result = resolve_dependency_tree(str(tmp_path / "solo"))
        assert result == {"name": "solo", "deps": []}

    def test_single_dependency(self, tmp_path):
        _create_skill(str(tmp_path), "child", depends_on=[
            SkillDependency(name="parent", source="https://github.com/test/repo/skills/parent"),
        ])
        _create_skill(str(tmp_path), "parent")
        result = resolve_dependency_tree(str(tmp_path / "child"))
        assert result["name"] == "child"
        assert len(result["deps"]) == 1
        assert result["deps"][0]["name"] == "parent"

    def test_transitive_dependencies(self, tmp_path):
        _create_skill(str(tmp_path), "grandchild", depends_on=[
            SkillDependency(name="child", source="test"),
        ])
        _create_skill(str(tmp_path), "child", depends_on=[
            SkillDependency(name="root", source="test"),
        ])
        _create_skill(str(tmp_path), "root")
        result = resolve_dependency_tree(str(tmp_path / "grandchild"))
        assert result["name"] == "grandchild"
        assert len(result["deps"]) == 1
        child_dep = result["deps"][0]
        assert child_dep["name"] == "child"
        assert len(child_dep["deps"]) == 1
        assert child_dep["deps"][0]["name"] == "root"

    def test_circular_dependency_raises(self, tmp_path):
        _create_skill(str(tmp_path), "a", depends_on=[
            SkillDependency(name="b", source="test"),
        ])
        _create_skill(str(tmp_path), "b", depends_on=[
            SkillDependency(name="a", source="test"),
        ])
        with pytest.raises(ValueError, match="[Cc]ircular"):
            resolve_dependency_tree(str(tmp_path / "a"))

    def test_missing_dependency_metadata(self, tmp_path):
        _create_skill(str(tmp_path), "orphan", depends_on=[
            SkillDependency(name="missing", source="test"),
        ])
        result = resolve_dependency_tree(str(tmp_path / "orphan"))
        assert result["name"] == "orphan"
        assert len(result["deps"]) == 1
        assert result["deps"][0]["name"] == "missing"
        assert result["deps"][0]["deps"] == []


class TestCheckDependencies:
    def test_all_satisfied(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", depends_on=[
            SkillDependency(name="parent", source="test"),
        ])
        _create_skill(str(tmp_path), "parent")
        monkeypatch.setattr('openskills.dependency.find_all_skills', lambda: [])
        monkeypatch.setattr('openskills.dependency.find_skill', lambda n: (
            type('obj', (object,), {'base_dir': str(tmp_path / n)})() if os.path.exists(str(tmp_path / n)) else None
        ))
        results = check_dependencies(str(tmp_path / "child"))
        assert len(results["missing"]) == 0
        assert len(results["satisfied"]) == 1

    def test_missing_dependency(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", depends_on=[
            SkillDependency(name="parent", source="test"),
        ])
        monkeypatch.setattr('openskills.dependency.find_all_skills', lambda: [])
        monkeypatch.setattr('openskills.dependency.find_skill', lambda n: None)
        results = check_dependencies(str(tmp_path / "child"))
        assert len(results["missing"]) == 1
        assert results["missing"][0].name == "parent"


class TestGetDependents:
    def test_no_dependents(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "solo")
        monkeypatch.setattr('openskills.dependency.find_all_skills', lambda: [
            type('obj', (object,), {'name': 'solo', 'path': str(tmp_path / 'solo')})()
        ])
        result = get_dependents("target")
        assert result == []

    def test_has_dependents(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", depends_on=[
            SkillDependency(name="parent", source="test"),
        ])
        _create_skill(str(tmp_path), "parent")
        monkeypatch.setattr('openskills.dependency.find_all_skills', lambda: [
            type('obj', (object,), {'name': 'child', 'path': str(tmp_path / 'child')})(),
            type('obj', (object,), {'name': 'parent', 'path': str(tmp_path / 'parent')})(),
        ])
        result = get_dependents("parent")
        assert len(result) == 1
        assert result[0]["name"] == "child"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dependency.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'openskills.dependency')

- [ ] **Step 3: Write minimal implementation**

Create `openskills/dependency.py`:

```python
from openskills.metadata import read_skill_metadata
from openskills.models import SkillDependency
from openskills.finder import find_all_skills, find_skill


def resolve_dependency_tree(skill_dir: str, _visiting: set | None = None) -> dict:
    if _visiting is None:
        _visiting = set()

    skill_name = _dir_name(skill_dir)
    if skill_name in _visiting:
        raise ValueError(f"Circular dependency detected: {skill_name}")

    _visiting = _visiting | {skill_name}

    metadata = read_skill_metadata(skill_dir)
    deps = []

    if metadata and metadata.depends_on:
        for dep in metadata.depends_on:
            dep_info = find_skill(dep.name)
            if dep_info:
                sub_tree = resolve_dependency_tree(dep_info.base_dir, _visiting)
                sub_tree["source"] = dep.source
                deps.append(sub_tree)
            else:
                deps.append({"name": dep.name, "source": dep.source, "deps": []})

    return {"name": skill_name, "deps": deps}


def check_dependencies(skill_dir: str) -> dict:
    metadata = read_skill_metadata(skill_dir)

    if not metadata or not metadata.depends_on:
        return {"missing": [], "satisfied": []}

    missing = []
    satisfied = []

    for dep in metadata.depends_on:
        if find_skill(dep.name):
            satisfied.append(dep)
        else:
            missing.append(dep)

    return {"missing": missing, "satisfied": satisfied}


def get_dependents(skill_name: str) -> list[dict]:
    all_skills = find_all_skills()
    dependents = []

    for skill in all_skills:
        metadata = read_skill_metadata(skill.path)
        if metadata and metadata.depends_on:
            for dep in metadata.depends_on:
                if dep.name == skill_name:
                    dependents.append({"name": skill.name, "location": skill.location})
                    break

    return dependents


def _dir_name(path: str) -> str:
    import os
    return os.path.basename(os.path.normpath(path))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_dependency.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add openskills/dependency.py tests/test_dependency.py
git commit -m "feat: add dependency.py with resolve, check, and dependents functions"
```

---

## Chunk 3: Installer and Remover Integration

### Task 4: Add post-install dependency resolution to installer

**Files:**
- Modify: `openskills/installer.py:1-569`
- Modify: `tests/test_installer.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_installer.py`:

```python
from openskills.metadata import read_skill_metadata


class TestInstallDependencies:
    def test_install_skill_processes_depends_on(self, tmp_path, monkeypatch, capsys):
        source_skill = tmp_path / "source" / "my-skill"
        source_skill.mkdir(parents=True)
        (source_skill / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: test\n---\n", encoding="utf-8"
        )
        dep_json = {"depends_on": [{"name": "dep-skill", "source": "https://github.com/test/repo/skills/dep-skill"}]}
        (source_skill / ".openskills.json").write_text(json.dumps(dep_json), encoding="utf-8")

        install_dir = tmp_path / "target" / "skills"
        install_dir.mkdir(parents=True)

        installed_called = []

        def mock_install_skill(source, options):
            installed_called.append(source)

        monkeypatch.setattr("openskills.installer.install_skill", mock_install_skill)
        monkeypatch.setattr("openskills.installer.find_skill", lambda n: None)
        monkeypatch.setattr("openskills.installer.is_local_path", lambda s: True)
        monkeypatch.setattr("openskills.installer.is_git_url", lambda s: False)
        monkeypatch.setattr("openskills.installer.expand_path", lambda s: s if os.path.isabs(s) else str(tmp_path / "source" / "my-skill"))
        monkeypatch.setattr("openskills.installer.warn_if_conflict", lambda *a, **kw: True)
        monkeypatch.setattr("openskills.installer.is_path_inside", lambda *a: True)
        monkeypatch.setattr("openskills.installer.print_post_install_hints", lambda *a: None)
        monkeypatch.setattr("openskills.installer.get_skills_dir", lambda *a: str(install_dir))
        monkeypatch.setattr(click, "confirm", lambda *a, **kw: True)

        from openskills.dependency import resolve_dependency_tree
        monkeypatch.setattr("openskills.dependency.resolve_dependency_tree", lambda sd: {
            "name": "my-skill", "deps": [{"name": "dep-skill", "source": "https://github.com/test/repo/skills/dep-skill", "deps": []}]
        })

    def test_resolve_dependencies_collects_missing(self, tmp_path, monkeypatch):
        from openskills.installer import _resolve_missing_deps

        tree = {
            "name": "a",
            "deps": [
                {"name": "b", "source": "url-b", "deps": [
                    {"name": "c", "source": "url-c", "deps": []}
                ]},
                {"name": "d", "source": "url-d", "deps": []},
            ],
        }

        installed = {"d"}

        def mock_find(name):
            return type('obj', (object,), {'base_dir': '/fake'})() if name in installed else None

        monkeypatch.setattr("openskills.installer.find_skill", mock_find)
        missing = _resolve_missing_deps(tree)
        assert len(missing) == 2
        names = [d["name"] for d in missing]
        assert "b" in names
        assert "c" in names
        assert "d" not in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_installer.py::TestInstallDependencies -v`
Expected: FAIL (ImportError or AttributeError)

- [ ] **Step 3: Write minimal implementation**

Add to `openskills/installer.py` imports:

```python
from openskills.dependency import resolve_dependency_tree
```

Add helper functions before `install_skill`:

```python
def _resolve_missing_deps(tree: dict) -> list[dict]:
    missing = []
    _collect_missing(tree, missing)
    return missing


def _collect_missing(tree: dict, missing: list[dict]) -> None:
    for dep in tree.get("deps", []):
        if not find_skill(dep["name"]):
            missing.append({"name": dep["name"], "source": dep.get("source", "")})
        _collect_missing(dep, missing)


def _install_dependencies(skill_dir: str, options: InstallOptions) -> None:
    try:
        tree = resolve_dependency_tree(skill_dir)
    except ValueError as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        return

    missing = _resolve_missing_deps(tree)
    if not missing:
        click.echo(click.style("All dependencies satisfied.", fg='green'))
        return

    click.echo(f"\n{click.style('Checking dependencies...', bold=True)}")
    click.echo(click.style("The following dependencies will be installed:", bold=True))
    for dep in missing:
        click.echo(f"  - {dep['name']} (from {dep['source']})")

    satisfied = []
    for dep in tree.get("deps", []):
        if find_skill(dep["name"]):
            satisfied.append(dep["name"])

    if satisfied:
        click.echo(click.style("\nAlready installed:", dim=True))
        for name in satisfied:
            click.echo(f"  - {name}")

    if not options.yes:
        if not click.confirm("\nInstall these dependencies?", default=True):
            click.echo(click.style(
                f"Warning: skill has unsatisfied dependencies. "
                f"Run 'openskills deps check' to see details.", fg='yellow'
            ))
            return

    for dep in missing:
        click.echo(f"  Installing dependency: {click.style(dep['name'], bold=True)}")
        install_skill(dep['source'], options)
        click.echo(click.style(f"  ✓ {dep['name']} installed", fg='green'))

    click.echo(click.style("\nAll dependencies satisfied.", fg='green'))
```

Now integrate into the three install endpoints. At the end of `install_from_repo` (after line 314), `_install_from_subpath` (after line 569), and `install_single_local_skill` (after line 358), add:

```python
    _install_dependencies(target_path, options)
```

Where `target_path` is the installed skill directory in each function.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_installer.py::TestInstallDependencies -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add openskills/installer.py tests/test_installer.py
git commit -m "feat: auto-install skill dependencies with confirmation"
```

---

### Task 5: Add pre-delete dependency check to remover

**Files:**
- Modify: `openskills/remover.py:35-47`
- Create: `tests/test_remover.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_remover.py`:

```python
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from openskills.remover import remove_skill


class TestRemoveWithDependencies:
    def test_remove_with_no_dependents(self, monkeypatch):
        mock_find = MagicMock(return_value=MagicMock(base_dir="/fake/skill", source="/project"))
        mock_dependents = MagicMock(return_value=[])
        monkeypatch.setattr("openskills.remover.find_skill", mock_find)
        monkeypatch.setattr("openskills.remover.get_dependents", mock_dependents)
        monkeypatch.patch("shutil.rmtree", lambda *a, **kw: None)
        with patch("shutil.rmtree"):
            remove_skill("solo-skill")
        mock_dependents.assert_called_once_with("solo-skill")

    def test_remove_with_dependents_user_confirms(self, monkeypatch):
        mock_find = MagicMock(return_value=MagicMock(base_dir="/fake/skill", source="/project"))
        mock_dependents = MagicMock(return_value=[
            {"name": "child-skill", "location": "project"},
        ])
        monkeypatch.setattr("openskills.remover.find_skill", mock_find)
        monkeypatch.setattr("openskills.remover.get_dependents", mock_dependents)
        with patch("openskills.remover.click.confirm", return_value=True), \
             patch("shutil.rmtree"):
            remove_skill("parent-skill")

    def test_remove_with_dependents_user_declines(self, monkeypatch):
        mock_find = MagicMock(return_value=MagicMock(base_dir="/fake/skill", source="/project"))
        mock_dependents = MagicMock(return_value=[
            {"name": "child-skill", "location": "project"},
        ])
        monkeypatch.setattr("openskills.remover.find_skill", mock_find)
        monkeypatch.setattr("openskills.remover.get_dependents", mock_dependents)
        with patch("openskills.remover.click.confirm", return_value=False), \
             patch("shutil.rmtree") as mock_rm:
            remove_skill("parent-skill")
            mock_rm.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_remover.py -v`
Expected: FAIL (ImportError: cannot import name 'get_dependents')

- [ ] **Step 3: Write minimal implementation**

Update `openskills/remover.py` imports:

```python
from openskills.dependency import get_dependents
```

Update `remove_skill` function:

```python
def remove_skill(skill_name: str) -> None:
    skill = find_skill(skill_name)

    if not skill:
        click.echo(f"Error: Skill '{skill_name}' not found", err=True)
        sys.exit(1)

    dependents = get_dependents(skill_name)
    if dependents:
        click.echo(click.style(f"Warning: The following skills depend on \"{skill_name}\":", fg='yellow'))
        for dep in dependents:
            click.echo(f"  - {dep['name']} ({dep['location']})")
        click.echo()
        if not click.confirm(
            click.style(f"Removing \"{skill_name}\" will break these skills. Continue anyway?", fg='yellow'),
            default=False
        ):
            click.echo(click.style(f"Aborted. \"{skill_name}\" was not removed.", fg='yellow'))
            return

    shutil.rmtree(skill.base_dir, ignore_errors=True)

    location = 'global' if str(Path.home()) in skill.source else 'project'
    click.echo(f"✅ Removed: {skill_name}")
    click.echo(f"   From: {location} ({skill.source})")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_remover.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add openskills/remover.py tests/test_remover.py
git commit -m "feat: warn when removing skills that others depend on"
```

---

## Chunk 4: CLI Commands

### Task 6: Add `deps` command group to CLI

**Files:**
- Modify: `openskills/cli.py:1-125`
- Modify: `tests/test_cli.py:1-130`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_cli.py`:

```python
def test_deps_check_no_args(monkeypatch):
    mock_check = MagicMock(return_value=[])
    monkeypatch.setattr('openskills.cli.check_all_dependencies', mock_check)
    runner = CliRunner()
    result = runner.invoke(cli, ['deps', 'check'])
    assert result.exit_code == 0


def test_deps_check_with_skill(monkeypatch):
    mock_check = MagicMock(return_value={"missing": [], "satisfied": []})
    monkeypatch.setattr('openskills.cli.check_skill_dependencies', mock_check)
    monkeypatch.setattr('openskills.cli.find_skill', MagicMock(return_value=MagicMock(base_dir='/fake')))
    runner = CliRunner()
    result = runner.invoke(cli, ['deps', 'check', 'my-skill'])
    assert result.exit_code == 0


def test_deps_tree_no_args(monkeypatch):
    mock_tree = MagicMock(return_value=[])
    monkeypatch.setattr('openskills.cli.build_all_dependency_trees', mock_tree)
    runner = CliRunner()
    result = runner.invoke(cli, ['deps', 'tree'])
    assert result.exit_code == 0


def test_deps_tree_with_skill(monkeypatch):
    mock_tree = MagicMock(return_value={"name": "test", "deps": []})
    monkeypatch.setattr('openskills.cli.resolve_dependency_tree', mock_tree)
    monkeypatch.setattr('openskills.cli.find_skill', MagicMock(return_value=MagicMock(base_dir='/fake')))
    runner = CliRunner()
    result = runner.invoke(cli, ['deps', 'tree', 'my-skill'])
    assert result.exit_code == 0


def test_deps_install_with_skill(monkeypatch):
    mock_install = MagicMock()
    monkeypatch.setattr('openskills.cli.install_missing_dependencies', mock_install)
    monkeypatch.setattr('openskills.cli.find_skill', MagicMock(return_value=MagicMock(base_dir='/fake')))
    runner = CliRunner()
    result = runner.invoke(cli, ['deps', 'install', 'my-skill'])
    assert result.exit_code == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py::test_deps_check_no_args -v`
Expected: FAIL (no such command 'deps')

- [ ] **Step 3: Write minimal implementation**

Update `openskills/cli.py` imports:

```python
from openskills.dependency import (
    resolve_dependency_tree,
    check_dependencies,
    get_dependents,
)
from openskills.finder import find_all_skills, find_skill as find_skill_by_name
from openskills.models import InstallOptions
```

Add the `deps` command group and subcommands before `_list_skills`:

```python
@cli.group()
def deps():
    """Manage skill dependencies"""
    pass


@deps.command('check')
@click.argument('skill_name', required=False)
def deps_check(skill_name):
    """Check dependency satisfaction"""
    if skill_name:
        skill = find_skill_by_name(skill_name)
        if not skill:
            click.echo(f"Error: Skill '{skill_name}' not found")
            return
        results = check_dependencies(skill.base_dir)
        if results["missing"]:
            click.echo(click.style(f"✗ {skill_name} has unsatisfied dependencies:", fg='red'))
            for dep in results["missing"]:
                click.echo(f"    - {dep.name} (not installed)")
        else:
            click.echo(click.style(f"✓ {skill_name} - all dependencies satisfied", fg='green'))
    else:
        skills = find_all_skills()
        issues = 0
        ok = 0
        for skill in skills:
            results = check_dependencies(skill.path)
            if results["missing"]:
                issues += 1
                click.echo(click.style(f"✗ {skill.name} has unsatisfied dependencies:", fg='red'))
                for dep in results["missing"]:
                    click.echo(f"    - {dep.name} (not installed)")
            elif results["satisfied"]:
                ok += 1
                click.echo(click.style(f"✓ {skill.name} - all dependencies satisfied", fg='green'))
        click.echo(click.style(f"\nSummary: {issues} skill(s) with issues, {ok} skill(s) OK", dim=True))


@deps.command('tree')
@click.argument('skill_name', required=False)
def deps_tree(skill_name):
    """Display dependency tree"""
    if skill_name:
        skill = find_skill_by_name(skill_name)
        if not skill:
            click.echo(f"Error: Skill '{skill_name}' not found")
            return
        tree = resolve_dependency_tree(skill.base_dir)
        click.echo(_format_tree(tree))
    else:
        skills = find_all_skills()
        for skill in sorted(skills, key=lambda s: s.name):
            tree = resolve_dependency_tree(skill.path)
            click.echo(_format_tree(tree))


@deps.command('install')
@click.argument('skill_name')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def deps_install(skill_name, yes):
    """Install missing dependencies for a skill"""
    from openskills.installer import install_skill
    skill = find_skill_by_name(skill_name)
    if not skill:
        click.echo(f"Error: Skill '{skill_name}' not found")
        return
    results = check_dependencies(skill.base_dir)
    if not results["missing"]:
        click.echo(click.style("All dependencies already satisfied.", fg='green'))
        return
    click.echo(click.style("The following dependencies will be installed:", bold=True))
    for dep in results["missing"]:
        click.echo(f"  - {dep.name} (from {dep.source})")
    if not yes:
        if not click.confirm("\nInstall these dependencies?", default=True):
            return
    options = InstallOptions(yes=yes)
    for dep in results["missing"]:
        click.echo(f"  Installing: {click.style(dep.name, bold=True)}")
        install_skill(dep.source, options)


def _format_tree(node: dict, prefix: str = "", is_last: bool = True) -> str:
    lines = []
    connector = "└── " if is_last else "├── "
    if prefix:
        lines.append(f"{prefix}{connector}{node['name']}")
    else:
        lines.append(node['name'])

    child_prefix = prefix + ("    " if is_last else "│   ")
    if prefix == "":
        child_prefix = ""
        for i, dep in enumerate(node.get('deps', [])):
            last = (i == len(node.get('deps', [])) - 1)
            sub = _format_tree(dep, "  ", last)
            lines.append(sub)
    else:
        for i, dep in enumerate(node.get('deps', [])):
            last = (i == len(node.get('deps', [])) - 1)
            sub = _format_tree(dep, child_prefix, last)
            lines.append(sub)

    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add openskills/cli.py tests/test_cli.py
git commit -m "feat: add deps command group with check, tree, and install"
```

---

### Task 7: Refine tree formatting and edge cases

**Files:**
- Modify: `openskills/cli.py` (the `_format_tree` function)
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test for tree formatting**

Add to `tests/test_cli.py`:

```python
def test_deps_tree_output_format(monkeypatch):
    from openskills.cli import _format_tree
    tree = {
        "name": "root",
        "deps": [
            {"name": "child-a", "deps": [
                {"name": "grandchild", "deps": []}
            ]},
            {"name": "child-b", "deps": []},
        ],
    }
    result = _format_tree(tree)
    assert "root" in result
    assert "child-a" in result
    assert "child-b" in result
    assert "grandchild" in result
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py::test_deps_tree_output_format -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "test: add tree formatting test"
```

---

### Task 8: Run full test suite and verify

- [ ] **Step 1: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 2: Verify CLI help**

Run: `python -m openskills deps --help`
Expected: Shows check, tree, install subcommands

Run: `python -m openskills deps check --help`
Expected: Shows usage info

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: final adjustments for dependency management"
```
