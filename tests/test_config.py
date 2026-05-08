from pathlib import Path

import yaml

from openskills.config import get_config_file_path, load_config


def test_get_config_file_path_returns_none_when_no_config(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "fakehome")
    result = get_config_file_path()
    assert result is None


def test_get_config_file_path_finds_config_in_cwd(monkeypatch, tmp_path):
    config_file = tmp_path / "market_sources.yaml"
    config_file.write_text(yaml.dump({"sources": [{"name": "test"}]}))
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "fakehome")
    result = get_config_file_path()
    assert result == str(config_file)


def test_get_config_file_path_searches_parent_directories(monkeypatch, tmp_path):
    parent = tmp_path / "root"
    child = parent / "sub1" / "sub2"
    child.mkdir(parents=True)
    config_file = parent / "market_sources.yaml"
    config_file.write_text(yaml.dump({"sources": []}))
    monkeypatch.setattr(Path, "cwd", lambda: child)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "fakehome")
    result = get_config_file_path()
    assert result == str(config_file)


def test_load_config_returns_empty_sources_when_no_config(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "fakehome")
    result = load_config()
    assert result == {"sources": []}


def test_load_config_reads_valid_config(monkeypatch, tmp_path):
    config_file = tmp_path / "market_sources.yaml"
    config_file.write_text(yaml.dump({"sources": [{"name": "my-source", "url": "https://example.com"}]}))
    monkeypatch.setattr("openskills.config.get_config_file_path", lambda: str(config_file))
    result = load_config()
    assert len(result["sources"]) == 1
    assert result["sources"][0]["name"] == "my-source"


def test_load_config_handles_invalid_yaml(monkeypatch, tmp_path):
    config_file = tmp_path / "market_sources.yaml"
    config_file.write_text("{{{{invalid yaml::::")
    monkeypatch.setattr("openskills.config.get_config_file_path", lambda: str(config_file))
    result = load_config()
    assert result == {"sources": []}


def test_load_config_handles_empty_yaml_file(monkeypatch, tmp_path):
    config_file = tmp_path / "market_sources.yaml"
    config_file.write_text("")
    monkeypatch.setattr("openskills.config.get_config_file_path", lambda: str(config_file))
    result = load_config()
    assert result == {}
