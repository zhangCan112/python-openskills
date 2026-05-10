import os
from typing import List, Optional
from unittest.mock import patch

import click
import pytest

from openskills.models import Skill, SkillLocation, SkillSourceMetadata, SkillSourceType
from openskills.updater import (
    _is_path_inside,
    _is_local_path,
    _is_git_url,
    _parse_git_source,
    _prompt_add_source,
    update_skills,
)


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
            with patch("openskills.updater._prompt_add_source"):
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
            with patch("openskills.updater._prompt_add_source"):
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
            with patch("openskills.updater._prompt_add_source"):
                update_skills(None)

        output = capsys.readouterr().out
        assert "0 updated" in output
        assert "1 skipped" in output


class TestIsLocalPath:
    def test_absolute_path(self):
        assert _is_local_path("/foo/bar") is True

    def test_relative_dot_slash(self):
        assert _is_local_path("./foo") is True

    def test_relative_dot_dot_slash(self):
        assert _is_local_path("../foo") is True

    def test_tilde_slash(self):
        assert _is_local_path("~/foo") is True

    def test_https_url(self):
        assert _is_local_path("https://github.com/owner/repo") is False

    def test_plain_name(self):
        assert _is_local_path("pdf") is False


class TestIsGitUrl:
    def test_https_url(self):
        assert _is_git_url("https://github.com/owner/repo") is True

    def test_http_url(self):
        assert _is_git_url("http://example.com/repo") is True

    def test_git_at_url(self):
        assert _is_git_url("git@github.com:owner/repo") is True

    def test_git_protocol(self):
        assert _is_git_url("git://example.com/repo") is True

    def test_dot_git_suffix(self):
        assert _is_git_url("repo.git") is True

    def test_local_path(self):
        assert _is_git_url("/foo/bar") is False

    def test_plain_name(self):
        assert _is_git_url("pdf") is False


class TestParseGitSource:
    def test_simple_repo_url(self):
        result = _parse_git_source("https://github.com/owner/repo")
        assert result["repo_url"] == "https://github.com/owner/repo"
        assert result["subpath"] == ""

    def test_repo_with_subpath(self):
        result = _parse_git_source("https://github.com/owner/repo/skills/pdf")
        assert result["repo_url"] == "https://github.com/owner/repo"
        assert result["subpath"] == "skills/pdf"

    def test_repo_with_deep_subpath(self):
        result = _parse_git_source("https://github.com/owner/repo/a/b/c")
        assert result["repo_url"] == "https://github.com/owner/repo"
        assert result["subpath"] == "a/b/c"

    def test_git_at_url(self):
        result = _parse_git_source("git@github.com:owner/repo")
        assert result["repo_url"] == "git@github.com:owner/repo"
        assert result["subpath"] == ""

    def test_source_field_preserved(self):
        url = "https://github.com/owner/repo/skills/pdf"
        result = _parse_git_source(url)
        assert result["source"] == url


class TestPromptAddSource:
    @patch("openskills.updater.write_skill_metadata")
    @patch("openskills.updater._is_git_url", return_value=True)
    @patch("openskills.updater._parse_git_source")
    def test_add_git_source(self, mock_parse, _mock_git, mock_write, capsys):
        mock_parse.return_value = {
            "source": "https://github.com/owner/repo/skills/pdf",
            "source_type": "git",
            "repo_url": "https://github.com/owner/repo",
            "subpath": "skills/pdf",
        }
        skill = _make_skill("pdf")

        with patch("click.confirm", return_value=True):
            with patch("click.prompt", return_value="https://github.com/owner/repo/skills/pdf"):
                result = _prompt_add_source(skill)

        assert result is True
        mock_write.assert_called_once()
        meta = mock_write.call_args[0][1]
        assert meta.source_type == SkillSourceType.GIT
        assert meta.repo_url == "https://github.com/owner/repo"
        assert meta.subpath == "skills/pdf"

    @patch("openskills.updater.write_skill_metadata")
    @patch("openskills.updater._is_local_path", return_value=True)
    @patch("openskills.updater._is_git_url", return_value=False)
    def test_add_local_source(self, _mock_git, _mock_local, mock_write, capsys):
        skill = _make_skill("my-skill")

        with patch("click.confirm", return_value=True):
            with patch("click.prompt", return_value="./local/path"):
                with patch("os.path.exists", return_value=True):
                    result = _prompt_add_source(skill)

        assert result is True
        mock_write.assert_called_once()
        meta = mock_write.call_args[0][1]
        assert meta.source_type == SkillSourceType.LOCAL

    def test_user_declines(self, capsys):
        skill = _make_skill("pdf")

        with patch("click.confirm", return_value=False):
            result = _prompt_add_source(skill)

        assert result is False

    def test_empty_source_skipped(self, capsys):
        skill = _make_skill("pdf")

        with patch("click.confirm", return_value=True):
            with patch("click.prompt", return_value=""):
                result = _prompt_add_source(skill)

        assert result is False

    @patch("openskills.updater._is_local_path", return_value=False)
    @patch("openskills.updater._is_git_url", return_value=False)
    def test_unrecognized_format(self, _mock_git, _mock_local, capsys):
        skill = _make_skill("pdf")

        with patch("click.confirm", return_value=True):
            with patch("click.prompt", return_value="just-a-name"):
                result = _prompt_add_source(skill)

        assert result is False


class TestUpdateSkillsPromptMetadata:
    @patch("openskills.updater.read_skill_metadata", return_value=None)
    def test_prompts_for_missing_metadata(self, _mock_meta, capsys):
        skill = _make_skill("no-meta")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            with patch("openskills.updater._prompt_add_source") as mock_prompt:
                update_skills(None)

        mock_prompt.assert_called_once_with(skill)

    @patch("openskills.updater.read_skill_metadata", return_value=None)
    def test_no_prompt_when_single_skill_not_found(self, _mock_meta, capsys):
        skill = _make_skill("alpha")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            with patch("openskills.updater._prompt_add_source") as mock_prompt:
                update_skills(["nonexistent"])

        mock_prompt.assert_not_called()

    @patch("openskills.updater.read_skill_metadata", return_value=None)
    def test_prompts_for_specific_skill_without_metadata(self, _mock_meta, capsys):
        skill = _make_skill("pdf")
        with patch("openskills.updater.find_all_skills", return_value=[skill]):
            with patch("openskills.updater._prompt_add_source") as mock_prompt:
                update_skills(["pdf"])

        mock_prompt.assert_called_once_with(skill)

    @patch("openskills.updater.read_skill_metadata", return_value=None)
    def test_multiple_skills_without_metadata(self, _mock_meta, capsys):
        skill_a = _make_skill("alpha")
        skill_b = _make_skill("beta")
        with patch("openskills.updater.find_all_skills", return_value=[skill_a, skill_b]):
            with patch("openskills.updater._prompt_add_source") as mock_prompt:
                update_skills(None)

        assert mock_prompt.call_count == 2
