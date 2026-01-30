"""
Skill metadata reading and writing utilities
"""

import json
import os
from typing import Any

from openskills.types import SkillSourceMetadata

SKILL_METADATA_FILE = '.openskills.json'


def read_skill_metadata(skill_dir: str) -> SkillSourceMetadata | None:
    """
    Read skill metadata from .openskills.json file
    
    Args:
        skill_dir: Directory containing the skill
        
    Returns:
        SkillSourceMetadata object or None if file doesn't exist or is invalid
    """
    metadata_path = os.path.join(skill_dir, SKILL_METADATA_FILE)
    
    if not os.path.exists(metadata_path):
        return None
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            raw = f.read()
            data = json.loads(raw)
            return SkillSourceMetadata(**data)
    except Exception:
        return None


def write_skill_metadata(skill_dir: str, metadata: SkillSourceMetadata) -> None:
    """
    Write skill metadata to .openskills.json file
    
    Args:
        skill_dir: Directory containing the skill
        metadata: SkillSourceMetadata object to write
    """
    metadata_path = os.path.join(skill_dir, SKILL_METADATA_FILE)
    
    payload = {
        'source': metadata.source,
        'source_type': metadata.source_type,
        'repo_url': metadata.repo_url,
        'subpath': metadata.subpath,
        'local_path': metadata.local_path,
        'installed_at': metadata.installed_at or datetime_now()
    }
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)


def datetime_now() -> str:
    """Get current datetime in ISO format"""
    from datetime import datetime
    return datetime.now().isoformat()