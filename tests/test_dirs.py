import os
from pathlib import Path

from openskills.dirs import get_cache_dir, get_search_dirs, get_skills_dir


def test_get_skills_dir_default_contains_cwd():
    result = get_skills_dir()
    assert result.endswith(".agents/skills")
    assert os.getcwd() in result


def test_get_skills_dir_default():
    result = get_skills_dir(global_install=False)
    expected = os.path.join(os.getcwd(), ".agents/skills")
    assert result == expected


def test_get_skills_dir_global_contains_home():
    result = get_skills_dir(global_install=True)
    assert result.endswith(".agents/skills")
    assert str(Path.home()) in result


def test_get_skills_dir_global():
    result = get_skills_dir(global_install=True)
    expected = os.path.join(str(Path.home()), ".agents/skills")
    assert result == expected


def test_get_skills_dir_with_monkeypatch(monkeypatch, tmp_path):
    fake_cwd = str(tmp_path / "project")
    monkeypatch.setattr("os.getcwd", lambda: fake_cwd)
    result = get_skills_dir()
    assert result == os.path.join(fake_cwd, ".agents/skills")


def test_get_search_dirs_returns_four():
    dirs = get_search_dirs()
    assert len(dirs) == 4


def test_get_search_dirs_first_contains_cwd():
    dirs = get_search_dirs()
    assert os.getcwd() in dirs[0]


def test_get_search_dirs_last_contains_home():
    dirs = get_search_dirs()
    assert str(Path.home()) in dirs[3]


def test_get_search_dirs_with_monkeypatch(monkeypatch, tmp_path):
    fake_cwd = str(tmp_path / "project")
    fake_home = str(tmp_path / "home")
    monkeypatch.setattr("os.getcwd", lambda: fake_cwd)
    monkeypatch.setattr("pathlib.Path.home", lambda: Path(fake_home))
    dirs = get_search_dirs()
    assert len(dirs) == 4
    assert dirs[0] == os.path.join(fake_cwd, ".agents/skills")
    assert dirs[1] == os.path.join(fake_cwd, ".claude/skills")
    assert dirs[2] == os.path.join(fake_home, ".agents/skills")
    assert dirs[3] == os.path.join(fake_home, ".claude/skills")


def test_get_cache_dir_ends_with_cache():
    monkeypatch_home = None
    original_home = Path.home
    result = get_cache_dir()
    assert result.endswith(os.path.join(".openskills", "cache"))
    Path.home = original_home


def test_get_cache_dir_creates_directory(monkeypatch, tmp_path):
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: Path(str(fake_home)))
    result = get_cache_dir()
    expected = str(fake_home / ".openskills" / "cache")
    assert result == expected
    assert os.path.isdir(expected)
