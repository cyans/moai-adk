# type: ignore
"""
Statusline data structures and models

TAG-WIN-005: Statusline Solution 구현
Provides data containers for statusline information display
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StatuslineData:
    """Statusline data container for Powerline-style display

    Contains all information needed to render statusline displays
    in various formats (Powerline, Extended, Minimal, Simple).

    Attributes:
        model: AI model name (e.g., "claude-sonnet")
        claude_version: Claude Code version string
        version: MoAI-ADK version string
        memory_usage: Memory usage information
        branch: Git branch name
        git_status: Git repository status
        directory: Current working directory
        output_style: Output style name
        update_available: Whether updates are available
        latest_version: Latest version if update available
        exit_code: Last command exit code
        python_venv: Current Python virtual environment
    """
    model: str
    claude_version: str
    version: str
    memory_usage: str
    branch: str
    git_status: str
    directory: str
    output_style: str
    update_available: bool
    latest_version: Optional[str] = None
    exit_code: Optional[str] = None  # Last command exit code
    python_venv: Optional[str] = None  # Python virtual environment

    def __post_init__(self):
        """Initialize default values for optional fields"""
        # Set default values for required fields
        self.model = self.model or "unknown"
        self.version = self.version or "0.0.0"
        self.branch = self.branch or "unknown"
        self.directory = self.directory or "project"

        # Set default for optional exit code
        if self.exit_code is None:
            self.exit_code = "0"  # Default to success