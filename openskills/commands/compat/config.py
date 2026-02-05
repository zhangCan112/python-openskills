"""
Compatibility command configuration
"""

# Define target configurations
TARGETS = {
    'copilot': {
        'path': '.github/instructions/openskills.instructions.md',
        'description': 'GitHub Copilot',
        'format': 'markdown'
    },
    'cline': {
        'path': '.clinerules/openskills.md',
        'description': 'Cline',
        'format': 'text'
    }
}