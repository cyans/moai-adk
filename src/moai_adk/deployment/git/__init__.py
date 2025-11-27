"""
Modular Git operations library for Windows deployment system.

This package provides a clean, maintainable architecture for Git operations
with separated concerns and proper error handling.
"""

from .base import (
    GitOperationType,
    GitOperationError,
    GitOperationResult,
    GitCommandExecutor,
    GitRepositoryValidator
)

from .operations import (
    GitBranchOperations,
    GitRemoteOperations,
    GitFetchOperations,
    GitPushOperations,
    GitMergeOperations
)

from .facade import GitOperationsFacade

__version__ = "1.0.0"
__author__ = "MoAI ADK Team"

# Main facade class for easy usage
GitOperations = GitOperationsFacade

# Convenience functions for common operations
def create_git_operations(repo_path: str, logger=None) -> GitOperationsFacade:
    """Create Git operations facade instance."""
    return GitOperationsFacade(repo_path, logger)

def validate_git_repository(repo_path: str) -> GitOperationResult:
    """Quick repository validation."""
    facade = GitOperationsFacade(repo_path)
    return facade.validate_environment()

__all__ = [
    # Base classes
    'GitOperationType',
    'GitOperationError',
    'GitOperationResult',
    'GitCommandExecutor',
    'GitRepositoryValidator',

    # Specialized operations
    'GitBranchOperations',
    'GitRemoteOperations',
    'GitFetchOperations',
    'GitPushOperations',
    'GitMergeOperations',

    # Facade
    'GitOperationsFacade',
    'GitOperations',

    # Convenience functions
    'create_git_operations',
    'validate_git_repository'
]