import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openskills.installer import (
    _format_source,
    _terminal_link,
    expand_path,
    find_skills_in_repo,
    format_size,
    get_cache_key,
    get_directory_size,
    get_repo_name,
    is_git_url,
    is_local_path,
    is_path_inside,
    warn_if_conflict,
)


SKILL_MD_WITH_NAME = (
    "---\n"
    "name: my-skill\n"
    "description: A test skill\n"
    "---\n"
)

SKILL_MD_NO_NAME = (
    "---\n"
    "description: A skill without name\n"
    "---\n"
)

SKILL_MD_INVALID = (
    "This is not valid frontmatter\n"
    "just plain text\n"
)


class TestIsLocalPath:
    def test_absolute_path(self):
        assert is_local_path("/usr/local/bin") is True

    def test_relative_dot_slash(self):
        assert is_local_path("./skills") is True

    def test_relative_dot_dot_slash(self):
        assert is_local_path("../skills") is True

    def test_tilde_slash(self):
        assert is_local_path("~/skills") is True

    def test_plain_name(self):
        assert is_local_path("skill-name") is False

    def test_https_url(self):
        assert is_local_path("https://github.com/owner/repo") is False

    def test_owner_repo_format(self):
        assert is_local_path("owner/repo") is False


class TestIsGitUrl:
    def test_git_at_url(self):
        assert is_git_url("git@github.com:owner/repo") is True

    def test_git_protocol(self):
        assert is_git_url("git://github.com/owner/repo") is True

    def test_http_url(self):
        assert is_git_url("http://github.com/owner/repo") is True

    def test_https_url(self):
        assert is_git_url("https://github.com/owner/repo") is True

    def test_dot_git_suffix(self):
        assert is_git_url("https://github.com/owner/repo.git") is True

    def test_local_path(self):
        assert is_git_url("./skills") is False

    def test_plain_name(self):
        assert is_git_url("skill-name") is False


class TestIsPathInside:
    def test_target_inside_dir(self):
        assert is_path_inside("/foo/bar/baz", "/foo/bar") is True

    def test_target_outside_dir(self):
        assert is_path_inside("/foo/bar", "/foo/baz") is False

    def test_target_equals_dir(self):
        assert is_path_inside("/foo/bar", "/foo/bar") is False

    def test_nested_path(self):
        assert is_path_inside("/foo/bar/baz/qux", "/foo/bar") is True

    def test_relative_paths(self):
        result = is_path_inside(
            os.path.join("sub", "file.txt"),
            "."
        )
        assert result is True


class TestExpandPath:
    def test_tilde_expands_to_home(self):
        result = expand_path("~/skills")
        expected = os.path.join(str(Path.home()), "skills")
        assert result == expected

    def test_relative_path_becomes_absolute(self, monkeypatch):
        monkeypatch.setattr(os, "getcwd", lambda: "/fake/cwd")
        result = expand_path("./skills")
        assert os.path.isabs(result)

    def test_absolute_path_stays_absolute(self):
        result = expand_path(os.path.join(os.sep, "absolute", "path"))
        assert os.path.isabs(result)
        assert result.endswith(os.path.join(os.sep, "absolute", "path"))


class TestGetRepoName:
    def test_https_url(self):
        assert get_repo_name("https://github.com/owner/repo") == "repo"

    def test_url_with_git_suffix(self):
        assert get_repo_name("https://github.com/owner/repo.git") == "repo"

    def test_git_at_url(self):
        assert get_repo_name("git@github.com:owner/repo") == "repo"

    def test_empty_string(self):
        assert get_repo_name("") is None

    def test_url_ending_with_slash(self):
        assert get_repo_name("https://github.com/owner/") is None


class TestGetDirectorySize:
    def test_empty_directory(self, tmp_path):
        assert get_directory_size(str(tmp_path)) == 0

    def test_directory_with_files(self, tmp_path):
        (tmp_path / "file.txt").write_bytes(b"hello world")
        assert get_directory_size(str(tmp_path)) == 11

    def test_counts_nested_files(self, tmp_path):
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (tmp_path / "a.txt").write_bytes(b"aaaa")
        (subdir / "b.txt").write_bytes(b"bbbbb")
        assert get_directory_size(str(tmp_path)) == 9


class TestFormatSize:
    def test_bytes(self):
        assert format_size(512) == "512B"

    def test_zero(self):
        assert format_size(0) == "0B"

    def test_kilobytes(self):
        assert format_size(2048) == "2.0KB"

    def test_megabytes(self):
        assert format_size(1024 * 1024 * 3) == "3.0MB"


class TestGetCacheKey:
    def test_returns_16_char_hex(self):
        key = get_cache_key("https://github.com/owner/repo")
        assert len(key) == 16
        assert all(c in "0123456789abcdef" for c in key)

    def test_deterministic(self):
        url = "https://github.com/owner/repo"
        assert get_cache_key(url) == get_cache_key(url)

    def test_different_inputs(self):
        assert get_cache_key("https://a.com") != get_cache_key("https://b.com")


class TestWarnIfConflict:
    def test_returns_true_when_target_missing(self, tmp_path):
        target = str(tmp_path / "nonexistent")
        assert warn_if_conflict("skill", target, True) is True

    def test_skip_prompt_returns_true(self, tmp_path):
        target = str(tmp_path / "existing")
        Path(target).mkdir()
        assert warn_if_conflict("skill", target, True, skip_prompt=True) is True

    def test_user_declines_returns_false(self, tmp_path):
        target = str(tmp_path / "existing")
        Path(target).mkdir()
        with patch("openskills.installer.click.confirm", return_value=False):
            assert warn_if_conflict("skill", target, True) is False

    def test_user_accepts_returns_true(self, tmp_path):
        target = str(tmp_path / "existing")
        Path(target).mkdir()
        with patch("openskills.installer.click.confirm", return_value=True):
            assert warn_if_conflict("skill", target, True) is True

    def test_existing_target_is_project(self, tmp_path):
        target = str(tmp_path / "existing")
        Path(target).mkdir()
        with patch("openskills.installer.click.confirm", return_value=True):
            assert warn_if_conflict("skill", target, True) is True


