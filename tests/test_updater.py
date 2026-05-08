import os
from typing import List, Optional
from unittest.mock import patch

import click
import pytest

from openskills.models import Skill, SkillLocation, SkillSourceMetadata, SkillSourceType
from openskills.updater import _is_path_inside, update_skills


def _make_skill(name: str, path: Optional[str] = None) -> Skill:
    return Skill(
        name=name,
        description="test",
        location=SkillLocation.PROJECT,
        path=path or os.path.join("/tmp", name),
    )


def _make_local_meta(local_path: Optional[str] = "/tmp/src") -> SkillSourceMetadata:
    return SkillSourceMetadata(
        source="local",
        source_type=SkillSourceType.LOCAL,
        local_path=local_path,
    )


def _make_git_meta(
    repo_url: Optional[str] = "https://github.com/example/repo",
    subpath: Optional[str] = None,
) -> SkillSourceMetadata:
    return SkillSourceMetadata(
        source=repo_url,
        source_type=SkillSourceType.GIT,
        repo_url=repo_url,
        subpath=subpath,
    )


class TestIsPathInside:
    def test_returns_true_for_nested_path(self):
        assert _is_path_inside("/foo/bar/baz", "/foo/bar") is True

    def test_returns_false_for_path_outside(self):
        assert _is_path_inside("/other/path", "/foo/bar") is False

    def test_returns_false_when_target_equals_dir(self):
        assert _is_path_inside("/foo/bar", "/foo/bar") is False

    def test_returns_true_for_deeply_nested(self):
        assert _is_path_inside("/a/b/c/d/e", "/a/b") is True

    def test_returns_false_for_sibling(self):
        assert _is_path_inside("/foo/baz", "/foo/bar") is False

    def test_handles_trailing_sep_on_dir(self):
        assert _is_path_inside("/foo/bar/baz", "/foo/bar/") is True

    def test_returns_false_for_partial_prefix_match(self):
        assert _is_path_inside("/foo/bar_extra", "/foo/bar") is False


class TestUpdateSkillsEmptyState:
    @patch("openskills.updater.find_all_skills", return_value=[])
    def test_displays_empty_state_when_no_skills(self, _mock_find, capsys):
        update_skills(None)
        output = capsys.readouterr().out
        assert "No skills installed" in output
        assert "Install skills" in output


class TestUpdateSkillsFiltering:
    @patch("openskills.updater.find_all_skills", return_value=[])
    def test_no_matching_skills_message(self, _mock_find, capsys):
        skill_a = _make_skill("alpha")
        skill_b = _make_skill("beta")

        with patch("openskills.updater.find_all_skills", return_value=[skill_a, skill_b]):
            with patch("openskills.updater.read_skill_metadata", return_value=None):
                update_skills(["nonexistent"])

        output = capsys.readouterr().out
        assert "No matching skills to update" in output

    @patch("openskills.updater.read_skill_metadata", return_value=None)
    def test_reports_missing_skills(self, _mock_meta, capsys):
        skill_a = _make_skill("alpha")
        with patch("openskills.updater.find_all_skills", return_value=[skill_a]):
            update_skills(["alpha", "ghost"])

        output = capsys.readouterr().out
        assert "Skipping missing skills: ghost" in output

    @patch("openskills.updater._update_skill_from_local", return_value=(True, ""))
    @patch("openskills.updater.read_skill_metadata", return_value=_make_local_meta())
    def test_filters_to_requested_skills(self, _mock_meta, _mock_update, capsys):
        skill_a = _make_skill("alpha")
        skill_b = _make_skill("beta")
        with patch("openskills.updater.find_all_skills", return_value=[skill_a, skill_b]):
            update_skills(["alpha"])

        output = capsys.readouterr().out
        assert "alpha" in output
        assert "beta" not in output


