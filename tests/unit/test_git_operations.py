"""
Unit tests for the new modular Git operations library.
"""
import pytest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from moai_adk.deployment.git import (
    GitOperationsFacade, GitOperationResult, GitOperationType,
    GitBranchOperations, GitRemoteOperations, GitFetchOperations,
    GitPushOperations, GitMergeOperations, GitCommandExecutor,
    GitRepositoryValidator
)


class TestGitCommandExecutor:
    """Test the Git command executor."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.executor = GitCommandExecutor(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")

        result = self.executor.execute_command(["git", "status"])

        assert result["success"] is True
        assert result["returncode"] == 0
        assert result["stdout"] == "success"
        assert result["stderr"] == ""

    @patch('subprocess.run')
    def test_execute_command_failure(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")

        result = self.executor.execute_command(["git", "status"])

        assert result["success"] is False
        assert result["returncode"] == 1
        assert result["error"] == "error"

    @patch('subprocess.run')
    def test_execute_command_timeout(self, mock_run):
        """Test command timeout."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("git", 10)

        result = self.executor.execute_command(["git", "status"], timeout=10)

        assert result["success"] is False
        assert "timeout" in result["error"]


class TestGitRepositoryValidator:
    """Test the Git repository validator."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.executor = GitCommandExecutor(self.temp_dir)
        self.validator = GitRepositoryValidator(self.executor)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_validate_url_format_valid(self):
        """Test valid URL format validation."""
        assert self.validator._validate_url_format("https://github.com/user/repo") is True
        assert self.validator._validate_url_format("git@github.com:user/repo") is True
        assert self.validator._validate_url_format("https://gitlab.com/user/repo") is True

    def test_validate_url_format_invalid(self):
        """Test invalid URL format validation."""
        assert self.validator._validate_url_format("invalid-url") is False
        assert self.validator._validate_url_format("ftp://github.com/user/repo") is False


class TestGitBranchOperations:
    """Test Git branch operations."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.executor = GitCommandExecutor(self.temp_dir)
        self.branch_ops = GitBranchOperations(self.executor)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_switch_branch_success(self, mock_run):
        """Test successful branch switch."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = self.branch_ops.switch_branch("main")

        assert result.success is True
        assert result.operation_type == GitOperationType.BRANCH
        assert "main" in result.message

    @patch('subprocess.run')
    def test_switch_branch_failure(self, mock_run):
        """Test failed branch switch."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Branch not found")

        result = self.branch_ops.switch_branch("nonexistent")

        assert result.success is False
        assert result.operation_type == GitOperationType.BRANCH
        assert "nonexistent" in result.message
        assert result.error == "Branch not found"


class TestGitRemoteOperations:
    """Test Git remote operations."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.executor = GitCommandExecutor(self.temp_dir)
        self.remote_ops = GitRemoteOperations(self.executor)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_add_remote_success(self, mock_run):
        """Test successful remote addition."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = self.remote_ops.add_remote("origin", "https://github.com/user/repo.git")

        assert result.success is True
        assert result.operation_type == GitOperationType.REMOTE
        assert result.data["remote"] == "origin"

    @patch('subprocess.run')
    def test_update_existing_remote(self, mock_run):
        """Test updating existing remote."""
        # First call fails (remote exists), second call succeeds (update)
        mock_run.side_effect = [
            Mock(returncode=1, stderr="remote already exists"),
            Mock(returncode=0, stdout="", stderr="")
        ]

        result = self.remote_ops.add_remote("origin", "https://github.com/user/new-repo.git")

        assert result.success is True
        assert result.operation_type == GitOperationType.REMOTE
        assert result.data["updated"] is True


class TestGitOperationsFacade:
    """Test the Git operations facade."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.facade = GitOperationsFacade(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    @patch('moai_adk.deployment.git.base.GitRepositoryValidator')
    @patch('moai_adk.deployment.git.base.GitCommandExecutor')
    def test_validate_environment_success(self, mock_executor_class, mock_validator_class):
        """Test successful environment validation."""
        # Mock the validator to return a successful result
        mock_validator = Mock()
        mock_validator.validate_repository.return_value = GitOperationResult(
            success=True,
            operation_type=None,
            message="Repository is valid"
        )
        mock_validator_class.return_value = mock_validator

        # Mock the executor to return successful results
        mock_executor = Mock()
        mock_executor.execute_command.return_value = {
            "success": True,
            "stdout": "git version 2.30.0",
            "stderr": ""
        }
        mock_executor_class.return_value = mock_executor

        # Create new facade with mocked components
        self.facade.validator = mock_validator
        self.facade.executor = mock_executor

        result = self.facade.validate_environment()

        assert result.success is True
        assert result.message == "Git environment is valid"

    @patch('moai_adk.deployment.git.base.GitRepositoryValidator')
    def test_validate_environment_failure(self, mock_validator_class):
        """Test failed environment validation."""
        # Mock the validator to return a failed result
        mock_validator = Mock()
        mock_validator.validate_repository.return_value = GitOperationResult(
            success=False,
            operation_type=None,
            message="Not a valid Git repository",
            error="Not a git repository"
        )
        mock_validator_class.return_value = mock_validator

        # Create new facade with mocked validator
        self.facade.validator = mock_validator

        result = self.facade.validate_environment()

        assert result.success is False
        assert result.message == "Not a valid Git repository"

    @patch('moai_adk.deployment.git.base.GitCommandExecutor')
    def test_create_commit_success(self, mock_executor_class):
        """Test successful commit creation."""
        # Mock the executor to return successful results
        mock_executor = Mock()
        mock_executor.execute_command.side_effect = [
            {"success": True, "stdout": "", "stderr": ""},  # git add
            {"success": True, "stdout": "", "stderr": ""},  # git commit
            {"success": True, "stdout": "abc123", "stderr": ""}  # git rev-parse
        ]
        mock_executor_class.return_value = mock_executor

        # Create new facade with mocked executor
        self.facade.executor = mock_executor

        result = self.facade.create_commit("Test commit", ["test.txt"])

        assert result.success is True
        assert result.data["commit_message"] == "Test commit"
        assert result.data["commit_hash"] == "abc123"


class TestGitOperationResult:
    """Test Git operation result."""

    def test_result_success(self):
        """Test successful result creation."""
        result = GitOperationResult(
            success=True,
            operation_type=GitOperationType.FETCH,
            message="Success",
            data={"test": "value"}
        )

        assert result.success is True
        assert result.operation_type == GitOperationType.FETCH
        assert result.message == "Success"
        assert result.data["test"] == "value"

    def test_result_failure(self):
        """Test failed result creation."""
        result = GitOperationResult(
            success=False,
            operation_type=GitOperationType.MERGE,
            error="Something went wrong"
        )

        assert result.success is False
        assert result.operation_type == GitOperationType.MERGE
        assert result.error == "Something went wrong"

    def test_result_to_dict(self):
        """Test result to dictionary conversion."""
        result = GitOperationResult(
            success=True,
            operation_type=GitOperationType.FETCH,
            message="Success",
            commit_hash="abc123"
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["operation_type"] == "fetch"
        assert result_dict["commit_hash"] == "abc123"
        assert "timestamp" in result_dict


if __name__ == "__main__":
    pytest.main([__file__])