"""
Core Git operations with separated responsibilities.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime

from .base import (
    GitCommandExecutor, GitRepositoryValidator, GitOperationResult,
    GitOperationType, GitOperationError
)


class GitBranchOperations:
    """Git branch-specific operations."""

    def __init__(self, executor: GitCommandExecutor, logger: Optional[logging.Logger] = None):
        self.executor = executor
        self.logger = logger or self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create default logger."""
        logger = logging.getLogger('GitBranchOperations')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def switch_branch(self, branch_name: str) -> GitOperationResult:
        """Switch to specified branch."""
        result = self.executor.execute_command(["git", "checkout", branch_name])

        if result["success"]:
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.BRANCH,
                message=f"Successfully switched to {branch_name}",
                data={"branch": branch_name}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.BRANCH,
                message=f"Failed to switch to {branch_name}",
                error=result["stderr"]
            )

    def create_branch(self, branch_name: str, from_branch: Optional[str] = None) -> GitOperationResult:
        """Create new branch."""
        command = ["git", "checkout", "-b", branch_name]
        if from_branch:
            command.extend(["-c", f"refs/heads/{from_branch}"])

        result = self.executor.execute_command(command)

        if result["success"]:
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.BRANCH,
                message=f"Successfully created branch {branch_name}",
                data={"branch": branch_name, "from_branch": from_branch}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.BRANCH,
                message=f"Failed to create branch {branch_name}",
                error=result["stderr"]
            )

    def create_branches(self, branches: List[str]) -> GitOperationResult:
        """Create multiple branches."""
        created_branches = []
        failed_branches = []

        for branch in branches:
            branch_result = self.create_branch(branch)
            if branch_result.success:
                created_branches.append(branch)
            else:
                failed_branches.append({
                    "branch": branch,
                    "error": branch_result.error
                })

        return GitOperationResult(
            success=len(failed_branches) == 0,
            operation_type=GitOperationType.BRANCH,
            message=f"Created {len(created_branches)}/{len(branches)} branches",
            data={
                "created_branches": created_branches,
                "failed_branches": failed_branches,
                "total_branches": len(branches)
            }
        )

    def list_branches(self) -> GitOperationResult:
        """List all branches."""
        result = self.executor.execute_command(["git", "branch", "-a"])

        if result["success"]:
            branches = [line.strip().replace("* ", "") for line in result.stdout.split('\n') if line.strip()]
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.BRANCH,
                message="Successfully listed branches",
                data={"branches": branches, "count": len(branches)}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.BRANCH,
                message="Failed to list branches",
                error=result["stderr"]
            )

    def delete_branch(self, branch_name: str, force: bool = False) -> GitOperationResult:
        """Delete branch."""
        command = ["git", "branch", "-d" if not force else "-D", branch_name]
        result = self.executor.execute_command(command)

        return GitOperationResult(
            success=result["success"],
            operation_type=GitOperationType.BRANCH,
            message=f"Successfully deleted branch {branch_name}" if result["success"] else f"Failed to delete branch {branch_name}",
            data={"branch": branch_name, "force": force},
            error=result["stderr"] if not result["success"] else None
        )


