"""
GitHub fork synchronization management system.

This module uses the modular Git operations library to provide
high-level fork synchronization functionality.
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json

from .git import GitOperationsFacade, GitOperationResult


class GitForkSyncManager:
    """Manages GitHub fork synchronization with upstream repository."""

    def __init__(self, repo_path: str, config: Dict[str, Any]):
        """Initialize Git fork sync manager."""
        self.repo_path = Path(repo_path)
        self.config = config
        self.git_ops = GitOperationsFacade(repo_path)
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the sync manager."""
        logger = logging.getLogger('GitForkSyncManager')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def sync_with_upstream(self, preserve_history: bool = True) -> Dict[str, Any]:
        """
        Synchronize fork with upstream repository.

        Args:
            preserve_history: Whether to preserve commit history during merge

        Returns:
            Dictionary with sync results
        """
        try:
            self.logger.info("Starting upstream synchronization...")

            # Track execution flow
            flow_executed = []

            # 1. Validate environment
            flow_executed.append("validate_environment")
            env_result = self.git_ops.validate_environment()
            if not env_result.success:
                raise Exception(f"Environment validation failed: {env_result.error}")

            # 2. Validate upstream connection
            flow_executed.append("validate_upstream")
            upstream_url_result = self.git_ops.remotes.get_remote_url(
                self.config["git"]["remote_name"]
            )
            if not upstream_url_result.success:
                raise Exception(f"Upstream connection validation failed: {upstream_url_result.error}")

            # 3. Validate fork status
            flow_executed.append("validate_fork")
            fork_status = self.validate_fork_status()
            if not fork_status["is_valid"]:
                self.logger.warning(f"Fork issues detected: {fork_status}")

            # 4. Fetch upstream changes
            flow_executed.append("fetch_upstream")
            fetch_result = self.git_ops.fetch.fetch_remote(
                self.config["git"]["remote_name"],
                self.config["git"]["branch"]
            )
            fetch_result_dict = fetch_result.to_dict()

            # 5. Merge changes
            flow_executed.append("merge_changes")
            merge_result = self.git_ops.merge.merge_branch(
                f"{self.config['git']['remote_name']}/{self.config['git']['branch']}",
                preserve_history=preserve_history
            )
            merge_result_dict = merge_result.to_dict()

            # 6. Push to fork
            flow_executed.append("push_to_fork")
            push_result = self.git_ops.push.push_remote(
                self.config["git"]["fork_remote_name"],
                self.config["git"]["branch"]
            )
            push_result_dict = push_result.to_dict()

            # 7. Validate sync
            flow_executed.append("validate_sync")
            sync_validation = self.validate_fork_status()

            result = {
                "status": "success",
                "message": "Successfully synchronized with upstream",
                "flow_executed": flow_executed,
                "timestamp": datetime.now().isoformat(),
                "results": {
                    "environment_validation": env_result.to_dict(),
                    "upstream_valid": upstream_url_result.success,
                    "fork_status": fork_status,
                    "fetch_result": fetch_result_dict,
                    "merge_result": merge_result_dict,
                    "push_result": push_result_dict,
                    "sync_validation": sync_validation
                }
            }

            self.logger.info(f"Sync completed successfully: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Sync failed: {str(e)}")
            return {
                "status": "failed",
                "message": f"Synchronization failed: {str(e)}",
                "flow_executed": flow_executed,
                "timestamp": datetime.now().isoformat()
            }

    def validate_fork_status(self) -> Dict[str, Any]:
        """Validate current fork status against upstream."""
        try:
            # Get status from both remotes
            upstream_result = self.git_ops.remotes.get_remote_url(self.config["git"]["remote_name"])
            origin_result = self.git_ops.remotes.get_remote_url(self.config["git"]["fork_remote_name"])

            if not upstream_result.success or not origin_result.success:
                return {
                    "is_valid": False,
                    "error": "Failed to get remote URLs",
                    "timestamp": datetime.now().isoformat()
                }

            # Get branch status
            branch_status = self.git_ops.get_branch_status(self.config["git"]["branch"])
            if not branch_status.success:
                return {
                    "is_valid": False,
                    "error": branch_status.error,
                    "timestamp": datetime.now().isoformat()
                }

            # Calculate sync status based on available data
            remote_status = branch_status.data.get("remote_status", {})
            upstream_status = remote_status.get(self.config["git"]["remote_name"], {})
            origin_status = remote_status.get(self.config["git"]["fork_remote_name"], {})

            upstream_commit = upstream_status.get("latest_commit")
            origin_commit = origin_status.get("latest_commit")

            is_synced = upstream_commit == origin_commit
            ahead_by = 0
            behind_by = 0

            if upstream_commit and origin_commit:
                # Calculate commit differences using git command
                executor = self.git_ops.executor
                try:
                    # Ahead: commits in origin that are not in upstream
                    ahead_result = executor.execute_command([
                        "git", "rev-list", "--count", f"{upstream_commit}..{origin_commit}"
                    ])
                    if ahead_result.success:
                        ahead_by = int(ahead_result.stdout.strip()) if ahead_result.stdout.strip() else 0

                    # Behind: commits in upstream that are not in origin
                    behind_result = executor.execute_command([
                        "git", "rev-list", "--count", f"{origin_commit}..{upstream_commit}"
                    ])
                    if behind_result.success:
                        behind_by = int(behind_result.stdout.strip()) if behind_result.stdout.strip() else 0
                except Exception:
                    pass  # Fall back to 0 if calculation fails

            return {
                "is_valid": True,
                "is_synced": is_synced,
                "ahead_by": ahead_by,
                "behind_by": behind_by,
                "upstream_status": {
                    "remote": self.config["git"]["remote_name"],
                    "url": upstream_result.data.get("url") if upstream_result.success else None,
                    "latest_commit": upstream_commit
                },
                "origin_status": {
                    "remote": self.config["git"]["fork_remote_name"],
                    "url": origin_result.data.get("url") if origin_result.success else None,
                    "latest_commit": origin_commit
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to validate fork status: {str(e)}")
            return {
                "is_valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def synchronize_branches(self, branches: List[str]) -> Dict[str, Any]:
        """Synchronize multiple branches with upstream."""
        synced_branches = []
        failed_branches = []

        for branch in branches:
            try:
                # Switch to branch
                switch_result = self.git_ops.branches.switch_branch(branch)
                if not switch_result.success:
                    raise Exception(f"Failed to switch to branch: {switch_result.error}")

                # Sync with upstream
                sync_result = self.sync_with_upstream()

                if sync_result["status"] == "success":
                    synced_branches.append({
                        "branch": branch,
                        "result": sync_result
                    })
                else:
                    failed_branches.append({
                        "branch": branch,
                        "error": sync_result["message"]
                    })

            except Exception as e:
                failed_branches.append({
                    "branch": branch,
                    "error": str(e)
                })

        return {
            "success": len(failed_branches) == 0,
            "synced_branches": synced_branches,
            "failed_branches": failed_branches,
            "total_branches": len(branches),
            "timestamp": datetime.now().isoformat()
        }

    def validate_auto_sync_config(self) -> bool:
        """Validate auto-sync configuration."""
        try:
            required_keys = ["auto_sync", "sync_on_start", "sync_interval"]

            for key in required_keys:
                if key not in self.config["deployment"]:
                    self.logger.error(f"Missing required config key: {key}")
                    return False

            # Validate sync interval
            sync_interval = self.config["deployment"]["sync_interval"]
            if not isinstance(sync_interval, int) or sync_interval <= 0:
                self.logger.error("Invalid sync interval")
                return False

            # Validate max retries if present
            if "max_retries" in self.config["deployment"]:
                max_retries = self.config["deployment"]["max_retries"]
                if not isinstance(max_retries, int) or max_retries < 0:
                    self.logger.error("Invalid max retries")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Config validation failed: {str(e)}")
            return False

    def handle_sync_error(self, error_type: str) -> Dict[str, Any]:
        """Handle synchronization errors based on type."""
        error_responses = {
            "network_error": {
                "error": "Network connectivity issue detected",
                "resolution": "Check internet connection and verify remote URLs",
                "retry_suggested": True
            },
            "auth_error": {
                "error": "Authentication failed",
                "resolution": "Verify GitHub credentials and token permissions",
                "retry_suggested": False
            },
            "merge_conflict": {
                "error": "Merge conflict detected during sync",
                "resolution": "Manually resolve conflicts and commit changes",
                "retry_suggested": True
            },
            "remote_not_found": {
                "error": "Remote repository not found",
                "resolution": "Verify upstream repository URL and fork status",
                "retry_suggested": False
            }
        }

        return error_responses.get(error_type, {
            "error": "Unknown error occurred",
            "resolution": "Check logs for more details",
            "retry_suggested": False
        })

    def setup_fork_remotes(self, upstream_url: str, fork_url: str) -> Dict[str, Any]:
        """Set up fork remotes configuration."""
        try:
            remote_configs = {
                self.config["git"]["remote_name"]: upstream_url,
                self.config["git"]["fork_remote_name"]: fork_url
            }

            result = self.git_ops.setup_remotes(remote_configs)

            return {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to setup fork remotes: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }