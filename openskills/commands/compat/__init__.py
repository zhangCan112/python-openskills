"""
Compatibility export command for AI tools that don't support AGENTS.md
"""

from openskills.commands.compat.handlers import compat_export, sync_to_targets
from openskills.commands.compat.utils import list_active_targets

__all__ = ['compat_export', 'sync_to_targets', 'list_active_targets']