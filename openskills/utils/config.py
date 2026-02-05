"""
Configuration management for OpenSkills
"""

import os
import yaml
from pathlib import Path


# Default configuration
DEFAULT_GITHUB_HOST = "github.com"
CONFIG_FILE_NAME = "market_sources.yaml"


def get_config_file_path() -> str:
    """
    Get the path to the configuration file
    
    Searches in the following order:
    1. Current working directory
    2. Parent directories up to project root
    3. User home directory
    
    Returns:
        Path to the configuration file, or None if not found
    """
    # Check current directory
    cwd = Path.cwd()
    config_path = cwd / CONFIG_FILE_NAME
    if config_path.exists():
        return str(config_path)
    
    # Check parent directories (up to 5 levels)
    current = cwd
    for _ in range(5):
        parent = current.parent
        if parent == current:  # Reached root
            break
        config_path = parent / CONFIG_FILE_NAME
        if config_path.exists():
            return str(config_path)
        current = parent
    
    # Check user home directory
    home_config = Path.home() / CONFIG_FILE_NAME
    if home_config.exists():
        return str(home_config)
    
    return None


def load_config() -> dict:
    """
    Load configuration from YAML file
    
    Returns:
        Dictionary containing configuration, with defaults if file not found
    """
    config_file = get_config_file_path()
    
    if not config_file or not os.path.exists(config_file):
        # Return defaults if no config file found
        return {
            'github_host': DEFAULT_GITHUB_HOST,
            'sources': []
        }
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        
        # Ensure github_host has a default value
        if 'github_host' not in config:
            config['github_host'] = DEFAULT_GITHUB_HOST
        
        return config
    except Exception:
        # Return defaults if there's an error loading the file
        return {
            'github_host': DEFAULT_GITHUB_HOST,
            'sources': []
        }


def get_github_host() -> str:
    """
    Get the configured GitHub host
    
    Returns:
        GitHub host (e.g., 'github.com', 'github.example.com')
    """
    config = load_config()
    return config.get('github_host', DEFAULT_GITHUB_HOST)


def get_github_base_url() -> str:
    """
    Get the base URL for GitHub
    
    Returns:
        GitHub base URL (e.g., 'https://github.com', 'https://github.example.com')
    """
    host = get_github_host()
    # If it's just a hostname, add https://
    if not host.startswith('http://') and not host.startswith('https://'):
        return f"https://{host}"
    return host