"""Windows Patch Manager

Implements Windows-specific optimizations for MoAI-ADK.
"""

import os
import sys
import platform
import json
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
        project_path: Optional[Path] = None,
        dry_run: bool = False,
        force: bool = False,
        verbose: bool = False
    ):
        self.dry_run = dry_run
        self.force = force
        self.verbose = verbose
        self.result = OptimizationResult(success=True)
        
        # Find project root (look for .moai directory)
        if project_path:
            self.project_root = Path(project_path).resolve()
        else:
            self.project_root = self._find_project_root()
        
        if not self.project_root:
            self.result.success = False
            self.result.error_details = "Could not find MoAI-ADK project root (.moai directory not found)"
    
    def _find_project_root(self) -> Optional[Path]:
        """Find MoAI-ADK project root by searching for .moai directory."""
        current = Path.cwd().resolve()
        max_depth = 10
        
        for _ in range(max_depth):
            if (current / ".moai").is_dir():
                if self.verbose:
                    console.print(f"[cyan]Found project root: {current}[/cyan]")
                return current
            if current == current.parent:
                break
            current = current.parent
        
        # Fallback: check if current directory has .claude or CLAUDE.md
        current = Path.cwd().resolve()
        if (current / ".claude").is_dir() or (current / "CLAUDE.md").exists():
            if self.verbose:
                console.print(f"[yellow]Using current directory as project root: {current}[/yellow]")
            return current
        
        return None

    def run_optimization(self) -> OptimizationResult:
        """Execute the complete Windows optimization workflow."""
        try:
            if not self.project_root:
                return self.result
            
            if self.verbose:
                console.print(f"[cyan]> Starting Windows optimization for: {self.project_root}[/cyan]")

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
                task = progress.add_task("Running optimizations...", total=5)

                # Patch statusline-runner.py
                progress.update(task, advance=1, description="Creating statusline-runner.py...")
                self._patch_statusline_runner()

                # Patch hooks
                progress.update(task, advance=1, description="Patching hooks...")
                self._patch_hooks()

                # Patch settings.json
                progress.update(task, advance=1, description="Patching settings.json...")
                self._patch_settings()

                # Patch mcp.json
                progress.update(task, advance=1, description="Patching mcp.json...")
                self._patch_mcp_json()

                # Verify optimizations
                progress.update(task, advance=1, description="Verifying optimizations...")
                self._verify_optimizations()

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
        return platform.system() == "Windows" or sys.platform == "win32"

    def _patch_statusline_runner(self) -> None:
        """Create or update statusline-runner.py with Windows UTF-8 encoding support."""
        if self.verbose:
            console.print("  > Creating/updating statusline-runner.py...")

        try:
            scripts_dir = self.project_root / ".moai" / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            statusline_runner = scripts_dir / "statusline-runner.py"
            
            # Content for statusline-runner.py (based on working example)
            content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statusline runner with UTF-8 encoding support for Windows
