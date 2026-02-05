"""
Compatibility command utilities
"""

import os
from openskills.commands.compat.config import TARGETS


def list_active_targets() -> list[str]:
    """
    List targets that have been previously configured
    
    Returns:
        List of target names that have configuration files
    """
    active_targets = []
    for target_name, config in TARGETS.items():
        if os.path.exists(config['path']):
            active_targets.append(target_name)
    return active_targets