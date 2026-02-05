"""
AGENTS.md generation and update utilities
"""

import os
import platform
import re
import shutil
from typing import Any

from openskills.skill_types import Skill


def parse_current_skills(content: str) -> list[str]:
    """
    Parse skill names currently in AGENTS.md
    
    Args:
        content: Content of AGENTS.md file
        
    Returns:
        List of skill names found
    """
    skill_names: list[str] = []
    
    # Match <skill><name>skill-name</name>...</skill>
    skill_regex = re.compile(r'<skill>[\s\S]*?<name>([^<]+)<\/name>[\s\S]*?<\/skill>')
    
    for match in skill_regex.finditer(content):
        skill_names.append(match.group(1).strip())
    
    return skill_names


def get_installation_method() -> tuple[str, str]:
    """
    Detect how OpenSkills is installed and return appropriate command format
    
    Returns:
        Tuple of (command_prefix, command_description)
        - command_prefix: The actual command to use (e.g., 'openskills', 'openskills.bat', './openskills.sh')
        - command_description: Human-readable description of the command format
    """
    is_windows = platform.system() == 'Windows'
    
    # Check for project-level installation scripts
    if is_windows:
        script_path = 'openskills.bat'
    else:
        script_path = './openskills.sh'
    
    # Check if script exists in current directory
    if os.path.exists(script_path):
        if is_windows:
            return 'openskills.bat', 'openskills.bat read <skill-name>'
        else:
            return './openskills.sh', './openskills.sh read <skill-name>'
    
    # Check if openskills command is available globally (in PATH)
    openskills_in_path = shutil.which('openskills')
    if openskills_in_path:
        return 'openskills', 'openskills read <skill-name>'
    
    # Fallback: assume global openskills command
    return 'openskills', 'openskills read <skill-name>'


def generate_skills_xml(skills: list[Skill]) -> str:
    """
    Generate skills XML section for AGENTS.md
    
    Args:
        skills: List of Skill objects
        
    Returns:
        XML-formatted skills section
    """
    # Detect installation method and generate appropriate command
    command_prefix, command_syntax = get_installation_method()
    multiple_syntax = f'{command_prefix} read skill-one,skill-two'
    
    skill_tags = '\n\n'.join([
        f"""<skill>
<name>{skill.name}</name>
<description>{skill.description}</description>
<location>{skill.location}</location>
</skill>"""
        for skill in skills
    ])
    
    return f"""<skills_system priority="1">

## Available Skills

<!-- SKILLS_TABLE_START -->
<usage>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

How to use skills:
- Invoke: {command_syntax} (run in your shell)
  - For multiple: {multiple_syntax}
- The skill content will load with detailed instructions on how to complete the task
- Base directory provided in output for resolving bundled resources (references/, scripts/, assets/)

Usage notes:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already loaded in your context
- Each skill invocation is stateless
</usage>

<available_skills>

{skill_tags}

</available_skills>
<!-- SKILLS_TABLE_END -->

</skills_system>"""


def replace_skills_section(content: str, new_section: str) -> str:
    """
    Replace or add skills section in AGENTS.md
    
    Args:
        content: Current content of AGENTS.md
        new_section: New skills section to insert
        
    Returns:
        Updated content
    """
    start_marker = '<skills_system'
    end_marker = '</skills_system>'
    
    # Check for XML markers
    if start_marker in content:
        regex = re.compile(r'<skills_system[^>]*>[\s\S]*?</skills_system>')
        return regex.sub(new_section, content)
    
    # Fallback to HTML comments
    html_start_marker = '<!-- SKILLS_TABLE_START -->'
    html_end_marker = '<!-- SKILLS_TABLE_END -->'
    
    if html_start_marker in content:
        # Extract content without outer XML wrapper
        inner_content = re.sub(r'<skills_system[^>]*>|</skills_system>', '', new_section)
        regex = re.compile(
            re.escape(html_start_marker) + r'[\s\S]*?' + re.escape(html_end_marker)
        )
        return regex.sub(f'{html_start_marker}\n{inner_content}\n{html_end_marker}', content)
    
    # No markers found - append to end of file
    return content.rstrip() + '\n\n' + new_section + '\n'


def remove_skills_section(content: str) -> str:
    """
    Remove skills section from AGENTS.md
    
    Args:
        content: Current content of AGENTS.md
        
    Returns:
        Updated content with skills section removed
    """
    start_marker = '<skills_system'
    end_marker = '</skills_system>'
    
    # Check for XML markers
    if start_marker in content:
        regex = re.compile(r'<skills_system[^>]*>[\s\S]*?</skills_system>')
        return regex.sub('<!-- Skills section removed -->', content)
    
    # Fallback to HTML comments
    html_start_marker = '<!-- SKILLS_TABLE_START -->'
    html_end_marker = '<!-- SKILLS_TABLE_END -->'
    
    if html_start_marker in content:
        regex = re.compile(
            re.escape(html_start_marker) + r'[\s\S]*?' + re.escape(html_end_marker)
        )
        return regex.sub(f'{html_start_marker}\n<!-- Skills section removed -->\n{html_end_marker}', content)
    
    # No markers found - nothing to remove
    return content