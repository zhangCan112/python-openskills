"""
Command modules for OpenSkills
"""

from openskills.commands.list import list_skills
from openskills.commands.remove import remove_skill
from openskills.commands.read import read_skill
from openskills.commands.install import install_skill
from openskills.commands.update import update_skills
from openskills.commands.sync import sync_agents_md
from openskills.commands.manage import manage_skills
from openskills.commands.compat import compat_export

__all__ = [
    'list_skills',
    'remove_skill',
    'read_skill',
    'install_skill',
    'update_skills',
    'sync_agents_md',
    'manage_skills',
    'compat_export',
]
