import os

import pytest

from openskills.finder import (
    find_all_skills,
    find_skill,
    is_directory_or_symlink_to_directory,
    normalize_skill_names,
)
from openskills.models import SkillLocationInfo


SKILL_MD = (
    "---\n"
    "name: test-skill\n"
    "description: A test skill\n"
    "---\n"
)


def _make_skill_dir(parent, name, content=SKILL_MD):
    skill_dir = parent / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    return skill_dir


class TestNormalizeSkillNames:
    def test_single_string_returns_list(self):
        assert normalize_skill_names("foo") == ["foo"]

    def test_comma_separated_returns_list(self):
        assert normalize_skill_names("foo, bar, baz") == ["foo", "bar", "baz"]

    def test_list_input_returns_same_list(self):
        names = ["foo", "bar"]
        assert normalize_skill_names(names) is names

    def test_strips_spaces_around_comma_names(self):
        assert normalize_skill_names("  foo  ,  bar  ,  baz  ") == [
            "foo",
            "bar",
            "baz",
        ]


class TestIsDirectoryOrSymlinkToDirectory:
    def test_regular_directory(self, tmp_path):
        (tmp_path / "mydir").mkdir()
        entries = list(os.scandir(str(tmp_path)))
        entry = next(e for e in entries if e.name == "mydir")
        assert is_directory_or_symlink_to_directory(entry, str(tmp_path)) is True

    def test_regular_file_returns_false(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        entries = list(os.scandir(str(tmp_path)))
        entry = next(e for e in entries if e.name == "file.txt")
        assert is_directory_or_symlink_to_directory(entry, str(tmp_path)) is False

    def test_symlink_to_directory(self, tmp_path):
        target = tmp_path / "target"
        target.mkdir()
        (tmp_path / "link").symlink_to(target)
        entries = list(os.scandir(str(tmp_path)))
        entry = next(e for e in entries if e.name == "link")
        assert is_directory_or_symlink_to_directory(entry, str(tmp_path)) is True

    def test_broken_symlink_returns_false(self, tmp_path):
        (tmp_path / "broken").symlink_to(tmp_path / "nonexistent")
        entries = list(os.scandir(str(tmp_path)))
        entry = next(e for e in entries if e.name == "broken")
        assert is_directory_or_symlink_to_directory(entry, str(tmp_path)) is False


class TestFindAllSkills:
    def test_returns_empty_when_no_dirs(self, monkeypatch, tmp_path):
        monkeypatch.setattr("openskills.finder.get_search_dirs", lambda: [])
        assert find_all_skills() == []

    def test_finds_skills_with_valid_skill_md(self, monkeypatch, tmp_path):
        search_dir = tmp_path / "skills"
        search_dir.mkdir()
        _make_skill_dir(search_dir, "my-skill")
        monkeypatch.setattr(
            "openskills.finder.get_search_dirs", lambda: [str(search_dir)]
        )
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / "unrelated"))
        skills = find_all_skills()
        assert len(skills) == 1
        assert skills[0].name == "my-skill"
        assert skills[0].description == "A test skill"

    def test_deduplicates_skills_by_name(self, monkeypatch, tmp_path):
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        _make_skill_dir(dir_a, "dup-skill")
        dir_b = tmp_path / "b"
        dir_b.mkdir()
        _make_skill_dir(dir_b, "dup-skill")
        monkeypatch.setattr(
            "openskills.finder.get_search_dirs",
            lambda: [str(dir_a), str(dir_b)],
        )
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / "unrelated"))
        skills = find_all_skills()
        assert len(skills) == 1
        assert skills[0].name == "dup-skill"
        assert "a" in skills[0].path

    def test_project_location_when_cwd_in_dir(self, monkeypatch, tmp_path):
        search_dir = tmp_path / "project" / ".claude" / "skills"
        search_dir.mkdir(parents=True)
        _make_skill_dir(search_dir, "proj-skill")
        monkeypatch.setattr(
            "openskills.finder.get_search_dirs", lambda: [str(search_dir)]
        )
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / "project"))
        skills = find_all_skills()
        assert len(skills) == 1
        assert skills[0].location == "project"

    def test_global_location_when_cwd_not_in_dir(self, monkeypatch, tmp_path):
        search_dir = tmp_path / "skills"
        search_dir.mkdir()
        _make_skill_dir(search_dir, "glob-skill")
        monkeypatch.setattr(
            "openskills.finder.get_search_dirs", lambda: [str(search_dir)]
        )
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / "unrelated"))
        skills = find_all_skills()
        assert len(skills) == 1
        assert skills[0].location == "global"

    def test_skips_dirs_without_skill_md(self, monkeypatch, tmp_path):
        search_dir = tmp_path / "skills"
        search_dir.mkdir()
        no_skill_dir = search_dir / "no-skill"
        no_skill_dir.mkdir()
        (no_skill_dir / "README.md").write_text("no skill here")
        _make_skill_dir(search_dir, "has-skill")
        monkeypatch.setattr(
            "openskills.finder.get_search_dirs", lambda: [str(search_dir)]
        )
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / "unrelated"))
        skills = find_all_skills()
        assert len(skills) == 1
        assert skills[0].name == "has-skill"


class TestFindSkill:
    def test_returns_none_when_not_found(self, monkeypatch, tmp_path):
        search_dir = tmp_path / "skills"
        search_dir.mkdir()
        monkeypatch.setattr(
            "openskills.finder.get_search_dirs", lambda: [str(search_dir)]
        )
        assert find_skill("nonexistent") is None

    def test_returns_location_info_when_found(self, monkeypatch, tmp_path):
        search_dir = tmp_path / "skills"
        search_dir.mkdir()
        _make_skill_dir(search_dir, "found-skill")
        monkeypatch.setattr(
            "openskills.finder.get_search_dirs", lambda: [str(search_dir)]
        )
        result = find_skill("found-skill")
        assert result is not None
        assert isinstance(result, SkillLocationInfo)

    def test_correct_path_base_dir_source(self, monkeypatch, tmp_path):
        search_dir = tmp_path / "skills"
        search_dir.mkdir()
        _make_skill_dir(search_dir, "my-skill")
        monkeypatch.setattr(
            "openskills.finder.get_search_dirs", lambda: [str(search_dir)]
        )
        result = find_skill("my-skill")
        assert result.path == os.path.join(str(search_dir), "my-skill", "SKILL.md")
        assert result.base_dir == os.path.join(str(search_dir), "my-skill")
        assert result.source == str(search_dir)

    def test_finds_in_first_matching_directory(self, monkeypatch, tmp_path):
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        _make_skill_dir(dir_a, "early-skill")
        dir_b = tmp_path / "b"
        dir_b.mkdir()
        _make_skill_dir(dir_b, "early-skill")
        monkeypatch.setattr(
            "openskills.finder.get_search_dirs",
            lambda: [str(dir_a), str(dir_b)],
        )
        result = find_skill("early-skill")
        assert result.source == str(dir_a)
