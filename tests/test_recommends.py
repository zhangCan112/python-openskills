import json
import os

import pytest

from openskills.recommends import (
    resolve_recommendation_tree,
    check_recommendations,
    get_recommenders,
    add_recommendation,
)
from openskills.metadata import read_skill_metadata, write_skill_metadata
from openskills.models import SkillRecommendation, SkillSourceMetadata, SkillSourceType


def _create_skill(base_dir, name, recommends=None):
    skill_dir = os.path.join(base_dir, name)
    os.makedirs(skill_dir, exist_ok=True)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    skill_md_content = f"---\nname: {name}\ndescription: Test skill {name}\n---\n"
    with open(skill_md, 'w', encoding='utf-8') as f:
        f.write(skill_md_content)

    metadata = SkillSourceMetadata(
        source=f"https://github.com/test/repo/skills/{name}",
        source_type=SkillSourceType.GIT,
        recommends=recommends,
    )
    write_skill_metadata(skill_dir, metadata)
    return skill_dir


class TestResolveRecommendationTree:
    def test_no_recommendations(self, tmp_path):
        _create_skill(str(tmp_path), "solo")
        result = resolve_recommendation_tree(str(tmp_path / "solo"))
        assert result == {"name": "solo", "recs": []}

    def test_single_recommendation(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", recommends=[
            SkillRecommendation(name="parent", source="https://github.com/test/repo/skills/parent"),
        ])
        _create_skill(str(tmp_path), "parent")

        def mock_find(name):
            p = str(tmp_path / name)
            if os.path.exists(p):
                import types
                return types.SimpleNamespace(base_dir=p)
            return None

        monkeypatch.setattr("openskills.recommends.find_skill", mock_find)
        result = resolve_recommendation_tree(str(tmp_path / "child"))
        assert result["name"] == "child"
        assert len(result["recs"]) == 1
        assert result["recs"][0]["name"] == "parent"

    def test_transitive_recommendations(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "grandchild", recommends=[
            SkillRecommendation(name="child", source="test"),
        ])
        _create_skill(str(tmp_path), "child", recommends=[
            SkillRecommendation(name="root", source="test"),
        ])
        _create_skill(str(tmp_path), "root")

        def mock_find(name):
            p = str(tmp_path / name)
            if os.path.exists(p):
                import types
                return types.SimpleNamespace(base_dir=p)
            return None

        monkeypatch.setattr("openskills.recommends.find_skill", mock_find)
        result = resolve_recommendation_tree(str(tmp_path / "grandchild"))
        assert result["name"] == "grandchild"
        assert len(result["recs"]) == 1
        child_rec = result["recs"][0]
        assert child_rec["name"] == "child"
        assert len(child_rec["recs"]) == 1
        assert child_rec["recs"][0]["name"] == "root"

    def test_circular_recommendation_raises(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "a", recommends=[
            SkillRecommendation(name="b", source="test"),
        ])
        _create_skill(str(tmp_path), "b", recommends=[
            SkillRecommendation(name="a", source="test"),
        ])

        def mock_find(name):
            p = str(tmp_path / name)
            if os.path.exists(p):
                import types
                return types.SimpleNamespace(base_dir=p)
            return None

        monkeypatch.setattr("openskills.recommends.find_skill", mock_find)
        with pytest.raises(ValueError, match="[Cc]ircular"):
            resolve_recommendation_tree(str(tmp_path / "a"))

    def test_missing_recommendation_not_installed(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "orphan", recommends=[
            SkillRecommendation(name="missing", source="test"),
        ])
        monkeypatch.setattr("openskills.recommends.find_skill", lambda n: None)
        result = resolve_recommendation_tree(str(tmp_path / "orphan"))
        assert result["name"] == "orphan"
        assert len(result["recs"]) == 1
        assert result["recs"][0]["name"] == "missing"
        assert result["recs"][0]["recs"] == []


class TestCheckRecommendations:
    def test_all_satisfied(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", recommends=[
            SkillRecommendation(name="parent", source="test"),
        ])
        _create_skill(str(tmp_path), "parent")

        def mock_find(name):
            p = str(tmp_path / name)
            if os.path.exists(p):
                import types
                return types.SimpleNamespace(base_dir=p)
            return None

        monkeypatch.setattr("openskills.recommends.find_skill", mock_find)
        results = check_recommendations(str(tmp_path / "child"))
        assert len(results["missing"]) == 0
        assert len(results["satisfied"]) == 1

    def test_missing_recommendation(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", recommends=[
            SkillRecommendation(name="parent", source="test"),
        ])
        monkeypatch.setattr("openskills.recommends.find_skill", lambda n: None)
        results = check_recommendations(str(tmp_path / "child"))
        assert len(results["missing"]) == 1
        assert results["missing"][0].name == "parent"

    def test_no_recommendations(self, tmp_path):
        _create_skill(str(tmp_path), "solo")
        results = check_recommendations(str(tmp_path / "solo"))
        assert results["missing"] == []
        assert results["satisfied"] == []


