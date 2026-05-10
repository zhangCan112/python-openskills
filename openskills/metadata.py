import json
import os
from datetime import datetime

from openskills.models import SkillDependency, SkillSourceMetadata

SKILL_METADATA_FILE = '.openskills.json'


def read_skill_metadata(skill_dir: str) -> SkillSourceMetadata | None:
    metadata_path = os.path.join(skill_dir, SKILL_METADATA_FILE)

    if not os.path.exists(metadata_path):
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
            depends_on = None
            if 'depends_on' in data and data['depends_on']:
                depends_on = [SkillDependency(**d) for d in data['depends_on']]
            return SkillSourceMetadata(
                source=data['source'],
                source_type=data['source_type'],
                repo_url=data.get('repo_url'),
                subpath=data.get('subpath'),
                local_path=data.get('local_path'),
                installed_at=data.get('installed_at'),
                depends_on=depends_on,
            )
    except Exception:
        return None


def write_skill_metadata(skill_dir: str, metadata: SkillSourceMetadata) -> None:
    metadata_path = os.path.join(skill_dir, SKILL_METADATA_FILE)

    payload = {
        'source': metadata.source,
        'source_type': metadata.source_type,
        'repo_url': metadata.repo_url,
        'subpath': metadata.subpath,
        'local_path': metadata.local_path,
        'installed_at': metadata.installed_at or datetime.now().isoformat(),
    }

    if metadata.depends_on is not None:
        payload['depends_on'] = [
            {'name': d.name, 'source': d.source} for d in metadata.depends_on
        ]

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
