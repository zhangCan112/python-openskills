"""
Update command Git operations
"""

import os
import subprocess
import tempfile
import click
from openskills.utils import read_skill_metadata, write_skill_metadata
from openskills.utils.yaml import has_valid_frontmatter
from openskills.commands.update.utils import update_skill_from_dir


def update_skill_from_git(target_path: str, metadata, skill_name: str) -> tuple[bool, str]:
    """
    Update skill from Git repository
    
    Args:
        target_path: Target path to update
        metadata: Skill source metadata
        skill_name: Name of the skill
        
    Returns:
        Tuple of (success, error_message)
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', '--quiet', metadata.repo_url, os.path.join(temp_dir, 'repo')],
                check=True,
                capture_output=True
            )
            
            repo_dir = os.path.join(temp_dir, 'repo')
            subpath = metadata.subpath if metadata.subpath and metadata.subpath != '.' else ''
            source_dir = os.path.join(repo_dir, subpath) if subpath else repo_dir
            
            skill_md_path = os.path.join(source_dir, 'SKILL.md')
            if not os.path.exists(skill_md_path):
                return False, f"SKILL.md not found in repo at {subpath or '.'}"
            
            update_skill_from_dir(target_path, source_dir)
            write_skill_metadata(target_path, metadata)
            return True, ''
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else 'Unknown error'
            return False, f"git clone failed: {error_msg}"