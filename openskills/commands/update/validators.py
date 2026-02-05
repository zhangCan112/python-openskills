"""
Update command validators
"""

import os


def is_path_inside(target_path: str, target_dir: str) -> bool:
    """Ensure target path stays within target directory"""
    resolved_target = os.path.abspath(target_path)
    resolved_dir = os.path.abspath(target_dir)
    resolved_dir_sep = resolved_dir if resolved_dir.endswith(os.sep) else resolved_dir + os.sep
    return resolved_target.startswith(resolved_dir_sep)