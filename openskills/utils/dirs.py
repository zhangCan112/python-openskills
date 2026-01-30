"""
Directory path management for OpenSkills
"""

import os
from pathlib import Path


def get_skills_dir(project_local: bool = False, universal: bool = False) -> str:
    """
    Get skills directory path
    
    Args:
        project_local: If True, use project directory; otherwise use home directory
        universal: If True, use .agent/skills; otherwise use .claude/skills
    """
    folder = '.agent/skills' if universal else '.claude/skills'
    if project_local:
        return os.path.join(os.getcwd(), folder)
    else:
        return os.path.join(Path.home(), folder)


def get_search_dirs() -> list[str]:
    """
    Get all searchable skill directories in priority order
    Priority: project .agent > global .agent > project .claude > global .claude
    """
    return [
        os.path.join(os.getcwd(), '.agent/skills'),   # 1. Project universal (.agent)
        os.path.join(Path.home(), '.agent/skills'),    # 2. Global universal (.agent)
        os.path.join(os.getcwd(), '.claude/skills'),  # 3. Project claude
        os.path.join(Path.home(), '.claude/skills'),   # 4. Global claude
    ]