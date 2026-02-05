#!/usr/bin/env python3
"""
Collect skill information from remote repositories and save to market skills database.
This script is for maintainers only.
"""

import os
import sys
import tempfile
import shutil
import subprocess
import json
import re
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path to import openskills modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from openskills.utils.yaml import has_valid_frontmatter, extract_yaml_field


def load_sources_config(config_path: str = "market_sources.yaml") -> Dict[str, Any]:
    """Load market sources configuration from YAML file"""
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        sys.exit(1)


def clone_repo(repo: str, branch: str = None, target_dir: str = None) -> str:
    """Clone a git repository to a temporary directory"""
    temp_dir = tempfile.mkdtemp(prefix="market_skill_")
    
    if target_dir is None:
        target_dir = os.path.join(temp_dir, "repo")
    
    try:
        # repo must be a complete URL
        if not repo.startswith('http://') and not repo.startswith('https://') and not repo.startswith('git@'):
            print(f"Error: Invalid repo format. Expected complete URL, got: {repo}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
        
        cmd = ['git', 'clone', '--depth', '1', '--quiet']
        if branch:
            cmd.extend(['--branch', branch])
        cmd.extend([repo, target_dir])
        
        subprocess.run(cmd, check=True, capture_output=True)
        return target_dir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"Error: Failed to clone {repo}")
        if e.stderr:
            print(e.stderr.decode())
        return None


def parse_tags(tags_str: str) -> List[str]:
    """
    Parse tags from comma-separated string
    
    Args:
        tags_str: Comma-separated tags string (e.g., "development,tools,workflow")
        
    Returns:
        List of tags (empty list if input is None or empty)
    """
    if not tags_str:
        return []
    # Split by comma and strip whitespace from each tag
    tags = [tag.strip() for tag in tags_str.split(',')]
    # Filter out empty tags
    return [tag for tag in tags if tag]


def extract_skill_info(skill_dir: str, repo: str) -> Dict[str, Any] | None:
    """Extract skill information from SKILL.md file"""
    skill_md_path = os.path.join(skill_dir, 'SKILL.md')
    
    if not os.path.exists(skill_md_path):
        return None
    
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not has_valid_frontmatter(content):
        print(f"Warning: Invalid SKILL.md in {skill_dir} (missing YAML frontmatter)")
        return None
    
    skill_name = extract_yaml_field(content, 'name')
    if not skill_name:
        # Use directory name as skill name
        skill_name = os.path.basename(skill_dir)
    
    # Get subpath relative to repo root
    # This will be set later by the caller
    
    # Extract and parse tags (comma-separated string to list)
    tags_str = extract_yaml_field(content, 'tags')
    tags_list = parse_tags(tags_str)
    
    skill_info = {
        'name': skill_name,
        'description': extract_yaml_field(content, 'description') or '',
        'version': extract_yaml_field(content, 'version') or '',
        'author': extract_yaml_field(content, 'author') or '',
        'tags': tags_list
    }
    
    return skill_info


def find_skills_in_repo(repo_dir: str, repo: str, skillspaths: List[str] = None) -> List[Dict[str, Any]]:
    """Find all skills in a repository
    
    Args:
        repo_dir: Path to the repository root
        repo: Repository identifier (e.g., "owner/repo")
        skillspaths: Optional list of paths to search for skills. If None, search entire repo.
    
    Returns:
        List of skill dictionaries
    """
    skills = []
    
    if skillspaths is None:
        # Original behavior: search entire repository
        # Check for root skill
        root_skill_path = os.path.join(repo_dir, 'SKILL.md')
        if os.path.exists(root_skill_path):
            skill_info = extract_skill_info(repo_dir, repo)
            if skill_info:
                skill_info['subpath'] = ''  # Root skill
                skills.append(skill_info)
        
        # Recursively find skills in subdirectories
        for root, dirs, files in os.walk(repo_dir):
            if 'SKILL.md' in files and root != repo_dir:
                skill_info = extract_skill_info(root, repo)
                if skill_info:
                    # Calculate subpath relative to repo root
                    subpath = os.path.relpath(root, repo_dir)
                    skill_info['subpath'] = subpath.replace('\\', '/')  # Normalize path separators
                    skills.append(skill_info)
    else:
        # Search only in specified paths
        for skillspath in skillspaths:
            search_dir = os.path.join(repo_dir, skillspath)
            if not os.path.exists(search_dir):
                print(f"    [!] Warning: Path '{skillspath}' does not exist in repository")
                continue
            
            # Check for skill at this path (if SKILL.md exists directly)
            skill_md_path = os.path.join(search_dir, 'SKILL.md')
            if os.path.exists(skill_md_path):
                skill_info = extract_skill_info(search_dir, repo)
                if skill_info:
                    skill_info['subpath'] = skillspath.replace('\\', '/')
                    skills.append(skill_info)
            
            # Recursively find skills in subdirectories of this path
            for root, dirs, files in os.walk(search_dir):
                if 'SKILL.md' in files and root != search_dir:
                    skill_info = extract_skill_info(root, repo)
                    if skill_info:
                        # Calculate subpath relative to repo root
                        subpath = os.path.relpath(root, repo_dir)
                        skill_info['subpath'] = subpath.replace('\\', '/')
                        skills.append(skill_info)
    
    return skills


