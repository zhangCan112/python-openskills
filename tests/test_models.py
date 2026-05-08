from openskills.models import (
    InstallOptions,
    Skill,
    SkillLocation,
    SkillLocationInfo,
    SkillSourceMetadata,
    SkillSourceType,
)


def test_skill_location_project():
    assert SkillLocation.PROJECT == "project"


def test_skill_location_global():
    assert SkillLocation.GLOBAL == "global"


def test_skill_location_is_string_enum():
    assert SkillLocation.PROJECT == "project"
    assert SkillLocation.GLOBAL == "global"
    assert isinstance(SkillLocation.PROJECT, str)


def test_skill_source_type_git():
    assert SkillSourceType.GIT == "git"


def test_skill_source_type_local():
    assert SkillSourceType.LOCAL == "local"


def test_skill_source_type_is_string_enum():
    assert SkillSourceType.GIT == "git"
    assert SkillSourceType.LOCAL == "local"
    assert isinstance(SkillSourceType.GIT, str)


def test_skill_creation():
    skill = Skill(
        name="my-skill",
        description="A test skill",
        location=SkillLocation.PROJECT,
        path="/some/path",
    )
    assert skill.name == "my-skill"
    assert skill.description == "A test skill"
    assert skill.location == SkillLocation.PROJECT
    assert skill.path == "/some/path"


def test_skill_location_info_creation():
    info = SkillLocationInfo(
        path="/skills/test",
        base_dir="/project",
        source="git",
    )
    assert info.path == "/skills/test"
    assert info.base_dir == "/project"
    assert info.source == "git"


def test_skill_source_metadata_defaults():
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
    )
    assert meta.source == "https://github.com/example/repo"
    assert meta.source_type == SkillSourceType.GIT
    assert meta.repo_url is None
    assert meta.subpath is None
    assert meta.local_path is None
    assert meta.installed_at is None


def test_skill_source_metadata_all_fields():
    meta = SkillSourceMetadata(
        source="https://github.com/example/repo",
        source_type=SkillSourceType.GIT,
        repo_url="https://github.com/example/repo",
        subpath="skills/python",
        local_path="/local/path",
        installed_at="2024-01-01",
    )
    assert meta.repo_url == "https://github.com/example/repo"
    assert meta.subpath == "skills/python"
    assert meta.local_path == "/local/path"
    assert meta.installed_at == "2024-01-01"


def test_install_options_defaults():
    opts = InstallOptions()
    assert opts.global_install is False
    assert opts.yes is False


def test_install_options_non_defaults():
    opts = InstallOptions(global_install=True, yes=True)
    assert opts.global_install is True
    assert opts.yes is True