class TestFindSkillsInRepo:
    def test_no_skill_md(self, tmp_path):
        assert find_skills_in_repo(str(tmp_path)) == []

    def test_root_skill_md(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(SKILL_MD_WITH_NAME, encoding="utf-8")
        result = find_skills_in_repo(str(tmp_path))
        assert len(result) == 1
        assert result[0]["skill_name"] == "my-skill"
        assert result[0]["skill_dir"] == str(tmp_path)

    def test_nested_skill_md(self, tmp_path):
        sub = tmp_path / "sub-skill"
        sub.mkdir()
        (sub / "SKILL.md").write_text(SKILL_MD_WITH_NAME, encoding="utf-8")
        result = find_skills_in_repo(str(tmp_path))
        assert len(result) == 1
        assert result[0]["skill_name"] == "sub-skill"
        assert result[0]["skill_dir"] == str(sub)

    def test_skips_invalid_frontmatter(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(SKILL_MD_INVALID, encoding="utf-8")
        assert find_skills_in_repo(str(tmp_path)) == []

    def test_uses_frontmatter_name(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(SKILL_MD_WITH_NAME, encoding="utf-8")
        result = find_skills_in_repo(str(tmp_path))
        assert result[0]["skill_name"] == "my-skill"

    def test_falls_back_to_directory_name(self, tmp_path):
        sub = tmp_path / "fallback-name"
        sub.mkdir()
        (sub / "SKILL.md").write_text(SKILL_MD_NO_NAME, encoding="utf-8")
        result = find_skills_in_repo(str(tmp_path))
        assert result[0]["skill_name"] == "fallback-name"


class TestTerminalLink:
    def test_link_with_text(self):
        result = _terminal_link("https://github.com/owner/repo", "owner/repo")
        assert "owner/repo" in result
        assert "https://github.com/owner/repo" in result
        assert "\x1b]8;;" in result

    def test_link_without_text_uses_url(self):
        result = _terminal_link("https://github.com/owner/repo")
        assert "https://github.com/owner/repo" in result
        assert "\x1b]8;;" in result


class TestFormatSource:
    def test_github_url_shortens_to_owner_repo(self):
        result = _format_source("https://github.com/owner/repo")
        assert result == "owner/repo"

    def test_github_url_with_subpath(self):
        result = _format_source("https://github.com/owner/repo/skills/foo")
        assert result == "owner/repo"

    def test_git_at_url(self):
        result = _format_source("git@github.com:owner/repo.git")
        assert result == "owner/repo"

    def test_non_github_url_strips_scheme(self):
        result = _format_source("https://gitlab.com/team/project")
        assert result == "gitlab.com/team/project"

    def test_empty_string(self):
        result = _format_source("")
        assert result == "(unknown)"

    def test_local_path(self):
        result = _format_source("./local-skill")
        assert result == "./local-skill"


class TestInstallRecommendations:
    def test_no_missing_does_not_prompt(self, tmp_path, monkeypatch):
        from openskills.installer import _install_recommendations
        from openskills.models import InstallOptions
        monkeypatch.setattr("openskills.installer.resolve_recommendation_tree",
                            lambda d: {"name": "skill", "recs": []})
        monkeypatch.setattr("openskills.installer.find_skill", lambda n: None)
        _install_recommendations(str(tmp_path), InstallOptions())

    def test_missing_recs_prompt_selective(self, tmp_path, monkeypatch):
        from openskills.installer import _install_recommendations
        from openskills.models import InstallOptions
        tree = {
            "name": "skill",
            "recs": [
                {"name": "rec-a", "source": "https://github.com/owner/rec-a", "recs": []},
                {"name": "rec-b", "source": "https://github.com/owner/rec-b", "recs": []},
            ]
        }
        monkeypatch.setattr("openskills.installer.resolve_recommendation_tree",
                            lambda d: tree)
        monkeypatch.setattr("openskills.installer.find_skill", lambda n: None)
        monkeypatch.setattr("openskills.installer.prompt_for_selection",
                            lambda msg, choices: ["rec-a"])
        mock_install = MagicMock()
        monkeypatch.setattr("openskills.installer.install_skill", mock_install)

        _install_recommendations(str(tmp_path), InstallOptions())

        mock_install.assert_called_once()
        assert mock_install.call_args[0][0] == "https://github.com/owner/rec-a"

    def test_missing_recs_yes_flag_installs_all(self, tmp_path, monkeypatch):
        from openskills.installer import _install_recommendations
        from openskills.models import InstallOptions
        tree = {
            "name": "skill",
            "recs": [
                {"name": "rec-a", "source": "https://github.com/owner/rec-a", "recs": []},
                {"name": "rec-b", "source": "https://github.com/owner/rec-b", "recs": []},
            ]
        }
        monkeypatch.setattr("openskills.installer.resolve_recommendation_tree",
                            lambda d: tree)
        monkeypatch.setattr("openskills.installer.find_skill", lambda n: None)
        mock_install = MagicMock()
        monkeypatch.setattr("openskills.installer.install_skill", mock_install)

        _install_recommendations(str(tmp_path), InstallOptions(yes=True))

        assert mock_install.call_count == 2


class TestInstallFromRepoChoices:
    def test_choices_have_no_ansi_escape_codes(self, monkeypatch, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / "SKILL.md").write_text("---\nname: alpha\n---\n")
        sub = repo_dir / "beta"
        sub.mkdir()
        (sub / "SKILL.md").write_text("---\nname: beta\n---\n")

        captured_choices = {}

        def fake_prompt(message, choices):
            captured_choices['value'] = choices
            return [c['value'] for c in choices]

        monkeypatch.setattr("openskills.installer.prompt_for_selection", fake_prompt)

        from openskills.installer import InstallOptions, install_from_repo
        target = tmp_path / "target"
        target.mkdir()

        import re
        install_from_repo(
            str(repo_dir), str(target),
            InstallOptions(yes=False), None,
            {'source_type': 'local', 'source': str(repo_dir)}
        )

        for choice in captured_choices['value']:
            assert not re.search(r'\x1b\[[0-9;]*m', choice['name']), (
                f"Choice name contains ANSI escape codes: {repr(choice['name'])}"
            )
