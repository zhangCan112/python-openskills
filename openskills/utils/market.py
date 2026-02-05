"""
Market skills data management
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from openskills.utils.config import get_github_base_url


# Market skills directory (relative to project root)
MARKETSKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'marketskills')


class MarketSkill:
    """Represents a skill from the market"""
    
    def __init__(self, name: str, description: str, repo: str, branch: str, 
                 subpath: str = '', version: str = '', author: str = '', 
                 tags: List[str] = None):
        self.name = name
        self.description = description
        self.repo = repo
        self.branch = branch
        self.subpath = subpath
        self.version = version
        self.author = author
        self.tags = tags or []
    
    @property
    def source(self) -> str:
        """Get source string for installation"""
        # Add GitHub URL prefix if not a full URL and not already containing github.com
        repo = self.repo
        if not repo.startswith('http://') and not repo.startswith('https://') and not repo.startswith('git@'):
            github_base = get_github_base_url()
            # Check if repo already contains the domain (e.g., "github.com/owner/repo")
            if not repo.startswith('github.com/'):
                repo = f"{github_base}/{repo}"
        
        if self.subpath:
            return f"{repo}/{self.subpath}"
        return repo
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'repo': self.repo,
            'branch': self.branch,
            'subpath': self.subpath,
            'version': self.version,
            'author': self.author,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], repo: str, branch: str) -> 'MarketSkill':
        """Create MarketSkill from dictionary"""
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            repo=repo,
            branch=branch,
            subpath=data.get('subpath', ''),
            version=data.get('version', ''),
            author=data.get('author', ''),
            tags=data.get('tags', [])
        )


def load_market_skills() -> List[MarketSkill]:
    """
    Load all market skills from JSON files in marketskills directory
    
    Returns:
        List of MarketSkill objects
    """
    skills = []
    
    # Check if marketskills directory exists
    if not os.path.exists(MARKETSKILLS_DIR):
        return skills
    
    # Load all JSON files in marketskills directory
    for filename in os.listdir(MARKETSKILLS_DIR):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(MARKETSKILLS_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            repo = data.get('repo', '')
            branch = data.get('branch', 'main')
            
            # Load skills from this file
            for skill_data in data.get('skills', []):
                skill = MarketSkill.from_dict(skill_data, repo, branch)
                skills.append(skill)
        
        except (json.JSONDecodeError, KeyError) as e:
            # Skip invalid files silently
            continue
    
    return skills


def find_skill_by_name(name: str) -> List[MarketSkill]:
    """
    Find skills by name (exact match)
    
    Args:
        name: Skill name to search for
        
    Returns:
        List of MarketSkill objects matching the name (may be multiple)
    """
    all_skills = load_market_skills()
    return [skill for skill in all_skills if skill.name.lower() == name.lower()]


def search_skills(keyword: str) -> List[MarketSkill]:
    """
    Search skills by keyword in name, description, or tags
    
    Args:
        keyword: Search keyword
        
    Returns:
        List of MarketSkill objects matching the keyword
    """
    all_skills = load_market_skills()
    keyword_lower = keyword.lower()
    
    matched_skills = []
    for skill in all_skills:
        # Search in name
        if keyword_lower in skill.name.lower():
            matched_skills.append(skill)
            continue
        
        # Search in description
        if keyword_lower in skill.description.lower():
            matched_skills.append(skill)
            continue
        
        # Search in tags
        if any(keyword_lower in tag.lower() for tag in skill.tags):
            matched_skills.append(skill)
            continue
    
    return matched_skills


def list_all_skills() -> List[MarketSkill]:
    """
    List all market skills
    
    Returns:
        List of all MarketSkill objects
    """
    return load_market_skills()


def get_unique_skill_names() -> List[str]:
    """
    Get list of unique skill names
    
    Returns:
        List of unique skill names
    """
    all_skills = load_market_skills()
    unique_names = set(skill.name.lower() for skill in all_skills)
    return sorted(list(unique_names))