class TestUpdateSkillsNoMetadata:
    @patch("openskills.updater.read_skill_metadata", return_value=None)
    def test_skips_skills_without_metadata(self, _mock_meta, capsys):
        skill = _make_skill("no-meta")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            update_skills(None)

        output = capsys.readouterr().out
        assert "Skipped: no-meta" in output
        assert "no source metadata" in output


class TestUpdateSkillsLocal:
    @patch("openskills.updater._update_skill_from_local", return_value=(True, ""))
    @patch("openskills.updater.read_skill_metadata", return_value=_make_local_meta())
    def test_updates_local_skill(self, _mock_meta, mock_update, capsys):
        skill = _make_skill("local-skill")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            update_skills(None)

        output = capsys.readouterr().out
        assert "Updated: local-skill" in output
        mock_update.assert_called_once()

    @patch(
        "openskills.updater._update_skill_from_local",
        return_value=(False, "Local source missing"),
    )
    @patch("openskills.updater.read_skill_metadata", return_value=_make_local_meta())
    def test_handles_local_update_failure(self, _mock_meta, mock_update, capsys):
        skill = _make_skill("bad-local")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            update_skills(None)

        output = capsys.readouterr().out
        assert "Skipped: bad-local" in output
        assert "Local source missing" in output


class TestUpdateSkillsGit:
    @patch("openskills.updater._update_skill_from_git", return_value=(True, ""))
    @patch("openskills.updater.read_skill_metadata", return_value=_make_git_meta())
    def test_updates_git_skill(self, _mock_meta, mock_update, capsys):
        skill = _make_skill("git-skill")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            update_skills(None)

        output = capsys.readouterr().out
        assert "Updated: git-skill" in output
        mock_update.assert_called_once()

    @patch("openskills.updater._update_skill_from_git", return_value=(True, ""))
    @patch(
        "openskills.updater.read_skill_metadata",
        return_value=_make_git_meta(subpath="skills/sub"),
    )
    def test_updates_git_skill_with_subpath(self, _mock_meta, mock_update, capsys):
        skill = _make_skill("git-sub")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            update_skills(None)

        output = capsys.readouterr().out
        assert "Updated: git-sub" in output

    @patch("openskills.updater.read_skill_metadata")
    def test_skips_git_skill_without_repo_url(self, mock_meta, capsys):
        meta = _make_git_meta(repo_url=None)
        meta.source_type = SkillSourceType.GIT
        mock_meta.return_value = meta

        skill = _make_skill("no-url")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            update_skills(None)

        output = capsys.readouterr().out
        assert "Skipped: no-url" in output
        assert "missing repo URL" in output

    @patch(
        "openskills.updater._update_skill_from_git",
        return_value=(False, "git clone failed: error"),
    )
    @patch("openskills.updater.read_skill_metadata", return_value=_make_git_meta())
    def test_handles_git_clone_failure(self, _mock_meta, mock_update, capsys):
        skill = _make_skill("clone-fail")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            update_skills(None)

        output = capsys.readouterr().out
        assert "Skipped: clone-fail" in output
        assert "git clone failed" in output


class TestUpdateSkillsSummary:
    @patch("openskills.updater._update_skill_from_local", return_value=(True, ""))
    @patch("openskills.updater.read_skill_metadata", return_value=_make_local_meta())
    def test_summary_shows_updated_count(self, _mock_meta, _mock_update, capsys):
        skill_a = _make_skill("a")
        skill_b = _make_skill("b")
        with patch(
            "openskills.updater.find_all_skills", return_value=[skill_a, skill_b]
        ):
            update_skills(None)

        output = capsys.readouterr().out
        assert "2 updated" in output
        assert "0 skipped" in output
        assert "2 total" in output

    @patch("openskills.updater.read_skill_metadata", return_value=None)
    def test_summary_shows_skipped_count(self, _mock_meta, capsys):
        skill = _make_skill("skip-me")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            update_skills(None)

        output = capsys.readouterr().out
        assert "0 updated" in output
        assert "1 skipped" in output
