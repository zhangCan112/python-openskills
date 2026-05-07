import re


def extract_yaml_field(content: str, field: str) -> str:
    match = re.search(f'^{field}:\\s*(.+?)$', content, re.MULTILINE)
    return match.group(1).strip() if match else ''


def has_valid_frontmatter(content: str) -> bool:
    return content.strip().startswith('---')
