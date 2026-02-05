"""
Sync command user interaction prompts
"""

from typing import Any
import click


def prompt_for_selection(message: str, choices: list[dict[str, Any]]) -> list[str]:
    """Prompt user to select from choices"""
    try:
        from questionary import checkbox as q_checkbox
        result = q_checkbox(message, choices=choices).ask()
        return result if result else []
    except ImportError:
        # Fallback to simple input if questionary not available
        click.echo(message)
        for i, choice in enumerate(choices, 1):
            click.echo(f"  {i}. {choice['name']}")
        
        indices_input = click.prompt("Enter numbers (comma-separated, or 'all')", default='all')
        
        if indices_input.strip().lower() == 'all':
            return [choice['value'] for choice in choices]
        
        try:
            indices = [int(x.strip()) for x in indices_input.split(',')]
            return [choices[i-1]['value'] for i in indices if 1 <= i <= len(choices)]
        except ValueError:
            click.echo(click.style("Invalid input. Selecting all skills.", fg='yellow'))
            return [choice['value'] for choice in choices]