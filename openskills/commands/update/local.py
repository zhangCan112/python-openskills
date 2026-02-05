"""
Update command local source operations
"""

import os
import click
from openskills.utils import read_skill_metadata, write_skill_metadata
from openskills.utils.yaml import has_valid_frontmatter
from openskills.commands.update.utils import update_skill_from_dir


def update_skill_from_local(target_path: str, metadata, skill_name: str) -> tuple[bool, str]:
    """
    Update skill from local source directory
    
    Args:
        target_path: Target path to update
        metadata: Skill source metadata
        skill_name: Name of the skill
        
    Returns:
        Tuple of (success, error_message)
    """
    local_path = metadata.local_path
    if not local_path or not os.path.exists(local_path):
        return False, 'Local source missing'
    
    skill_md_path = os.path.join(local_path, 'SKILL.md')
    if not os.path.exists(skill_md_path):
        return False, 'SKILL.md missing at local source'
    
    update_skill_from_dir(target_path, local_path)
    write_skill_metadata(target_path, metadata)
    return True, ''