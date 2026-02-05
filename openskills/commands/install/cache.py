"""
Install command cache management
"""

import os
import shutil
import subprocess
import hashlib
from pathlib import Path


def get_cache_dir() -> str:
    """Get the cache directory for cloned repositories"""
    cache_dir = os.path.join(str(Path.home()), '.openskills', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def get_cache_key(repo_url: str) -> str:
    """Generate a cache key from repo URL"""
    # Simple hash of the URL to create a unique directory name
    # Using SHA256 to avoid issues with special characters in URLs
    return hashlib.sha256(repo_url.encode()).hexdigest()[:16]


def clone_to_cache(repo_url: str, cache_path: str) -> str:
    """Clone a repository to cache directory"""
    import click
    import sys
    try:
        click.echo(click.style(f"Cloning repository to cache...", dim=True))
        subprocess.run(
            ['git', 'clone', '--depth', '1', '--quiet', repo_url, cache_path],
            check=True,
            capture_output=True
        )
        click.echo(click.style(f"Repository cloned to cache", fg='green'))
        return cache_path
    except subprocess.CalledProcessError as e:
        click.echo(click.style("Failed to clone repository", fg='red'))
        if e.stderr:
            click.echo(click.style(e.stderr.decode().strip(), dim=True))
        sys.exit(1)


def get_cached_repo(repo_url: str) -> str:
    """
    Get or clone a repository from cache.
    Returns the path to the cached repository.
    """
    import click
    cache_dir = get_cache_dir()
    cache_key = get_cache_key(repo_url)
    cache_path = os.path.join(cache_dir, cache_key)
    
    # Check if cache exists
    if os.path.exists(cache_path):
        # Cache exists, try to update it
        try:
            click.echo(click.style(f"Updating cached repository...", dim=True))
            subprocess.run(
                ['git', 'fetch', '--quiet'],
                cwd=cache_path,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ['git', 'checkout', '--quiet', 'main'],
                cwd=cache_path,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ['git', 'pull', '--quiet'],
                cwd=cache_path,
                check=True,
                capture_output=True
            )
            click.echo(click.style(f"Cache updated", fg='green'))
        except subprocess.CalledProcessError:
            # Update failed, remove and re-clone
            click.echo(click.style("Cache update failed, recloning...", fg='yellow'))
            shutil.rmtree(cache_path, ignore_errors=True)
            return clone_to_cache(repo_url, cache_path)
        
        return cache_path
    else:
        # Cache doesn't exist, clone it
        return clone_to_cache(repo_url, cache_path)