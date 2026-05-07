import os

from openskills.models import Skill, SkillLocationInfo
from openskills.dirs import get_search_dirs
from openskills.yaml_utils import extract_yaml_field


def normalize_skill_names(skill_names: str | list[str]) -> list[str]:
    if isinstance(skill_names, str):
        if ',' in skill_names:
            return [name.strip() for name in skill_names.split(',')]
        return [skill_names]
    return skill_names


def is_directory_or_symlink_to_directory(entry: os.DirEntry, parent_dir: str) -> bool:
    if entry.is_dir():
        return True
    if entry.is_symlink():
        try:
            full_path = os.path.join(parent_dir, entry.name)
            return os.path.isdir(full_path)
        except Exception:
            return False
    return False


def find_all_skills() -> list[Skill]:
    skills: list[Skill] = []
    seen = set()
    dirs = get_search_dirs()

    for directory in dirs:
        if not os.path.exists(directory):
            continue

        try:
            entries = os.scandir(directory)
        except OSError:
            continue

        for entry in entries:
            if is_directory_or_symlink_to_directory(entry, directory):
                if entry.name in seen:
                    continue

                skill_path = os.path.join(directory, entry.name, 'SKILL.md')
                if os.path.exists(skill_path):
                    with open(skill_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    is_project_local = os.getcwd() in directory

                    skills.append(Skill(
                        name=entry.name,
                        description=extract_yaml_field(content, 'description'),
                        location='project' if is_project_local else 'global',
                        path=os.path.join(directory, entry.name)
                    ))

                    seen.add(entry.name)

    return skills


def find_skill(skill_name: str) -> SkillLocationInfo | None:
    dirs = get_search_dirs()

    for directory in dirs:
        skill_path = os.path.join(directory, skill_name, 'SKILL.md')
        if os.path.exists(skill_path):
            return SkillLocationInfo(
                path=skill_path,
                base_dir=os.path.join(directory, skill_name),
                source=directory
            )

    return None
