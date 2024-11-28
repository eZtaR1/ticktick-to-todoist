"""
Command-line interface for the TickTick to Todoist converter.
"""
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress

from .converter import TickTickToTodoistConverter
from .utils import ensure_path

console = Console()

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file (default: todoist_import.csv)')
@click.option('--no-priority', is_flag=True, help='Disable priority mapping')
def main(input_file: str, output: Optional[str], no_priority: bool) -> None:
    """Convert TickTick backup CSV to Todoist import format."""
    try:
        input_path = ensure_path(input_file)
        output_path = Path(output) if output else None
        
        # Initialize converter
        converter = TickTickToTodoistConverter(include_priority=not no_priority)
        
        # Convert file
        output_file = converter.convert(input_path, output_path)
        
        console.print(f"\n✅ Created [green]{output_file}[/green]")
        console.print(f"Priority mapping is {'[red]disabled' if no_priority else '[green]enabled'}[/]")
        
    except Exception as e:
        console.print(f"\n❌ Error: [red]{str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    main()
