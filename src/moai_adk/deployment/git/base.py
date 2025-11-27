"""
Base Git operations module providing common functionality and interfaces.
"""
import os
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
from enum import Enum


class GitOperationType(Enum):
    """Types of Git operations."""
    FETCH = "fetch"
    PUSH = "push"
    MERGE = "merge"
    COMMIT = "commit"
    BRANCH = "branch"
    REMOTE = "remote"
    INIT = "init"
    STATUS = "status"
    DIFF = "diff"


class GitOperationError(Exception):
    """Custom exception for Git operation errors."""
    pass


class GitOperationResult:
    """Result wrapper for Git operations."""

    def __init__(self,
                 success: bool,
                 operation_type: GitOperationType,
                 message: str = "",
                 data: Optional[Dict[str, Any]] = None,
                 error: Optional[str] = None,
                 commit_hash: Optional[str] = None):
        self.success = success
        self.operation_type = operation_type
        self.message = message
        self.data = data or {}
        self.error = error
        self.commit_hash = commit_hash
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "operation_type": self.operation_type.value,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "commit_hash": self.commit_hash,
            "timestamp": self.timestamp
        }


class GitCommandExecutor:
    """Low-level Git command executor."""

    def __init__(self, repo_path: Union[str, Path], logger: Optional[logging.Logger] = None):
        self.repo_path = Path(repo_path)
        self.logger = logger or self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create default logger."""
        logger = logging.getLogger('GitCommandExecutor')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def execute_command(self,
                      command: List[str],
                      capture_output: bool = True,
                      text: bool = True,
                      timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute Git command with proper error handling."""
        try:
            self.logger.debug(f"Executing command: {' '.join(command)}")

            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=text,
                timeout=timeout
            )

            response = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command,
                "timestamp": datetime.now().isoformat()
            }

            # Add error key for failures
            if not response["success"]:
                response["error"] = result.stderr or "Unknown error"

            return response

        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timeout: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": command,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Command execution failed: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": command,
                "timestamp": datetime.now().isoformat()
            }


class GitRepositoryValidator:
    """Git repository validation utilities."""

    def __init__(self, executor: GitCommandExecutor, logger: Optional[logging.Logger] = None):
        self.executor = executor
        self.logger = logger or self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create default logger."""
        logger = logging.getLogger('GitRepositoryValidator')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def validate_repository(self) -> GitOperationResult:
        """Validate that the current directory is a Git repository."""
        result = self.executor.execute_command(["git", "status"])

        if result["success"]:
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.STATUS,
                message="Repository is valid",
                data={"is_git_repo": True}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.STATUS,
                message="Not a valid Git repository",
                error=result["error"]
            )

    def validate_remote_config(self, remote_configs: Dict[str, str]) -> GitOperationResult:
        """Validate remote configuration."""
        errors = []

        for remote_name, url in remote_configs.items():
            try:
                # Test URL format
                if not self._validate_url_format(url):
                    errors.append(f"Invalid URL format for {remote_name}: {url}")
                    continue

                # Test connectivity
                result = self.executor.execute_command(
                    ["git", "ls-remote", url],
                    timeout=10
                )

                if not result["success"]:
                    errors.append(f"Connection test failed for {remote_name}: {result['error']}")

            except Exception as e:
                errors.append(f"Validation error for {remote_name}: {str(e)}")

        return GitOperationResult(
            success=len(errors) == 0,
            operation_type=GitOperationType.REMOTE,
            message="Remote configuration validation",
            data={"errors": errors, "is_valid": len(errors) == 0}
        )

    def _validate_url_format(self, url: str) -> bool:
        """Validate Git URL format."""
        return url.startswith(('https://github.com/', 'git@github.com:', 'https://gitlab.com/', 'git@gitlab.com:'))

    def validate_branch_exists(self, branch_name: str) -> GitOperationResult:
        """Validate if branch exists."""
        result = self.executor.execute_command(
            ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"]
        )

        return GitOperationResult(
            success=result["success"],
            operation_type=GitOperationType.BRANCH,
            message=f"Branch '{branch_name}' exists" if result["success"] else f"Branch '{branch_name}' does not exist",
            data={"branch_exists": result["success"]}
        )