"""Windows Optimization Command

Implements the `moai-adk windows-optimize` command for Windows-specific optimizations.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from moai_adk.platform_windows.windows_patch import WindowsPatchManager

console = Console()


@click.command(
    name="windows-optimize",
    help="Apply Windows-specific optimizations to MoAI-ADK",
    short_help="Optimize MoAI-ADK for Windows environment"
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=None,
    help="Project path (default: auto-detect from current directory)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be optimized without making changes",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force optimization even if system checks pass",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed optimization information",
)
@click.pass_context
def windows_optimize(
    ctx: click.Context,
    path: Optional[str],
    dry_run: bool,
    force: bool,
    verbose: bool,
) -> None:
    """Apply Windows-specific optimizations to MoAI-ADK.

    This command analyzes the Windows environment and applies targeted
    optimizations for:
    - Statusline rendering improvements (creates statusline-runner.py)
    - Hook script compatibility (adds UTF-8 encoding support)
    - Settings configuration (updates paths for Windows)
    - MCP server configuration (adds cmd /c wrapper for npx)
    
    The command automatically detects the MoAI-ADK project root by searching
    for the .moai directory. You can also specify a path with --path.
    
    Examples:
        moai-adk windows-optimize              # Optimize current project
        moai-adk windows-optimize --path ./my-project
        moai-adk windows-optimize --dry-run    # Preview changes
        moai-adk windows-optimize --verbose    # Show detailed output
    """
    try:
        # Convert path to Path object if provided
        project_path = Path(path).resolve() if path else None
        
        # Initialize Windows patch manager
        patch_manager = WindowsPatchManager(
            project_path=project_path,
            dry_run=dry_run,
            force=force,
            verbose=verbose
        )

        # Run optimization
        result = patch_manager.run_optimization()

        # Display results
        if result.success:
            display_success(result, dry_run, verbose)
        else:
            display_error(result, verbose)

    except Exception as e:
        console.print(f"[red]Error during Windows optimization:[/red] {e}")
        raise click.ClickException(str(e))


def display_success(result, dry_run: bool, verbose: bool) -> None:
    """Display successful optimization results."""
    console.print(Panel.fit(
        "[green]Windows optimization completed successfully![/green]",
        title="Optimization Status",
        border_style="green"
    ))

    if dry_run:
        console.print("[yellow]This was a dry run - no changes were made.[/yellow]")

    if verbose and result.summary:
        console.print("\n[cyan]Optimization Summary:[/cyan]")
        console.print(result.summary)


def display_error(result, verbose: bool) -> None:
    """Display optimization error results."""
    console.print(Panel.fit(
        "[red]Windows optimization failed![/red]",
        title="Optimization Status",
        border_style="red"
    ))

    if verbose and result.error_details:
        console.print(f"\n[red]Error Details:[/red]")
        console.print(result.error_details)


class OptimizationResult:
    """Result container for optimization operations."""

    def __init__(
        self,
        success: bool,
        summary: Optional[str] = None,
        error_details: Optional[str] = None,
        patches_applied: int = 0
    ):
        self.success = success
        self.summary = summary
        self.error_details = error_details
        self.patches_applied = patches_applied


if __name__ == "__main__":
    # Allow direct execution for testing
    windows_optimize.main(sys.argv[1:])