class GitRemoteOperations:
    """Git remote-specific operations."""

    def __init__(self, executor: GitCommandExecutor, logger: Optional[logging.Logger] = None):
        self.executor = executor
        self.logger = logger or self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create default logger."""
        logger = logging.getLogger('GitRemoteOperations')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def add_remote(self, remote_name: str, url: str) -> GitOperationResult:
        """Add new remote."""
        result = self.executor.execute_command(
            ["git", "remote", "add", remote_name, url]
        )

        if result["success"]:
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.REMOTE,
                message=f"Successfully added remote {remote_name}",
                data={"remote": remote_name, "url": url}
            )
        else:
            # Check if remote already exists and try to update URL
            return self._update_remote_url(remote_name, url)

    def _update_remote_url(self, remote_name: str, url: str) -> GitOperationResult:
        """Update existing remote URL."""
        result = self.executor.execute_command(
            ["git", "remote", "set-url", remote_name, url]
        )

        if result["success"]:
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.REMOTE,
                message=f"Successfully updated remote {remote_name}",
                data={"remote": remote_name, "url": url, "updated": True}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.REMOTE,
                message=f"Failed to add/update remote {remote_name}",
                error=result["stderr"]
            )

    def remove_remote(self, remote_name: str) -> GitOperationResult:
        """Remove remote."""
        result = self.executor.execute_command(
            ["git", "remote", "remove", remote_name]
        )

        return GitOperationResult(
            success=result["success"],
            operation_type=GitOperationType.REMOTE,
            message=f"Successfully removed remote {remote_name}" if result["success"] else f"Failed to remove remote {remote_name}",
            data={"remote": remote_name},
            error=result["stderr"] if not result["success"] else None
        )

    def list_remotes(self) -> GitOperationResult:
        """List all remotes."""
        result = self.executor.execute_command(["git", "remote", "-v"])

        if result["success"]:
            remotes = {}
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        remote_name = parts[0]
                        remote_url = parts[1].split(' ')[0]  # Remove fetch/push info
                        if remote_name not in remotes:
                            remotes[remote_name] = []
                        remotes[remote_name].append(remote_url)

            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.REMOTE,
                message="Successfully listed remotes",
                data={"remotes": remotes, "count": len(remotes)}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.REMOTE,
                message="Failed to list remotes",
                error=result["stderr"]
            )

    def get_remote_url(self, remote_name: str) -> GitOperationResult:
        """Get remote URL."""
        result = self.executor.execute_command(
            ["git", "remote", "get-url", remote_name]
        )

        if result["success"]:
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.REMOTE,
                message=f"Successfully retrieved URL for {remote_name}",
                data={"remote": remote_name, "url": result.stdout.strip()}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.REMOTE,
                message=f"Failed to get URL for {remote_name}",
                error=result["stderr"]
            )


class GitFetchOperations:
    """Git fetch-specific operations."""

    def __init__(self, executor: GitCommandExecutor, logger: Optional[logging.Logger] = None):
        self.executor = executor
        self.logger = logger or self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create default logger."""
        logger = logging.getLogger('GitFetchOperations')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def fetch_remote(self, remote_name: str, branch: Optional[str] = None) -> GitOperationResult:
        """Fetch from remote."""
        command = ["git", "fetch", remote_name]
        if branch:
            command.append(branch)

        result = self.executor.execute_command(command)

        if result["success"]:
            message = f"Successfully fetched from {remote_name}"
            if branch:
                message += f" (branch: {branch})"

            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.FETCH,
                message=message,
                data={"remote": remote_name, "branch": branch}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.FETCH,
                message=f"Failed to fetch from {remote_name}",
                error=result["stderr"]
            )

    def fetch_all(self) -> GitOperationResult:
        """Fetch from all remotes."""
        result = self.executor.execute_command(["git", "fetch", "--all"])

        if result["success"]:
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.FETCH,
                message="Successfully fetched from all remotes"
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.FETCH,
                message="Failed to fetch from all remotes",
                error=result["stderr"]
            )


class GitPushOperations:
    """Git push-specific operations."""

    def __init__(self, executor: GitCommandExecutor, logger: Optional[logging.Logger] = None):
        self.executor = executor
        self.logger = logger or self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create default logger."""
        logger = logging.getLogger('GitPushOperations')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def push_branch(self, remote_name: str, branch: str, force: bool = False) -> GitOperationResult:
        """Push branch to remote."""
        command = ["git", "push", remote_name, branch]
        if force:
            command.append("--force")

        result = self.executor.execute_command(command)

        if result["success"]:
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.PUSH,
                message=f"Successfully pushed {branch} to {remote_name}",
                data={"remote": remote_name, "branch": branch, "force": force}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.PUSH,
                message=f"Failed to push {branch} to {remote_name}",
                error=result["stderr"]
            )


class GitMergeOperations:
    """Git merge-specific operations."""

    def __init__(self, executor: GitCommandExecutor, logger: Optional[logging.Logger] = None):
        self.executor = executor
        self.logger = logger or self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create default logger."""
        logger = logging.getLogger('GitMergeOperations')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def detect_merge_conflicts(self) -> GitOperationResult:
        """Detect merge conflicts in current branch."""
        result = self.executor.execute_command(
            ["git", "diff", "--name-only", "--diff-filter=U"]
        )

        if result["success"]:
            conflict_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.DIFF,
                message=f"Detected {len(conflict_files)} merge conflicts",
                data={"conflict_files": conflict_files, "count": len(conflict_files)}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.DIFF,
                message="Failed to detect merge conflicts",
                error=result["stderr"]
            )

    def merge_branch(self, source_branch: str, preserve_history: bool = True, no_ff: bool = False) -> GitOperationResult:
        """Merge source branch into current branch."""
        command = ["git", "merge", source_branch]

        if preserve_history or no_ff:
            command.insert(1, "--no-ff")

        # Add conflict detection
        conflict_result = self.detect_merge_conflicts()
        if conflict_result.success and conflict_result.data["count"] > 0:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.MERGE,
                message=f"Merge conflicts detected in {conflict_result.data['count']} files",
                error="Merge conflicts detected",
                data={"conflict_files": conflict_result.data["conflict_files"]}
            )

        result = self.executor.execute_command(command)

        if result["success"]:
            return GitOperationResult(
                success=True,
                operation_type=GitOperationType.MERGE,
                message=f"Successfully merged {source_branch}",
                data={"source_branch": source_branch, "preserve_history": preserve_history or no_ff}
            )
        else:
            return GitOperationResult(
                success=False,
                operation_type=GitOperationType.MERGE,
                message=f"Failed to merge {source_branch}",
                error=result["stderr"]
            )