import json
import os
from datetime import datetime

from openskills.models import SkillSourceMetadata

SKILL_METADATA_FILE = '.openskills.json'


def read_skill_metadata(skill_dir: str) -> SkillSourceMetadata | None:
    metadata_path = os.path.join(skill_dir, SKILL_METADATA_FILE)

    if not os.path.exists(metadata_path):
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
            return SkillSourceMetadata(**data)
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

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
