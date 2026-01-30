"""
YAML parsing and validation utilities
"""

import re


def extract_yaml_field(content: str, field: str) -> str:
    """
    Extract field from YAML frontmatter
    
    Args:
        content: The content to search in
        field: The field name to extract
        
    Returns:
        The field value or empty string if not found
    """
    match = re.search(f'^{field}:\\s*(.+?)$', content, re.MULTILINE)
    return match.group(1).strip() if match else ''


def has_valid_frontmatter(content: str) -> bool:
    """
    Validate SKILL.md has proper YAML frontmatter
    
    Args:
        content: The content to validate
        
    Returns:
        True if content starts with '---', False otherwise
    """
    return content.strip().startswith('---')