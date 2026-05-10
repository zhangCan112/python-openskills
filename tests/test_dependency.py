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

    def test_single_dependency(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", depends_on=[
            SkillDependency(name="parent", source="https://github.com/test/repo/skills/parent"),
        ])
        _create_skill(str(tmp_path), "parent")

        def mock_find(name):
            p = str(tmp_path / name)
            if os.path.exists(p):
                import types
                return types.SimpleNamespace(base_dir=p)
            return None

        monkeypatch.setattr("openskills.dependency.find_skill", mock_find)
        result = resolve_dependency_tree(str(tmp_path / "child"))
        assert result["name"] == "child"
        assert len(result["deps"]) == 1
        assert result["deps"][0]["name"] == "parent"

    def test_transitive_dependencies(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "grandchild", depends_on=[
            SkillDependency(name="child", source="test"),
        ])
        _create_skill(str(tmp_path), "child", depends_on=[
            SkillDependency(name="root", source="test"),
        ])
        _create_skill(str(tmp_path), "root")

        def mock_find(name):
            p = str(tmp_path / name)
            if os.path.exists(p):
                import types
                return types.SimpleNamespace(base_dir=p)
            return None

        monkeypatch.setattr("openskills.dependency.find_skill", mock_find)
        result = resolve_dependency_tree(str(tmp_path / "grandchild"))
        assert result["name"] == "grandchild"
        assert len(result["deps"]) == 1
        child_dep = result["deps"][0]
        assert child_dep["name"] == "child"
        assert len(child_dep["deps"]) == 1
        assert child_dep["deps"][0]["name"] == "root"

    def test_circular_dependency_raises(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "a", depends_on=[
            SkillDependency(name="b", source="test"),
        ])
        _create_skill(str(tmp_path), "b", depends_on=[
            SkillDependency(name="a", source="test"),
        ])

        def mock_find(name):
            p = str(tmp_path / name)
            if os.path.exists(p):
                import types
                return types.SimpleNamespace(base_dir=p)
            return None

        monkeypatch.setattr("openskills.dependency.find_skill", mock_find)
        with pytest.raises(ValueError, match="[Cc]ircular"):
            resolve_dependency_tree(str(tmp_path / "a"))

    def test_missing_dependency_not_installed(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "orphan", depends_on=[
            SkillDependency(name="missing", source="test"),
        ])
        monkeypatch.setattr("openskills.dependency.find_skill", lambda n: None)
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

        def mock_find(name):
            p = str(tmp_path / name)
            if os.path.exists(p):
                import types
                return types.SimpleNamespace(base_dir=p)
            return None

        monkeypatch.setattr("openskills.dependency.find_skill", mock_find)
        results = check_dependencies(str(tmp_path / "child"))
        assert len(results["missing"]) == 0
        assert len(results["satisfied"]) == 1

    def test_missing_dependency(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", depends_on=[
            SkillDependency(name="parent", source="test"),
        ])
        monkeypatch.setattr("openskills.dependency.find_skill", lambda n: None)
        results = check_dependencies(str(tmp_path / "child"))
        assert len(results["missing"]) == 1
        assert results["missing"][0].name == "parent"

    def test_no_dependencies(self, tmp_path):
        _create_skill(str(tmp_path), "solo")
        results = check_dependencies(str(tmp_path / "solo"))
        assert results["missing"] == []
        assert results["satisfied"] == []


class TestGetDependents:
    def test_no_dependents(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "solo")

        import types
        monkeypatch.setattr("openskills.dependency.find_all_skills", lambda: [
            types.SimpleNamespace(name="solo", path=str(tmp_path / "solo")),
        ])
        result = get_dependents("target")
        assert result == []

    def test_has_dependents(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", depends_on=[
            SkillDependency(name="parent", source="test"),
        ])
        _create_skill(str(tmp_path), "parent")

        import types
        monkeypatch.setattr("openskills.dependency.find_all_skills", lambda: [
            types.SimpleNamespace(name="child", path=str(tmp_path / "child"), location="project"),
            types.SimpleNamespace(name="parent", path=str(tmp_path / "parent"), location="project"),
        ])
        result = get_dependents("parent")
        assert len(result) == 1
        assert result[0]["name"] == "child"

    def test_multiple_dependents(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child-a", depends_on=[
            SkillDependency(name="parent", source="test"),
        ])
        _create_skill(str(tmp_path), "child-b", depends_on=[
            SkillDependency(name="parent", source="test"),
        ])
        _create_skill(str(tmp_path), "parent")

        import types
        monkeypatch.setattr("openskills.dependency.find_all_skills", lambda: [
            types.SimpleNamespace(name="child-a", path=str(tmp_path / "child-a"), location="project"),
            types.SimpleNamespace(name="child-b", path=str(tmp_path / "child-b"), location="project"),
            types.SimpleNamespace(name="parent", path=str(tmp_path / "parent"), location="project"),
        ])
        result = get_dependents("parent")
        assert len(result) == 2
        names = [d["name"] for d in result]
        assert "child-a" in names
        assert "child-b" in names
