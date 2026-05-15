"""OpenSkills - Universal skills manager for AI coding agents"""

try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version('openskills')
except Exception:
    __version__ = "2.0.0"