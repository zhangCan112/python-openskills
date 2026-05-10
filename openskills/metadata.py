import json
import os
from datetime import datetime

from openskills.models import SkillRecommendation, SkillSourceMetadata

SKILL_METADATA_FILE = '.openskills.json'


def read_skill_metadata(skill_dir: str) -> SkillSourceMetadata | None:
    metadata_path = os.path.join(skill_dir, SKILL_METADATA_FILE)

    if not os.path.exists(metadata_path):
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
            recommends = None
            if 'recommends' in data and data['recommends']:
                recommends = [SkillRecommendation(**d) for d in data['recommends']]
            return SkillSourceMetadata(
                source=data['source'],
                source_type=data['source_type'],
                repo_url=data.get('repo_url'),
                subpath=data.get('subpath'),
                local_path=data.get('local_path'),
                installed_at=data.get('installed_at'),
                recommends=recommends,
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

    if metadata.recommends is not None:
        payload['recommends'] = [
            {'name': d.name, 'source': d.source} for d in metadata.recommends
        ]

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
