from dataclasses import dataclass
from enum import Enum


class SkillLocation(str, Enum):
    PROJECT = "project"
    GLOBAL = "global"


class SkillSourceType(str, Enum):
    GIT = "git"
    LOCAL = "local"


@dataclass
class SkillRecommendation:
    name: str
    source: str


@dataclass
class Skill:
    name: str
    description: str
    location: SkillLocation
    path: str


@dataclass
class SkillLocationInfo:
    path: str
    base_dir: str
    source: str


@dataclass
class SkillSourceMetadata:
    source: str
    source_type: SkillSourceType
    repo_url: str | None = None
    subpath: str | None = None
    local_path: str | None = None
    recommends: list[SkillRecommendation] | None = None
    installed_at: str | None = None


@dataclass
class InstallOptions:
    global_install: bool = False
    yes: bool = False
