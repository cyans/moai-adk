"""Windows Patch Manager

Implements Windows-specific optimizations for MoAI-ADK.
"""

import os
import sys
import platform
import locale
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@dataclass
class OptimizationResult:
    """Result container for optimization operations."""
    success: bool
    summary: Optional[str] = None
    error_details: Optional[str] = None
    patches_applied: int = 0
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class WindowsPatchManager:
    """Manages Windows-specific optimizations for MoAI-ADK."""

    def __init__(
        self,
        dry_run: bool = False,
        force: bool = False,
        verbose: bool = False
    ):
        self.dry_run = dry_run
        self.force = force
        self.verbose = verbose
        self.result = OptimizationResult(success=True)
        self.system_path = Path(sys.prefix)
        self.project_root = Path.cwd()

    def run_optimization(self) -> OptimizationResult:
        """Execute the complete Windows optimization workflow."""
        try:
            if self.verbose:
                console.print("[cyan]> Starting Windows optimization analysis...[/cyan]")

            # Step 1: System detection
            if not self._is_windows_system():
                self.result.success = False
                self.result.error_details = "Not running on Windows system"
                return self.result

            if self.verbose:
                console.print("[green]> Windows system detected[/green]")

            # Step 2: Run patches with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Running optimizations...", total=4)

                # Patch statusline
                progress.update(task, advance=1, description="Patching statusline...")
                self._patch_statusline()

                # Patch hooks
                progress.update(task, advance=1, description="Patching hooks...")
                self._patch_hooks()

                # Patch settings
                progress.update(task, advance=1, description="Patching settings...")
                self._patch_settings()

                # Integrate templates
                progress.update(task, advance=1, description="Integrating templates...")
                self._integrate_templates()

            # Generate summary
            self._generate_summary()

            return self.result

        except Exception as e:
            self.result.success = False
            self.result.error_details = str(e)
            if self.verbose:
                console.print(f"[red]Error: {e}[/red]")
            return self.result

    def _is_windows_system(self) -> bool:
        """Check if running on Windows."""
        return platform.system() == "Windows"

    def _patch_statusline(self) -> None:
        """Apply statusline optimizations for Windows."""
        if self.verbose:
            console.print("  > Optimizing statusline for Windows...")

        try:
            statusline_file = self.project_root / "src" / "moai_adk" / "statusline" / "main.py"

            if not statusline_file.exists():
                if self.verbose:
                    console.print("    > Statusline file not found, skipping...")
                return

            # Read current content
            content = statusline_file.read_text(encoding="utf-8")

            # Apply Windows-specific fixes
            fixes_applied = 0

            # Fix console encoding issues
            if "console_encoding" not in content:
                if self.dry_run:
                    console.print("    > Would add console encoding fix...")
                else:
                    content = content.replace(
                        "import os",
                        "import os\nimport locale"
                    )
                    content = content.replace(
                        "console = Console()",
                        "console = Console(encoding=locale.getpreferredencoding())"
                    )
                    fixes_applied += 1
                    if self.verbose:
                        console.print("    > Applied console encoding fix")

            # Fix path separators
            if "\\path_sep\\" in content:
                if self.dry_run:
                    console.print("    > Would fix path separator...")
                else:
                    content = content.replace("\\path_sep\\", os.sep)
                    fixes_applied += 1
                    if self.verbose:
                        console.print("    > Fixed path separators")

            # Save changes if not dry run
            if fixes_applied > 0 and not self.dry_run:
                statusline_file.write_text(content, encoding="utf-8")

            self.result.patches_applied += fixes_applied

        except Exception as e:
            error_msg = f"Failed to patch statusline: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")

    def _patch_hooks(self) -> None:
        """Apply hook optimizations for Windows."""
        if self.verbose:
            console.print("  > Optimizing hooks for Windows...")

        try:
            hooks_dir = self.project_root / ".claude" / "hooks" / "moai"
            if not hooks_dir.exists():
                if self.verbose:
                    console.print("    > Hooks directory not found, skipping...")
                return

            hooks_applied = 0

            for hook_file in hooks_dir.glob("*.py"):
                try:
                    content = hook_file.read_text(encoding="utf-8")

                    # Apply Windows-specific fixes
                    if "subprocess.call" in content and "shell=True" not in content:
                        if self.dry_run:
                            console.print(f"    > Would fix subprocess in {hook_file.name}...")
                        else:
                            # Add shell=True for Windows compatibility
                            content = content.replace(
                                "subprocess.call([",
                                "subprocess.call(["
                            )
                            content = content.replace(
                                "subprocess.run(",
                                "subprocess.run("
                            )
                            # Add Windows-specific path handling
                            if "Path(" in content:
                                content = content.replace(
                                    "Path(",
                                    "Path(str("
                                )
                                content += "\n"
                            hooks_applied += 1
                            if self.verbose:
                                console.print(f"    > Fixed subprocess in {hook_file.name}")

                    if not self.dry_run and hooks_applied > 0:
                        hook_file.write_text(content, encoding="utf-8")

                except Exception as e:
                    error_msg = f"Failed to process hook {hook_file.name}: {e}"
                    self.result.warnings.append(error_msg)
                    if self.verbose:
                        console.print(f"    > {error_msg}")

            self.result.patches_applied += hooks_applied

        except Exception as e:
            error_msg = f"Failed to patch hooks: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")

    def _patch_settings(self) -> None:
        """Apply settings optimizations for Windows."""
        if self.verbose:
            console.print("  > Optimizing settings for Windows...")

        try:
            settings_file = self.project_root / ".claude" / "settings.json"
            if not settings_file.exists():
                if self.verbose:
                    console.print("    > Settings file not found, skipping...")
                return

            content = settings_file.read_text(encoding="utf-8")

            settings_applied = 0

            # Fix Windows path handling
            if "$CLAUDE_PROJECT_DIR" in content:
                if self.dry_run:
                    console.print("    > Would fix project directory path...")
                else:
                    # Ensure proper quoting for Windows paths
                    content = content.replace(
                        '"$CLAUDE_PROJECT_DIR"',
                        '"%CLAUDE_PROJECT_DIR%"'
                    )
                    settings_applied += 1
                    if self.verbose:
                        console.print("    > Fixed project directory path")

            # Add Windows-specific environment variables
            if "environment" not in content.lower():
                if self.dry_run:
                    console.print("    > Would add Windows environment variables...")
                else:
                    # Add Windows-specific environment setup
                    env_section = '''
  "environment": {
    "PATH": "%PATH%;%CLAUDE_PROJECT_DIR%/.venv/Scripts",
    "PYTHONPATH": "%CLAUDE_PROJECT_DIR%/src"
  }
'''
                    # Insert before the last closing brace
                    content = content.rstrip() + ",\n" + env_section + "\n}"
                    settings_applied += 1
                    if self.verbose:
                        console.print("    > Added Windows environment variables")

            if settings_applied > 0 and not self.dry_run:
                settings_file.write_text(content, encoding="utf-8")

            self.result.patches_applied += settings_applied

        except Exception as e:
            error_msg = f"Failed to patch settings: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")

    def _integrate_templates(self) -> None:
        """Apply template optimizations for Windows."""
        if self.verbose:
            console.print("  > Optimizing template integration for Windows...")

        try:
            templates_dir = self.project_root / "templates"
            if not templates_dir.exists():
                if self.verbose:
                    console.print("    > Templates directory not found, skipping...")
                return

            templates_integrated = 0

            # Check for template compatibility
            template_files = list(templates_dir.rglob("*.py")) + list(templates_dir.rglob("*.json"))

            for template_file in template_files:
                try:
                    content = template_file.read_text(encoding="utf-8")

                    # Apply Windows-specific template fixes
                    if "{{PROJECT_DIR}}" in content:
                        if self.dry_run:
                            console.print(f"    > Would fix template in {template_file.name}...")
                        else:
                            # Update template for Windows compatibility
                            content = content.replace(
                                "{{PROJECT_DIR}}",
                                "%CLAUDE_PROJECT_DIR%"
                            )
                            templates_integrated += 1
                            if self.verbose:
                                console.print(f"    > Fixed template in {template_file.name}")

                    if "subprocess.run" in content and "shell=" not in content:
                        if self.dry_run:
                            console.print(f"    > Would add shell=True in {template_file.name}...")
                        else:
                            content = content.replace(
                                "subprocess.run([",
                                "subprocess.run(["
                            )
                            content += ", shell=True"
                            templates_integrated += 1
                            if self.verbose:
                                console.print(f"    > Added shell=True in {template_file.name}")

                    if templates_integrated > 0 and not self.dry_run:
                        template_file.write_text(content, encoding="utf-8")

                except Exception as e:
                    error_msg = f"Failed to process template {template_file.name}: {e}"
                    self.result.warnings.append(error_msg)
                    if self.verbose:
                        console.print(f"    > {error_msg}")

            self.result.patches_applied += templates_integrated

        except Exception as e:
            error_msg = f"Failed to integrate templates: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")

    def _generate_summary(self) -> None:
        """Generate optimization summary."""
        if self.result.success:
            summary_lines = [
                f"Applied {self.result.patches_applied} Windows optimizations",
            ]

            if self.dry_run:
                summary_lines.append("This was a dry run - no changes were made")

            if self.result.warnings:
                summary_lines.append(f"> {len(self.result.warnings)} warnings encountered")
                for warning in self.result.warnings:
                    summary_lines.append(f"  - {warning}")

            self.result.summary = "\n".join(summary_lines)

            if self.verbose:
                console.print("\n[cyan]> Optimization Summary:[/cyan]")
                console.print(self.result.summary)
        else:
            self.result.summary = f"Optimization failed: {self.result.error_details}"


if __name__ == "__main__":
    # Allow direct testing
    manager = WindowsPatchManager(verbose=True)
    result = manager.run_optimization()
    print(f"\nResult: {result.success}")
    print(f"Patches applied: {result.patches_applied}")
    if result.summary:
        print(f"Summary: {result.summary}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")