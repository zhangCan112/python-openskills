"""
Skill finding and management utilities
"""

import os
from pathlib import Path

from openskills.types import Skill, SkillLocationInfo
from openskills.utils.dirs import get_search_dirs
from openskills.utils.yaml import extract_yaml_field


def is_directory_or_symlink_to_directory(entry: os.DirEntry, parent_dir: str) -> bool:
    """
    Check if a directory entry is a directory or a symlink pointing to a directory
    
    Args:
        entry: Directory entry to check
        parent_dir: Parent directory path
        
    Returns:
        True if entry is a directory or symlink to directory
    """
    if entry.is_dir():
        return True
    
    if entry.is_symlink():
        try:
            full_path = os.path.join(parent_dir, entry.name)
            stats = os.stat(full_path)  # stat follows symlinks
            return os.path.isdir(full_path)
        except Exception:
            # Broken symlink or permission error
            return False
    return False


def find_all_skills() -> list[Skill]:
    """
    Find all installed skills across directories
    
    Returns:
        List of Skill objects found
    """
    skills: list[Skill] = []
    seen = set()
    dirs = get_search_dirs()
    
    for directory in dirs:
        if not os.path.exists(directory):
            continue
        
        try:
            entries = os.scandir(directory)
        except OSError:
            continue
        
        for entry in entries:
            if is_directory_or_symlink_to_directory(entry, directory):
                # Deduplicate: only add if we haven't seen this skill name yet
                if entry.name in seen:
                    continue
                
                skill_path = os.path.join(directory, entry.name, 'SKILL.md')
                if os.path.exists(skill_path):
                    with open(skill_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    is_project_local = os.getcwd() in directory
                    
                    skills.append(Skill(
                        name=entry.name,
                        description=extract_yaml_field(content, 'description'),
                        location='project' if is_project_local else 'global',
                        path=os.path.join(directory, entry.name)
                    ))
                    
                    seen.add(entry.name)
    
    return skills


def find_skill(skill_name: str) -> SkillLocationInfo | None:
    """
    Find specific skill by name
    
    Args:
        skill_name: Name of the skill to find
        
    Returns:
        SkillLocationInfo object or None if not found
    """
    dirs = get_search_dirs()
    
    for directory in dirs:
        skill_path = os.path.join(directory, skill_name, 'SKILL.md')
        if os.path.exists(skill_path):
            return SkillLocationInfo(
                path=skill_path,
                base_dir=os.path.join(directory, skill_name),
                source=directory
            )
    
    return None