def get_repo_branch(repo_dir: str) -> str:
    """Get the current branch of a repository"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return 'main'


def save_market_skills(repo: str, branch: str, skills: List[Dict[str, Any]], output_dir: str) -> None:
    """Save market skills to a JSON file"""
    # Sanitize repo name for filename
    # Remove URL protocol (http:// or https://) if present
    if repo.startswith('http://'):
        repo = repo[7:]
    elif repo.startswith('https://'):
        repo = repo[8:]
    
    # Replace slashes and colons with underscores to create safe filename
    filename = repo.replace('/', '_').replace(':', '_') + '.json'
    filepath = os.path.join(output_dir, filename)
    
    data = {
        'repo': repo,
        'branch': branch,
        'skills': skills
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  [OK] Saved {len(skills)} skill(s) to {filename}")


def collect_from_source(source: Dict[str, Any], output_dir: str) -> None:
    """Collect skills from a single source"""
    repo = source['repo']
    branch = source.get('branch', None)
    skillspath_config = source.get('skillspath', None)
    
    print(f"\n[Collecting] from: {repo}")
    
    # Normalize skillspath to list
    skillspaths = None
    if skillspath_config is not None:
        if isinstance(skillspath_config, str):
            skillspaths = [skillspath_config]
        elif isinstance(skillspath_config, list):
            skillspaths = skillspath_config
        else:
            print(f"  [!] Warning: Invalid skillspath type (expected string or list), ignoring")
    
    # Clone repository
    repo_dir = clone_repo(repo, branch)
    if not repo_dir:
        return
    
    try:
        # Get actual branch (if not specified)
        if not branch:
            branch = get_repo_branch(repo_dir)
        
        # Find all skills
        skills = find_skills_in_repo(repo_dir, repo, skillspaths)
        
        if skills:
            print(f"  Found {len(skills)} skill(s):")
            for skill in skills:
                subpath_info = f" (at '{skill['subpath']}')" if skill['subpath'] else " (root)"
                print(f"    - {skill['name']}{subpath_info}")
            
            # Save to market skills database
            save_market_skills(repo, branch, skills, output_dir)
        else:
            if skillspaths:
                print(f"  [!] No valid skills found in specified paths: {skillspaths}")
            else:
                print(f"  [!] No valid skills found in repository")
    
    finally:
        # Clean up temp directory
        shutil.rmtree(os.path.dirname(repo_dir), ignore_errors=True)


def main():
    """Main function"""
    print("=" * 60)
    print("Market Skills Collector")
    print("=" * 60)
    
    # Load configuration
    config = load_sources_config()
    sources = config.get('sources', [])
    
    if not sources:
        print("\n[!] No sources configured in market_sources.yaml")
        print("Add repositories to the sources list and try again.")
        return
    
    print(f"\nFound {len(sources)} source(s) to process")
    
    # Create output directory
    output_dir = "marketskills"
    os.makedirs(output_dir, exist_ok=True)
    
    # Collect from each source
    success_count = 0
    for source in sources:
        if 'repo' not in source:
            print(f"\n[!] Skipping invalid source (missing 'repo' field)")
            continue
        
        try:
            collect_from_source(source, output_dir)
            success_count += 1
        except Exception as e:
            print(f"\n[ERROR] Error processing {source.get('repo', 'unknown')}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Collection complete: {success_count}/{len(sources)} source(s) processed")
    print(f"Market skills saved to: {output_dir}/")
    print("=" * 60)


if __name__ == '__main__':
    main()