class TestGetRecommenders:
    def test_no_recommenders(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "solo")

        import types
        monkeypatch.setattr("openskills.recommends.find_all_skills", lambda: [
            types.SimpleNamespace(name="solo", path=str(tmp_path / "solo")),
        ])
        result = get_recommenders("target")
        assert result == []

    def test_has_recommenders(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child", recommends=[
            SkillRecommendation(name="parent", source="test"),
        ])
        _create_skill(str(tmp_path), "parent")

        import types
        monkeypatch.setattr("openskills.recommends.find_all_skills", lambda: [
            types.SimpleNamespace(name="child", path=str(tmp_path / "child"), location="project"),
            types.SimpleNamespace(name="parent", path=str(tmp_path / "parent"), location="project"),
        ])
        result = get_recommenders("parent")
        assert len(result) == 1
        assert result[0]["name"] == "child"

    def test_multiple_recommenders(self, tmp_path, monkeypatch):
        _create_skill(str(tmp_path), "child-a", recommends=[
            SkillRecommendation(name="parent", source="test"),
        ])
        _create_skill(str(tmp_path), "child-b", recommends=[
            SkillRecommendation(name="parent", source="test"),
        ])
        _create_skill(str(tmp_path), "parent")

        import types
        monkeypatch.setattr("openskills.recommends.find_all_skills", lambda: [
            types.SimpleNamespace(name="child-a", path=str(tmp_path / "child-a"), location="project"),
            types.SimpleNamespace(name="child-b", path=str(tmp_path / "child-b"), location="project"),
            types.SimpleNamespace(name="parent", path=str(tmp_path / "parent"), location="project"),
        ])
        result = get_recommenders("parent")
        assert len(result) == 2
        names = [d["name"] for d in result]
        assert "child-a" in names
        assert "child-b" in names


def _create_skill_without_metadata(base_dir, name):
    skill_dir = os.path.join(base_dir, name)
    os.makedirs(skill_dir, exist_ok=True)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    with open(skill_md, "w", encoding="utf-8") as f:
        f.write(f"---\nname: {name}\ndescription: Test {name}\n---\n")
    return skill_dir


class TestAddRecommendation:
    def test_creates_metadata_if_missing(self, tmp_path):
        skill_dir = _create_skill_without_metadata(str(tmp_path), "myskill")
        assert not os.path.exists(os.path.join(skill_dir, ".openskills.json"))

        add_recommendation(skill_dir, SkillRecommendation(name="rec-skill", source="https://example.com/rec"))

        metadata = read_skill_metadata(skill_dir)
        assert metadata is not None
        assert metadata.source_type == SkillSourceType.LOCAL
        assert metadata.recommends is not None
        assert len(metadata.recommends) == 1
        assert metadata.recommends[0].name == "rec-skill"

    def test_appends_to_existing_recommends(self, tmp_path):
        skill_dir = _create_skill_without_metadata(str(tmp_path), "myskill")
        write_skill_metadata(skill_dir, SkillSourceMetadata(
            source="https://github.com/test/repo",
            source_type=SkillSourceType.GIT,
            recommends=[SkillRecommendation(name="existing", source="test")],
        ))

        add_recommendation(skill_dir, SkillRecommendation(name="new-rec", source="test2"))

        metadata = read_skill_metadata(skill_dir)
        assert metadata is not None
        assert len(metadata.recommends) == 2
        names = [r.name for r in metadata.recommends]
        assert "existing" in names
        assert "new-rec" in names

    def test_adds_recommends_to_metadata_without_recommends(self, tmp_path):
        skill_dir = _create_skill_without_metadata(str(tmp_path), "myskill")
        write_skill_metadata(skill_dir, SkillSourceMetadata(
            source="https://github.com/test/repo",
            source_type=SkillSourceType.GIT,
        ))

        add_recommendation(skill_dir, SkillRecommendation(name="new-rec", source="test"))

        metadata = read_skill_metadata(skill_dir)
        assert metadata is not None
        assert metadata.recommends is not None
        assert len(metadata.recommends) == 1
        assert metadata.recommends[0].name == "new-rec"

    def test_duplicate_name_not_added(self, tmp_path):
        skill_dir = _create_skill_without_metadata(str(tmp_path), "myskill")
        write_skill_metadata(skill_dir, SkillSourceMetadata(
            source="test",
            source_type=SkillSourceType.LOCAL,
            recommends=[SkillRecommendation(name="existing", source="test")],
        ))

        result = add_recommendation(skill_dir, SkillRecommendation(name="existing", source="test"))

        assert result is False
        metadata = read_skill_metadata(skill_dir)
        assert len(metadata.recommends) == 1

    def test_preserves_other_metadata_fields(self, tmp_path):
        skill_dir = _create_skill_without_metadata(str(tmp_path), "myskill")
        write_skill_metadata(skill_dir, SkillSourceMetadata(
            source="https://github.com/test/repo",
            source_type=SkillSourceType.GIT,
            repo_url="https://github.com/test/repo",
            subpath="skills/myskill",
            installed_at="2024-01-01T00:00:00",
        ))

        add_recommendation(skill_dir, SkillRecommendation(name="rec", source="test"))

        metadata = read_skill_metadata(skill_dir)
        assert metadata.repo_url == "https://github.com/test/repo"
        assert metadata.subpath == "skills/myskill"
        assert metadata.installed_at == "2024-01-01T00:00:00"