"""
import os
import sys
import subprocess

# UTF-8 환경 변수 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Windows에서 콘솔 코드 페이지를 UTF-8로 설정
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
    except Exception:
        pass

# moai-adk statusline 실행
try:
    result = subprocess.run(
        ['uv', 'run', 'moai-adk', 'statusline'],
        env=os.environ,
        stdout=sys.stdout,
        stderr=sys.stderr,
        encoding='utf-8',
        errors='replace'
    )
    sys.exit(result.returncode)
except Exception as e:
    print(f"Error running statusline: {e}", file=sys.stderr)
    sys.exit(1)
'''
            
            if self.dry_run:
                console.print("    > Would create/update statusline-runner.py")
            else:
                statusline_runner.write_text(content, encoding="utf-8")
                self.result.patches_applied += 1
                if self.verbose:
                    console.print("    > Created/updated statusline-runner.py")

        except Exception as e:
            error_msg = f"Failed to create statusline-runner.py: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")

    def _patch_hooks(self) -> None:
        """Add UTF-8 encoding support to hook files."""
        if self.verbose:
            console.print("  > Optimizing hooks for Windows...")

        try:
            hooks_dir = self.project_root / ".claude" / "hooks" / "moai"
            if not hooks_dir.exists():
                if self.verbose:
                    console.print("    > Hooks directory not found, skipping...")
                return

            hooks_applied = 0
            utf8_setup = '''# UTF-8 환경 변수 설정 (Windows 호환성)
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Windows에서 콘솔 코드 페이지를 UTF-8로 설정
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # UTF-8
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    except Exception:
        pass
'''

            for hook_file in hooks_dir.glob("*.py"):
                try:
                    content = hook_file.read_text(encoding="utf-8")
                    original_content = content
                    modified = False

                    # Check if UTF-8 encoding setup is already present
                    if "PYTHONIOENCODING" not in content:
                        # Find insertion point (after imports and docstrings)
                        lines = content.split('\n')
                        insert_idx = 0
                        in_docstring = False
                        docstring_char = None
                        
                        for i, line in enumerate(lines):
                            # Track docstrings
                            if '"""' in line or "'''" in line:
                                if not in_docstring:
                                    in_docstring = True
                                    docstring_char = '"""' if '"""' in line else "'''"
                                elif docstring_char in line:
                                    in_docstring = False
                                continue
                            
                            # Skip docstrings
                            if in_docstring:
                                continue
                            
                            # Find last import statement
                            if line.strip().startswith('import ') or line.strip().startswith('from '):
                                insert_idx = i + 1
                            # Stop at first non-import, non-comment, non-empty line
                            elif line.strip() and not line.strip().startswith('#'):
                                break
                        
                        # Insert UTF-8 encoding setup after imports
                        lines.insert(insert_idx, utf8_setup)
                        content = '\n'.join(lines)
                        modified = True

                    # Fix subprocess.run calls to include encoding (simple pattern matching)
                    if "subprocess.run" in content:
                        import re
                        # Pattern: subprocess.run(..., ...) - match common patterns
                        # Look for subprocess.run calls without encoding parameter
                        patterns_to_fix = [
                            # Pattern: subprocess.run([...])
                            (r"subprocess\.run\((\[[^\]]+\])(\s*)\)", r"subprocess.run(\1\2, encoding='utf-8', errors='replace')"),
                            # Pattern: subprocess.run([...], ...) without encoding
                            (r"subprocess\.run\((\[[^\]]+\])(,\s*)([^,)]+)(\))(?!.*encoding=)", 
                             lambda m: f"subprocess.run({m.group(1)}{m.group(2)}{m.group(3)}, encoding='utf-8', errors='replace'{m.group(4)}"),
                        ]
                        
                        for pattern, replacement in patterns_to_fix:
                            if callable(replacement):
                                new_content = re.sub(pattern, replacement, content)
                            else:
                                new_content = re.sub(pattern, replacement, content)
                            
                            if new_content != content:
                                content = new_content
                                modified = True
                                break

                    if modified and not self.dry_run:
                        hook_file.write_text(content, encoding="utf-8")
                        hooks_applied += 1
                        if self.verbose:
                            console.print(f"    > Patched {hook_file.name}")

                except Exception as e:
                    error_msg = f"Failed to process hook {hook_file.name}: {e}"
                    self.result.warnings.append(error_msg)
                    if self.verbose:
                        console.print(f"    > {error_msg}")

            if hooks_applied > 0:
                self.result.patches_applied += hooks_applied

        except Exception as e:
            error_msg = f"Failed to patch hooks: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")

    def _patch_settings(self) -> None:
        """Update settings.json with Windows-optimized paths."""
        if self.verbose:
            console.print("  > Optimizing settings.json for Windows...")

        try:
            settings_file = self.project_root / ".claude" / "settings.json"
            if not settings_file.exists():
                if self.verbose:
                    console.print("    > Settings file not found, skipping...")
                return

            # Read and parse JSON - handle malformed JSON
            content = settings_file.read_text(encoding="utf-8")
            
            # Fix common JSON issues (trailing comma, extra data)
            # Remove trailing comma before closing brace
            content = content.rstrip()
            # Remove any content after the main JSON object
            if '},\n\n  "environment"' in content:
                # This is a malformed JSON - fix it
                content = content.split('},\n\n  "environment"')[0] + '\n}'
            
            try:
                settings = json.loads(content)
            except json.JSONDecodeError:
                # Try to fix by removing the last part
                lines = content.split('\n')
                # Find the last valid closing brace
                brace_count = 0
                last_valid_line = len(lines) - 1
                for i, line in enumerate(lines):
                    brace_count += line.count('{') - line.count('}')
                    if brace_count == 0 and i > 0:
                        last_valid_line = i
                        break
                
                content = '\n'.join(lines[:last_valid_line + 1])
                settings = json.loads(content)
            
            modified = False

            # Fix statusline command
            if "statusLine" in settings:
                statusline_cmd = settings["statusLine"].get("command", "")
                # Update to use statusline-runner.py with Windows path
                expected_cmd = 'uv run python %CLAUDE_PROJECT_DIR%/.moai/scripts/statusline-runner.py'
                if statusline_cmd != expected_cmd and "$CLAUDE_PROJECT_DIR" in statusline_cmd:
                    settings["statusLine"]["command"] = expected_cmd
                    modified = True
                    if self.verbose:
                        console.print("    > Updated statusline command")

            # Fix hook commands
            if "hooks" in settings:
                hook_types = ["SessionStart", "PreToolUse", "SessionEnd"]
                for hook_type in hook_types:
                    if hook_type in settings["hooks"]:
                        for hook_group in settings["hooks"][hook_type]:
                            if "hooks" in hook_group:
                                for hook in hook_group["hooks"]:
                                    if hook.get("type") == "command":
                                        cmd = hook.get("command", "")
                                        # Update to use %CLAUDE_PROJECT_DIR% for Windows
                                        if "$CLAUDE_PROJECT_DIR" in cmd:
                                            new_cmd = cmd.replace("$CLAUDE_PROJECT_DIR", "%CLAUDE_PROJECT_DIR%")
                                            # Remove quotes around variable if present
                                            new_cmd = new_cmd.replace('"%CLAUDE_PROJECT_DIR%"', '%CLAUDE_PROJECT_DIR%')
                                            hook["command"] = new_cmd
                                            modified = True
                                            if self.verbose:
                                                console.print(f"    > Updated {hook_type} hook command")

            if modified and not self.dry_run:
                # Write back with proper formatting
                settings_file.write_text(
                    json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8"
                )
                self.result.patches_applied += 1
                if self.verbose:
                    console.print("    > Updated settings.json")

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse settings.json: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")
            # Try to fix the JSON file
            try:
                self._fix_settings_json()
            except Exception as fix_error:
                if self.verbose:
                    console.print(f"    > Failed to auto-fix settings.json: {fix_error}")
        except Exception as e:
            error_msg = f"Failed to patch settings.json: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")
    
    def _fix_settings_json(self) -> None:
        """Try to fix malformed settings.json file."""
        settings_file = self.project_root / ".claude" / "settings.json"
        content = settings_file.read_text(encoding="utf-8")
        
        # Remove everything after the main JSON object
        lines = content.split('\n')
        new_lines = []
        brace_count = 0
        in_string = False
        escape_next = False
        
        for line in lines:
            if brace_count == 0 and line.strip() and not line.strip().startswith('{'):
                # We've closed the main object, stop here
                break
            
            for char in line:
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
            
            new_lines.append(line)
            
            if brace_count == 0 and new_lines:
                break
        
        # Write fixed content
        fixed_content = '\n'.join(new_lines)
        if not fixed_content.rstrip().endswith('}'):
            fixed_content += '\n}'
        
        settings_file.write_text(fixed_content, encoding="utf-8")

    def _patch_mcp_json(self) -> None:
        """Update .mcp.json with Windows-optimized npx commands (cmd /c wrapper)."""
        if self.verbose:
            console.print("  > Optimizing .mcp.json for Windows...")

        try:
            mcp_file = self.project_root / ".mcp.json"
            if not mcp_file.exists():
                if self.verbose:
                    console.print("    > .mcp.json not found, skipping...")
                return

            # Read and parse JSON
            content = mcp_file.read_text(encoding="utf-8")
            mcp_config = json.loads(content)
            modified = False

            if "mcpServers" in mcp_config:
                for server_name, server_config in mcp_config["mcpServers"].items():
                    # Skip SSE servers
                    if server_config.get("type") == "sse":
                        continue
                    
                    # Check if command is npx and needs Windows wrapper
                    command = server_config.get("command", "")
                    args = server_config.get("args", [])
                    
                    if command == "npx" or (isinstance(args, list) and len(args) > 0 and args[0] == "npx"):
                        # Convert to Windows format: cmd /c npx ...
                        server_config["command"] = "cmd"
                        if isinstance(args, list):
                            # Insert /c before npx
                            if args[0] == "npx":
                                server_config["args"] = ["/c"] + args
                            else:
                                server_config["args"] = ["/c", "npx"] + args[1:]
                        else:
                            server_config["args"] = ["/c", "npx"] + (args if isinstance(args, list) else [args])
                        
                        modified = True
                        if self.verbose:
                            console.print(f"    > Updated {server_name} MCP server for Windows")

            if modified and not self.dry_run:
                # Write back with proper formatting
                mcp_file.write_text(
                    json.dumps(mcp_config, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8"
                )
                self.result.patches_applied += 1
                if self.verbose:
                    console.print("    > Updated .mcp.json")

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse .mcp.json: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")
        except Exception as e:
            error_msg = f"Failed to patch .mcp.json: {e}"
            self.result.warnings.append(error_msg)
            if self.verbose:
                console.print(f"    > {error_msg}")

    def _verify_optimizations(self) -> None:
        """Verify that optimizations were applied correctly."""
        if self.verbose:
            console.print("  > Verifying optimizations...")

        checks_passed = 0
        checks_failed = 0

        # Check statusline-runner.py
        statusline_runner = self.project_root / ".moai" / "scripts" / "statusline-runner.py"
        if statusline_runner.exists():
            checks_passed += 1
            if self.verbose:
                console.print("    > [OK] statusline-runner.py exists")
        else:
            checks_failed += 1
            if self.verbose:
                console.print("    > [FAIL] statusline-runner.py not found")

        # Check settings.json
        settings_file = self.project_root / ".claude" / "settings.json"
        if settings_file.exists():
            try:
                content = settings_file.read_text(encoding="utf-8")
                if "%CLAUDE_PROJECT_DIR%" in content:
                    checks_passed += 1
                    if self.verbose:
                        console.print("    > [OK] settings.json uses Windows paths")
                else:
                    checks_failed += 1
                    if self.verbose:
                        console.print("    > [FAIL] settings.json does not use Windows paths")
            except Exception:
                checks_failed += 1

        # Check .mcp.json
        mcp_file = self.project_root / ".mcp.json"
        if mcp_file.exists():
            try:
                content = mcp_file.read_text(encoding="utf-8")
                if '"command": "cmd"' in content and '"/c"' in content:
                    checks_passed += 1
                    if self.verbose:
                        console.print("    > [OK] .mcp.json uses Windows cmd wrapper")
                else:
                    checks_failed += 1
                    if self.verbose:
                        console.print("    > [FAIL] .mcp.json does not use Windows cmd wrapper")
            except Exception:
                checks_failed += 1

        if checks_failed > 0:
            self.result.warnings.append(f"{checks_failed} verification checks failed")

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
