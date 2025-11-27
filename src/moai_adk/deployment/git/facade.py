"""
High-level Git operations facade providing clean interface.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime

from .base import GitCommandExecutor, GitRepositoryValidator, GitOperationResult
from .operations import (
    GitBranchOperations, GitRemoteOperations, GitFetchOperations,
    GitPushOperations, GitMergeOperations
)


class GitOperationsFacade:
    """
    High-level facade for Git operations providing a clean interface.

    This class orchestrates the various specialized Git operation classes
    to provide a unified and easy-to-use interface.
    """

    def __init__(self, repo_path: Union[str, Path], logger: Optional[logging.Logger] = None):
        """Initialize Git operations facade."""
        self.repo_path = Path(repo_path)
        self.logger = logger or self._create_logger()

        # Initialize components
        self.executor = GitCommandExecutor(self.repo_path, self.logger)
        self.validator = GitRepositoryValidator(self.executor, self.logger)

        # Initialize specialized operation classes
        self.branches = GitBranchOperations(self.executor, self.logger)
        self.remotes = GitRemoteOperations(self.executor, self.logger)
        self.fetch = GitFetchOperations(self.executor, self.logger)
        self.push = GitPushOperations(self.executor, self.logger)
        self.merge = GitMergeOperations(self.executor, self.logger)

    def _create_logger(self) -> logging.Logger:
        """Create default logger."""
        logger = logging.getLogger('GitOperationsFacade')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def validate_environment(self) -> GitOperationResult:
        """Validate Git environment and repository."""
        # Validate repository
        repo_result = self.validator.validate_repository()
        if not repo_result.success:
            return repo_result

        # Validate Git installation
        git_result = self.executor.execute_command(["git", "--version"])
        if not git_result.get("success", False):
            return GitOperationResult(
                success=False,
                operation_type=None,
                message="Git not installed or not accessible",
                error=git_result.get("error", git_result.get("stderr", ""))
            )

        return GitOperationResult(
            success=True,
            operation_type=None,
            message="Git environment is valid",
            data={"repo_path": str(self.repo_path), "git_version": git_result["stdout"].strip()}
        )

    def setup_remotes(self, remote_configs: Dict[str, str]) -> GitOperationResult:
        """Set up Git remotes with validation."""
        # Validate remote configuration first
        validation_result = self.validator.validate_remote_config(remote_configs)
        if not validation_result.success:
            return validation_result

        # Add remotes
        results = []
        for remote_name, url in remote_configs.items():
            result = self.remotes.add_remote(remote_name, url)
            results.append(result)

        # Aggregate results
        success_count = sum(1 for r in results if r.success)

        return GitOperationResult(
            success=success_count == len(remote_configs),
            operation_type=None,
            message=f"Setup {success_count}/{len(remote_configs)} remotes",
            data={
                "total_remotes": len(remote_configs),
                "successful": success_count,
                "results": [r.to_dict() for r in results]
            }
        )

    def sync_with_upstream(self,
                         remote_name: str,
                         branch: str = "main",
                         preserve_history: bool = True) -> GitOperationResult:
        """
        Synchronize with upstream repository.

        Args:
            remote_name: Name of the upstream remote
            branch: Branch to sync (default: main)
            preserve_history: Whether to preserve commit history

        Returns:
            Operation result with sync details
        """
        try:
            flow_results = []

            # 1. Validate upstream connection
            url_result = self.remotes.get_remote_url(remote_name)
            flow_results.append(("validate_upstream", url_result))
            if not url_result.success:
                return GitOperationResult(
                    success=False,
                    operation_type=None,
                    message="Upstream connection validation failed",
                    error=url_result.error
                )

            # 2. Fetch upstream changes
            fetch_result = self.fetch.fetch_remote(remote_name, branch)
            flow_results.append(("fetch_upstream", fetch_result))
            if not fetch_result.success:
                return GitOperationResult(
                    success=False,
                    operation_type=None,
                    message="Failed to fetch upstream changes",
                    error=fetch_result.error
                )

            # 3. Merge changes
            merge_result = self.merge.merge_branch(
                f"{remote_name}/{branch}",
                preserve_history=preserve_history
            )
            flow_results.append(("merge_changes", merge_result))
            if not merge_result.success:
                return GitOperationResult(
                    success=False,
                    operation_type=None,
                    message="Failed to merge upstream changes",
                    error=merge_result.error
                )

            # 4. Push to origin (if different from upstream)
            origin_result = self.remotes.get_remote_url("origin")
            if origin_result.success and origin_result.data["url"] != url_result.data["url"]:
                push_result = self.push.push_branch("origin", branch)
                flow_results.append(("push_to_origin", push_result))

            return GitOperationResult(
                success=True,
                operation_type=None,
                message="Successfully synchronized with upstream",
                data={
                    "upstream_remote": remote_name,
                    "branch": branch,
                    "preserve_history": preserve_history,
                    "flow_results": [step for step, result in flow_results]
                }
            )

        except Exception as e:
            self.logger.error(f"Sync operation failed: {str(e)}")
            return GitOperationResult(
                success=False,
                operation_type=None,
                message="Synchronization failed",
                error=str(e)
            )

    def get_branch_status(self, branch: str = "main") -> GitOperationResult:
        """Get detailed status information for a branch."""
        try:
            # Get branch info
            branch_result = self.branches.switch_branch(branch)
            if not branch_result.success:
                return branch_result

            # Get remote status for each remote
            remotes_result = self.remotes.list_remotes()
            if not remotes_result.success:
                return GitOperationResult(
                    success=False,
                    operation_type=None,
                    message="Failed to get remotes for status check",
                    error=remotes_result.error
                )

            remote_status = {}
            for remote_name in remotes_result.data["remotes"].keys():
                try:
                    # Get latest commit
                    commit_result = self.executor.execute_command(
                        ["git", "ls-remote", remote_name, branch],
                        timeout=10
                    )

                    if commit_result.success:
                        commit_hash = commit_result.stdout.strip().split('\t')[0]
                        remote_status[remote_name] = {
                            "latest_commit": commit_hash,
                            "reachable": True
                        }
                    else:
                        remote_status[remote_name] = {
                            "reachable": False,
                            "error": commit_result.get("error", "Unknown error")
                        }
                except Exception as e:
                    remote_status[remote_name] = {
                        "reachable": False,
                        "error": str(e)
                    }

            # Check for local changes
            status_result = self.executor.execute_command(["git", "status", "--porcelain"])
            local_changes = status_result.stdout.strip().split('\n') if status_result.success else []

            return GitOperationResult(
                success=True,
                operation_type=None,
                message=f"Status retrieved for branch {branch}",
                data={
                    "branch": branch,
                    "local_changes": len([c for c in local_changes if c.strip()]),
                    "remote_status": remote_status,
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to get branch status: {str(e)}")
            return GitOperationResult(
                success=False,
                operation_type=None,
                message="Failed to get branch status",
                error=str(e)
            )

    def create_and_push_branch(self,
                              branch_name: str,
                              source_branch: Optional[str] = None,
                              remote_name: str = "origin") -> GitOperationResult:
        """Create a new branch and push it to remote."""
        try:
            # Create branch
            create_result = self.branches.create_branch(branch_name, source_branch)
            if not create_result.success:
                return create_result

            # Push to remote
            push_result = self.push.push_branch(remote_name, branch_name)
            if not push_result.success:
                # Try to clean up local branch if push failed
                self.branches.delete_branch(branch_name)
                return push_result

            return GitOperationResult(
                success=True,
                operation_type=None,
                message=f"Successfully created and pushed branch {branch_name}",
                data={
                    "branch": branch_name,
                    "source_branch": source_branch,
                    "remote": remote_name
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to create and push branch: {str(e)}")
            return GitOperationResult(
                success=False,
                operation_type=None,
                message="Failed to create and push branch",
                error=str(e)
            )

    def initialize_repository(self) -> GitOperationResult:
        """Initialize Git repository."""
        try:
            # Check if already initialized
            if (self.repo_path / ".git").exists():
                return GitOperationResult(
                    success=True,
                    operation_type=None,
                    message="Repository already initialized",
                    data={"already_initialized": True}
                )

            # Initialize
            result = self.executor.execute_command(["git", "init"])

            if result["success"]:
                return GitOperationResult(
                    success=True,
                    operation_type=None,
                    message="Repository initialized successfully"
                )
            else:
                return GitOperationResult(
                    success=False,
                    operation_type=None,
                    message="Failed to initialize repository",
                    error=result["stderr"]
                )

        except Exception as e:
            self.logger.error(f"Failed to initialize repository: {str(e)}")
            return GitOperationResult(
                success=False,
                operation_type=None,
                message="Failed to initialize repository",
                error=str(e)
            )

    def create_commit(self, message: str, files: Optional[List[str]] = None) -> GitOperationResult:
        """Create Git commit."""
        try:
            # Add files if specified
            if files:
                for file_path in files:
                    add_result = self.executor.execute_command(["git", "add", file_path])
                    if not add_result.get("success", False):
                        return GitOperationResult(
                            success=False,
                            operation_type=None,
                            message=f"Failed to add file {file_path}",
                            error=add_result.get("error", add_result.get("stderr", ""))
                        )

            # Commit
            commit_result = self.executor.execute_command(
                ["git", "commit", "-m", message]
            )

            if commit_result.get("success", False):
                # Get commit hash
                hash_result = self.executor.execute_command(["git", "rev-parse", "HEAD"])

                return GitOperationResult(
                    success=True,
                    operation_type=None,
                    message="Commit created successfully",
                    data={
                        "commit_message": message,
                        "files": files,
                        "commit_hash": hash_result.get("stdout", "").strip() if hash_result.get("success", False) else None
                    }
                )
            else:
                return GitOperationResult(
                    success=False,
                    operation_type=None,
                    message="Failed to create commit",
                    error=commit_result.get("error", commit_result.get("stderr", ""))
                )

        except Exception as e:
            self.logger.error(f"Failed to create commit: {str(e)}")
            return GitOperationResult(
                success=False,
                operation_type=None,
                message="Failed to create commit",
                error=str(e)
            )

    def get_repository_info(self) -> GitOperationResult:
        """Get comprehensive repository information."""
        try:
            # Get basic info
            status_result = self.executor.execute_command(["git", "status", "--porcelain"])
            branch_result = self.executor.execute_command(["git", "branch", "--show-current"])
            remote_result = self.remotes.list_remotes()

            # Get latest commit
            log_result = self.executor.execute_command(["git", "log", "-1", "--format=%H|%an|%ae|%ad|%s", "--date=iso"])

            # Parse commit info
            commit_info = None
            if log_result.get("success", False):
                parts = log_result.get("stdout", "").strip().split('|', 4)
                if len(parts) == 5:
                    commit_info = {
                        "hash": parts[0],
                        "author_name": parts[1],
                        "author_email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    }

            return GitOperationResult(
                success=True,
                operation_type=None,
                message="Repository info retrieved",
                data={
                    "current_branch": branch_result.stdout.strip() if branch_result.success else "unknown",
                    "has_local_changes": bool(status_result.stdout.strip()),
                    "remotes_count": len(remote_result.data["remotes"]) if remote_result.success else 0,
                    "latest_commit": commit_info,
                    "repo_path": str(self.repo_path)
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to get repository info: {str(e)}")
            return GitOperationResult(
                success=False,
                operation_type=None,
                message="Failed to get repository info",
                error=str(e)
            )