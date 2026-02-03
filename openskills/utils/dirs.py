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
    Priority: project .cline > project .clinerules > project .claude > global .cline > project .agent > global .agent > global .claude
    """
    return [
        os.path.join(os.getcwd(), '.cline/skills'),      # 1. Project cline (recommended)
        os.path.join(os.getcwd(), '.clinerules/skills'),  # 2. Project clinerules
        os.path.join(os.getcwd(), '.claude/skills'),      # 3. Project claude (for Claude Code compatibility)
        os.path.join(Path.home(), '.cline/skills'),       # 4. Global cline
        os.path.join(os.getcwd(), '.agent/skills'),       # 5. Project universal (.agent)
        os.path.join(Path.home(), '.agent/skills'),       # 6. Global universal (.agent)
        os.path.join(Path.home(), '.claude/skills'),      # 7. Global claude
    ]
