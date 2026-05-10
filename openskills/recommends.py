import os

from openskills.metadata import read_skill_metadata
from openskills.finder import find_all_skills, find_skill


def resolve_recommendation_tree(skill_dir: str, _visiting: set | None = None) -> dict:
    if _visiting is None:
        _visiting = set()

    skill_name = os.path.basename(os.path.normpath(skill_dir))
    if skill_name in _visiting:
        raise ValueError(f"Circular recommendation detected: {skill_name}")

    _visiting = _visiting | {skill_name}

    metadata = read_skill_metadata(skill_dir)
    recs = []

    if metadata and metadata.recommends:
        for rec in metadata.recommends:
            rec_info = find_skill(rec.name)
            if rec_info:
                sub_tree = resolve_recommendation_tree(rec_info.base_dir, _visiting)
                sub_tree["source"] = rec.source
                recs.append(sub_tree)
            else:
                recs.append({"name": rec.name, "source": rec.source, "recs": []})

    return {"name": skill_name, "recs": recs}


def check_recommendations(skill_dir: str) -> dict:
    metadata = read_skill_metadata(skill_dir)

    if not metadata or not metadata.recommends:
        return {"missing": [], "satisfied": []}

    missing = []
    satisfied = []

    for rec in metadata.recommends:
        if find_skill(rec.name):
            satisfied.append(rec)
        else:
            missing.append(rec)

    return {"missing": missing, "satisfied": satisfied}


def get_recommenders(skill_name: str) -> list[dict]:
    all_skills = find_all_skills()
    recommenders = []

    for skill in all_skills:
        metadata = read_skill_metadata(skill.path)
        if metadata and metadata.recommends:
            for rec in metadata.recommends:
                if rec.name == skill_name:
                    recommenders.append({"name": skill.name, "location": skill.location})
                    break

    return recommenders
