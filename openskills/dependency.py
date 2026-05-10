import os

from openskills.metadata import read_skill_metadata
from openskills.finder import find_all_skills, find_skill


def resolve_dependency_tree(skill_dir: str, _visiting: set | None = None) -> dict:
    if _visiting is None:
        _visiting = set()

    skill_name = os.path.basename(os.path.normpath(skill_dir))
    if skill_name in _visiting:
        raise ValueError(f"Circular dependency detected: {skill_name}")

    _visiting = _visiting | {skill_name}

    metadata = read_skill_metadata(skill_dir)
    deps = []

    if metadata and metadata.depends_on:
        for dep in metadata.depends_on:
            dep_info = find_skill(dep.name)
            if dep_info:
                sub_tree = resolve_dependency_tree(dep_info.base_dir, _visiting)
                sub_tree["source"] = dep.source
                deps.append(sub_tree)
            else:
                deps.append({"name": dep.name, "source": dep.source, "deps": []})

    return {"name": skill_name, "deps": deps}


def check_dependencies(skill_dir: str) -> dict:
    metadata = read_skill_metadata(skill_dir)

    if not metadata or not metadata.depends_on:
        return {"missing": [], "satisfied": []}

    missing = []
    satisfied = []

    for dep in metadata.depends_on:
        if find_skill(dep.name):
            satisfied.append(dep)
        else:
            missing.append(dep)

    return {"missing": missing, "satisfied": satisfied}


def get_dependents(skill_name: str) -> list[dict]:
    all_skills = find_all_skills()
    dependents = []

    for skill in all_skills:
        metadata = read_skill_metadata(skill.path)
        if metadata and metadata.depends_on:
            for dep in metadata.depends_on:
                if dep.name == skill_name:
                    dependents.append({"name": skill.name, "location": skill.location})
                    break

    return dependents
