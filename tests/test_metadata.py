import json
from datetime import datetime

from openskills.metadata import read_skill_metadata, write_skill_metadata
from openskills.models import SkillRecommendation, SkillSourceMetadata, SkillSourceType


def test_read_skill_metadata_returns_none_for_nonexistent_directory(tmp_path):
    result = read_skill_metadata(str(tmp_path / "no_such_dir"))
    assert result is None


def test_read_skill_metadata_returns_none_when_file_missing(tmp_path):
    result = read_skill_metadata(str(tmp_path))
    assert result is None


def test_read_skill_metadata_returns_none_for_invalid_json(tmp_path):
    bad = tmp_path / ".openskills.json"
    bad.write_text("not valid json{{{")
    result = read_skill_metadata(str(tmp_path))
    assert result is None


def test_read_skill_metadata_returns_none_for_wrong_structure(tmp_path):
    bad = tmp_path / ".openskills.json"
    bad.write_text(json.dumps({"unexpected_key": 123}))
    result = read_skill_metadata(str(tmp_path))
    assert result is None


def test_write_skill_metadata_creates_file(tmp_path):
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
    )
    write_skill_metadata(str(tmp_path), meta)
    assert tmp_path.joinpath(".openskills.json").exists()


def test_write_then_read_roundtrip(tmp_path):
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
        repo_url="https://github.com/example/repo",
        subpath="skills/python",
        local_path="/local/path",
    )
    write_skill_metadata(str(tmp_path), meta)
    result = read_skill_metadata(str(tmp_path))
    assert result is not None
    assert result.source == "https://github.com/example/repo"
    assert result.source_type == SkillSourceType.GIT


def test_write_skill_metadata_fills_installed_at_when_none(tmp_path):
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
    )
    write_skill_metadata(str(tmp_path), meta)
    data = json.loads(tmp_path.joinpath(".openskills.json").read_text())
    assert data["installed_at"] is not None
    parsed = datetime.fromisoformat(data["installed_at"])
    assert isinstance(parsed, datetime)


def test_write_skill_metadata_preserves_existing_installed_at(tmp_path):
    fixed_ts = "2024-06-15T12:00:00"
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
        installed_at=fixed_ts,
    )
    write_skill_metadata(str(tmp_path), meta)
    data = json.loads(tmp_path.joinpath(".openskills.json").read_text())
    assert data["installed_at"] == fixed_ts


def test_read_after_write_returns_correct_metadata(tmp_path):
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.LOCAL,
        repo_url="https://github.com/example/repo",
        subpath="skills/python",
        local_path="/local/path",
        installed_at="2024-01-01T00:00:00",
    )
    write_skill_metadata(str(tmp_path), meta)
    result = read_skill_metadata(str(tmp_path))
    assert result is not None
    assert result.source == meta.source
    assert result.source_type == meta.source_type
    assert result.repo_url == meta.repo_url
    assert result.subpath == meta.subpath
    assert result.local_path == meta.local_path
    assert result.installed_at == meta.installed_at


def test_read_skill_metadata_with_recommends(tmp_path):
    data = {
        "source": "https://github.com/example/repo",
        "source_type": "git",
        "recommends": [
            {"name": "brainstorming", "source": "https://github.com/anthropics/skills/skills/brainstorming"}
        ],
    }
    tmp_path.joinpath(".openskills.json").write_text(json.dumps(data))
    result = read_skill_metadata(str(tmp_path))
    assert result is not None
    assert result.recommends is not None
    assert len(result.recommends) == 1
    assert result.recommends[0].name == "brainstorming"


def test_read_skill_metadata_without_recommends(tmp_path):
    data = {
        "source": "https://github.com/example/repo",
        "source_type": "git",
    }
    tmp_path.joinpath(".openskills.json").write_text(json.dumps(data))
    result = read_skill_metadata(str(tmp_path))
    assert result is not None
    assert result.recommends is None


def test_write_skill_metadata_with_recommends(tmp_path):
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
        recommends=[
            SkillRecommendation(name="brainstorming", source="https://github.com/anthropics/skills/skills/brainstorming"),
        ],
    )
    write_skill_metadata(str(tmp_path), meta)
    data = json.loads(tmp_path.joinpath(".openskills.json").read_text())
    assert "recommends" in data
    assert data["recommends"][0]["name"] == "brainstorming"


def test_write_skill_metadata_without_recommends(tmp_path):
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
    )
    write_skill_metadata(str(tmp_path), meta)
    data = json.loads(tmp_path.joinpath(".openskills.json").read_text())
    assert data.get("recommends") is None


def test_recommends_roundtrip(tmp_path):
    recs = [
        SkillRecommendation(name="brainstorming", source="https://github.com/anthropics/skills/skills/brainstorming"),
        SkillRecommendation(name="writing-plans", source="superpowers"),
    ]
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
        recommends=recs,
    )
    write_skill_metadata(str(tmp_path), meta)
    result = read_skill_metadata(str(tmp_path))
    assert result is not None
    assert result.recommends is not None
    assert len(result.recommends) == 2
    assert result.recommends[0].name == "brainstorming"
    assert result.recommends[1].source == "superpowers"
