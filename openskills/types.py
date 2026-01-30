"""
Core type definitions for OpenSkills
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class SkillLocation(str, Enum):
    """Skill installation location"""
    PROJECT = "project"
    GLOBAL = "global"


class SkillSourceType(str, Enum):
    """Source type for skill installation"""
    GIT = "git"
    LOCAL = "local"


@dataclass
class Skill:
    """Represents an installed skill"""
    name: str
    description: str
    location: SkillLocation
    path: str


@dataclass
class SkillLocationInfo:
    """Information about where a skill is located"""
    path: str  # Path to SKILL.md
    base_dir: str  # Base directory containing the skill
    source: str  # Source directory (skills folder)


@dataclass
class SkillSourceMetadata:
    """Metadata about where a skill was installed from"""
    source: str
    source_type: SkillSourceType
    repo_url: str | None = None
    subpath: str | None = None
    local_path: str | None = None
    installed_at: str | None = None


@dataclass
class InstallOptions:
    """Options for skill installation"""
    global_install: bool = False
    universal: bool = False
    yes: bool = False