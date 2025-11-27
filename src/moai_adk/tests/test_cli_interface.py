"""
Test suite for CLI interface and user interaction.
TAG-CLI-002: CLI interface and user interaction
"""

import pytest
import click
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import tempfile
import os
from pathlib import Path

# Import the CLI modules to be tested (will be implemented in GREEN phase)
from moai_adk.cli.main import main, cli
from moai_adk.cli.commands import (
    deploy_command,
    config_command,
    status_command,
    list_command,
    validate_command,
    rollback_command
)
from moai_adk.cli.interaction import (
    UserConfirmation,
    ProgressDisplay,
    InteractiveSession,
    get_user_input
)
from moai_adk.cli.formatters import (
    format_deployment_status,
    format_step_progress,
    format_error_message,
    format_success_message
)
from moai_adk.cli.validators import (
    validate_config_file,
    validate_deployment_name,
    validate_step_command
)
from moai_adk.cli.exceptions import (
    CLIError,
    ValidationError,
    ConfigurationError,
    UserAbortError
)


class TestUserConfirmation:
    """Test cases for UserConfirmation class"""

    def test_confirmation_initialization(self):
        """Test UserConfirmation initialization"""
        confirmation = UserConfirmation(
            message="진행할까요?",
            options={
                "진행": "proceed",
                "건너뛰기": "skip",
                "중단": "abort"
            }
        )

        assert confirmation.message == "진행할까요?"
        assert "진행" in confirmation.options
        assert "건너뛰기" in confirmation.options
        assert "중단" in confirmation.options
        assert confirmation.options["진행"] == "proceed"
        assert confirmation.options["건너뛰기"] == "skip"
        assert confirmation.options["중단"] == "abort"

    @patch('builtins.input')
    def test_get_user_input_proceed(self, mock_input):
        """Test getting user input for proceed option"""
        mock_input.return_value = "1"

        confirmation = UserConfirmation(
            message="Test message",
            options={"진행": "proceed", "건너뛰기": "skip", "중단": "abort"}
        )

        result = confirmation.get_user_input()

        assert result == "proceed"
        mock_input.assert_called_once()

    @patch('builtins.input')
    def test_get_user_input_invalid_then_valid(self, mock_input):
        """Test handling invalid input followed by valid input"""
        mock_input.side_effect = ["invalid", "2"]  # First invalid, second valid

        confirmation = UserConfirmation(
            message="Test message",
            options={"진행": "proceed", "건너뛰기": "skip", "중단": "abort"}
        )

        result = confirmation.get_user_input()

        assert result == "skip"
        assert mock_input.call_count == 2

    @patch('builtins.input')
    def test_get_user_input_abort(self, mock_input):
        """Test user choosing abort option"""
        mock_input.return_value = "3"

        confirmation = UserConfirmation(
            message="Test message",
            options={"진행": "proceed", "건너뛰기": "skip", "중단": "abort"}
        )

        with pytest.raises(UserAbortError, match="사용자가 중단을 선택했습니다"):
            confirmation.get_user_input(allow_abort=True)

    @patch('builtins.input')
    def test_get_user_input_no_abort(self, mock_input):
        """Test user choosing abort when not allowed"""
        mock_input.return_value = "3"

        confirmation = UserConfirmation(
            message="Test message",
            options={"진행": "proceed", "건너뛰기": "skip", "중단": "abort"}
        )

        result = confirmation.get_user_input(allow_abort=False)

        assert result == "abort"  # Returns the value but doesn't raise exception


class TestProgressDisplay:
    """Test cases for ProgressDisplay class"""

    def test_progress_initialization(self):
        """Test ProgressDisplay initialization"""
        progress = ProgressDisplay("테스트 배포")

        assert progress.title == "테스트 배포"
        assert progress.current_step == 0
        assert progress.total_steps == 0
        assert progress.steps == []

    def test_progress_add_step(self):
        """Test adding steps to progress display"""
        progress = ProgressDisplay("테스트 배포")

        progress.add_step("환경 설정")
        progress.add_step("애플리케이션 빌드")
        progress.add_step("배포")

        assert len(progress.steps) == 3
        assert progress.steps[0] == {"name": "환경 설정", "status": "pending"}
        assert progress.steps[1] == {"name": "애플리케이션 빌드", "status": "pending"}
        assert progress.steps[2] == {"name": "배포", "status": "pending"}
        assert progress.total_steps == 3

    def test_progress_update_step_status(self):
        """Test updating step status"""
        progress = ProgressDisplay("테스트 배포")
        progress.add_step("Step 1")
        progress.add_step("Step 2")

        progress.update_step_status(0, "completed")
        progress.update_step_status(1, "failed")

        assert progress.steps[0]["status"] == "completed"
        assert progress.steps[1]["status"] == "failed"

    @patch('click.echo')
    def test_progress_display_start(self, mock_echo):
        """Test displaying progress at start"""
        progress = ProgressDisplay("테스트 배포")
        progress.add_step("Step 1")
        progress.add_step("Step 2")

        progress.display()

        mock_echo.assert_called()
        # Check that progress bar is displayed
        call_args = mock_echo.call_args[0][0]
        assert "테스트 배포" in call_args
        assert "Step 1" in call_args

    @patch('click.echo')
    def test_progress_display_completion(self, mock_echo):
        """Test displaying progress completion"""
        progress = ProgressDisplay("테스트 배포")
        progress.add_step("Step 1")
        progress.update_step_status(0, "completed")

        progress.display()

        mock_echo.assert_called()

    def test_progress_get_percent_complete(self):
        """Test calculating percentage complete"""
        progress = ProgressDisplay("테스트 배포")
        progress.add_step("Step 1")
        progress.add_step("Step 2")
        progress.add_step("Step 3")

        # 0% complete initially
        assert progress.get_percent_complete() == 0

        # 33% complete after one step
        progress.update_step_status(0, "completed")
        assert progress.get_percent_complete() == 33

        # 66% complete after two steps
        progress.update_step_status(1, "completed")
        assert progress.get_percent_complete() == 66

        # 100% complete after all steps
        progress.update_step_status(2, "completed")
        assert progress.get_percent_complete() == 100


class TestInteractiveSession:
    """Test cases for InteractiveSession class"""

    def test_session_initialization(self):
        """Test InteractiveSession initialization"""
        session = InteractiveSession("test_session")

        assert session.session_id == "test_session"
        assert session.current_step == 0
        assert session.is_active is False
        assert session.user_responses == {}

    def test_session_start(self):
        """Test starting a session"""
        session = InteractiveSession("test_session")

        session.start()

        assert session.is_active is True
        assert session.started_at is not None

    def test_session_end(self):
        """Test ending a session"""
        session = InteractiveSession("test_session")
        session.start()

        session.end()

        assert session.is_active is False
        assert session.ended_at is not None

    def test_session_add_user_response(self):
        """Test adding user responses to session"""
        session = InteractiveSession("test_session")
        session.start()

        session.add_user_response("step1", "proceed")
        session.add_user_response("step2", "skip")

        assert session.user_responses["step1"] == "proceed"
        assert session.user_responses["step2"] == "skip"

    def test_session_get_user_response(self):
        """Test getting user responses from session"""
        session = InteractiveSession("test_session")
        session.start()
        session.add_user_response("step1", "proceed")

        response = session.get_user_response("step1")

        assert response == "proceed"

    def test_session_get_nonexistent_response(self):
        """Test getting nonexistent user response"""
        session = InteractiveSession("test_session")
        session.start()

        response = session.get_user_response("nonexistent")

        assert response is None


class TestFormatters:
    """Test cases for formatter functions"""

    def test_format_deployment_status_completed(self):
        """Test formatting completed deployment status"""
        status = format_deployment_status("completed", "Test Deployment")

        assert "✅" in status
        assert "완료" in status
        assert "Test Deployment" in status

    def test_format_deployment_status_failed(self):
        """Test formatting failed deployment status"""
        status = format_deployment_status("failed", "Test Deployment")

        assert "❌" in status
        assert "실패" in status
        assert "Test Deployment" in status

    def test_format_deployment_status_running(self):
        """Test formatting running deployment status"""
        status = format_deployment_status("running", "Test Deployment")

        assert "🔄" in status
        assert "진행 중" in status
        assert "Test Deployment" in status

    def test_format_step_progress(self):
        """Test formatting step progress"""
        progress = format_step_progress(3, 5, "Building Application")

        assert "Building Application" in progress
        assert "3/5" in progress
        assert "60%" in progress

    def test_format_error_message(self):
        """Test formatting error messages"""
        error = format_error_message("Configuration error", "Invalid config file")

        assert "❌" in error
        assert "Configuration error" in error
        assert "Invalid config file" in error

    def test_format_success_message(self):
        """Test formatting success messages"""
        success = format_success_message("Deployment completed", "All steps successful")

        assert "✅" in success
        assert "Deployment completed" in success
        assert "All steps successful" in success

    def test_format_korean_error_message(self):
        """Test formatting Korean error messages"""
        error = format_error_message("파일 오류", "파일을 찾을 수 없습니다")

        assert "❌" in error
        assert "파일 오류" in error
        assert "파일을 찾을 수 없습니다" in error


class TestValidators:
    """Test cases for validator functions"""

    def test_validate_config_file_valid(self):
        """Test validating valid config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
name: test_config
steps:
  - name: step1
    command: echo hello
""")
            config_path = f.name

        try:
            result = validate_config_file(config_path)
            assert result is True
        finally:
            os.unlink(config_path)

    def test_validate_config_file_invalid_extension(self):
        """Test validating config file with invalid extension"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            config_path = f.name

        try:
            with pytest.raises(ValidationError, match="지원하지 않는 파일 확장자"):
                validate_config_file(config_path)
        finally:
            os.unlink(config_path)

    def test_validate_config_file_not_found(self):
        """Test validating nonexistent config file"""
        with pytest.raises(ValidationError, match="파일을 찾을 수 없습니다"):
            validate_config_file("/nonexistent/file.yaml")

    def test_validate_deployment_name_valid(self):
        """Test validating valid deployment names"""
        valid_names = ["webapp", "api-server", "mobile-app", "backend-service"]

        for name in valid_names:
            result = validate_deployment_name(name)
            assert result is True

    def test_validate_deployment_name_invalid(self):
        """Test validating invalid deployment names"""
        invalid_names = [
            "",  # empty
            "123invalid",  # starts with number
            "invalid-name",  # contains hyphen
            "invalid name",  # contains space
            "invalid@name",  # contains special character
            "a" * 101  # too long
        ]

        for name in invalid_names:
            with pytest.raises(ValidationError):
                validate_deployment_name(name)

    def test_validate_step_command_valid(self):
        """Test validating valid step commands"""
        valid_commands = [
            "echo hello",
            "npm install",
            "python manage.py migrate",
            "docker build -t myapp .",
            "scp file.txt user@host:/path/"
        ]

        for command in valid_commands:
            result = validate_step_command(command)
            assert result is True

    def test_validate_step_command_invalid(self):
        """Test validating invalid step commands"""
        invalid_commands = [
            "",  # empty
            "   ",  # whitespace only
            None,  # None value
            "echo ; rm -rf /",  # dangerous command
            "sudo rm -rf /",  # privileged command
        ]

        for command in invalid_commands:
            with pytest.raises(ValidationError):
                validate_step_command(command)


class TestCLICommands:
    """Test cases for CLI commands"""

    @patch('moai_adk.cli.commands.DeploymentEngine')
    def test_deploy_command_success(self, mock_engine):
        """Test successful deploy command"""
        # Mock the engine and workflow
        mock_engine_instance = Mock()
        mock_workflow = Mock()
        mock_workflow.execute = AsyncMock(return_value=True)
        mock_engine_instance.get_workflow.return_value = mock_workflow
        mock_engine.return_value = mock_engine_instance

        # Mock click context
        ctx = Mock()
        ctx.obj = {'engine': mock_engine_instance}

        # Test command execution
        with patch('click.echo') as mock_echo:
            result = deploy_command.callback(ctx, "test_deployment")

        assert result is None
        mock_workflow.execute.assert_called_once()

    @patch('moai_adk.cli.commands.DeploymentEngine')
    def test_deploy_command_failure(self, mock_engine):
        """Test deploy command failure"""
        # Mock the engine and workflow
        mock_engine_instance = Mock()
        mock_workflow = Mock()
        mock_workflow.execute = AsyncMock(return_value=False)
        mock_engine_instance.get_workflow.return_value = mock_workflow
        mock_engine.return_value = mock_engine_instance

        # Mock click context
        ctx = Mock()
        ctx.obj = {'engine': mock_engine_instance}

        # Test command execution
        with patch('click.echo') as mock_echo:
            result = deploy_command.callback(ctx, "test_deployment")

        assert result is None

    def test_config_command_help(self):
        """Test config command help display"""
        with patch('click.echo') as mock_echo:
            with pytest.raises(SystemExit):
                config_command.callback(["--help"])

    def test_status_command_success(self, mock_engine):
        """Test successful status command"""
        # Mock engine with workflow
        mock_engine_instance = Mock()
        mock_workflow = Mock()
        mock_workflow.status = "completed"
        mock_workflow.steps = {
            "step1": Mock(status="completed"),
            "step2": Mock(status="completed")
        }
        mock_engine_instance.get_workflow.return_value = mock_workflow
        mock_engine.return_value = mock_engine_instance

        # Mock click context
        ctx = Mock()
        ctx.obj = {'engine': mock_engine_instance}

        # Test command execution
        with patch('click.echo') as mock_echo:
            result = status_command.callback(ctx, "test_deployment")

        assert result is None

    def test_list_command_workflows(self, mock_engine):
        """Test list command displaying workflows"""
        # Mock engine with multiple workflows
        mock_engine_instance = Mock()
        mock_engine_instance.workflows = {
            "webapp": Mock(config=Mock(name="Web Application")),
            "api": Mock(config=Mock(name="API Service"))
        }
        mock_engine.return_value = mock_engine_instance

        # Mock click context
        ctx = Mock()
        ctx.obj = {'engine': mock_engine_instance}

        # Test command execution
        with patch('click.echo') as mock_echo:
            result = list_command.callback(ctx)

        assert result is None
        # Should display both workflows
        call_count = mock_echo.call_count
        assert call_count >= 2

    def test_validate_command_valid_config(self):
        """Test validate command with valid config"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
name: test_config
steps:
  - name: step1
    command: echo hello
""")
            config_path = f.name

        try:
            with patch('click.echo') as mock_echo:
                result = validate_command.callback([config_path])

            assert result is None
        finally:
            os.unlink(config_path)

    def test_validate_command_invalid_config(self):
        """Test validate command with invalid config"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
# Invalid config - missing name
steps:
  - name: step1
    command: echo hello
""")
            config_path = f.name

        try:
            with patch('click.echo') as mock_echo:
                with pytest.raises(SystemExit):
                    validate_command.callback([config_path])
        finally:
            os.unlink(config_path)


class TestCLIIntegration:
    """Integration tests for CLI components"""

    @patch('moai_adk.cli.main.DeploymentEngine')
    def test_cli_deploy_with_confirmation(self, mock_engine):
        """Test CLI deploy with user confirmation"""
        # Mock engine and workflow
        mock_engine_instance = Mock()
        mock_workflow = Mock()
        mock_workflow.execute = AsyncMock(return_value=True)
        mock_engine_instance.get_workflow.return_value = mock_workflow
        mock_engine.return_value = mock_engine_instance

        with patch('moai_adk.cli.commands.get_user_input') as mock_input:
            mock_input.return_value = "진행"  # User chooses proceed

            with patch('click.echo') as mock_echo:
                # This would be called via CLI
                from moai_adk.cli.commands import deploy_with_confirmation
                result = deploy_with_confirmation(
                    engine=mock_engine_instance,
                    deployment_name="test_deployment"
                )

        assert result is True
        mock_workflow.execute.assert_called_once()

    def test_cli_help_command(self):
        """Test CLI help command functionality"""
        with pytest.raises(SystemExit):
            cli.main(["--help"])

    def test_cli_version_command(self):
        """Test CLI version command"""
        with patch('click.echo') as mock_echo:
            try:
                cli.main(["--version"])
            except SystemExit:
                pass  # Version command exits with code 0

        # Should have called echo with version info
        assert mock_echo.called

    def test_cli_interactive_workflow(self):
        """Test interactive CLI workflow"""
        # This would test the complete interactive experience
        # including user prompts, progress display, and error handling

        with patch('builtins.input') as mock_input:
            mock_input.return_value = "진행"  # User always chooses proceed

            with patch('click.echo') as mock_echo:
                # This would simulate the interactive deployment process
                # For now, just test that the components work together
                confirmation = UserConfirmation("테스트 메시지", {"진행": "proceed"})
                response = confirmation.get_user_input()

                assert response == "proceed"


class TestCLIErrorHandling:
    """Test CLI error handling scenarios"""

    def test_cli_error_creation(self):
        """Test CLIError creation"""
        error = CLIError("Test CLI error")

        assert str(error) == "Test CLI error"
        assert isinstance(error, Exception)

    def test_validation_error_creation(self):
        """Test ValidationError creation"""
        error = ValidationError("Invalid input")

        assert str(error) == "Invalid input"
        assert isinstance(error, CLIError)

    def test_configuration_error_creation(self):
        """Test ConfigurationError creation"""
        error = ConfigurationError("Config error")

        assert str(error) == "Config error"
        assert isinstance(error, CLIError)

    def test_user_abort_error_creation(self):
        """Test UserAbortError creation"""
        error = UserAbortError("User aborted")

        assert str(error) == "User aborted"
        assert isinstance(error, CLIError)

    @patch('moai_adk.cli.commands.get_user_input')
    def test_user_abort_handling(self, mock_input):
        """Test user abort handling"""
        mock_input.side_effect = UserAbortError("User aborted")

        with pytest.raises(UserAbortError, match="User aborted"):
            mock_input()

    @patch('moai_adk.cli.commands.validate_config_file')
    def test_config_validation_error_handling(self, mock_validate):
        """Test config validation error handling"""
        mock_validate.side_effect = ValidationError("Invalid config")

        with pytest.raises(ValidationError, match="Invalid config"):
            mock_validate("/invalid/path")


class TestWindowsCompatibility:
    """Test Windows-specific CLI functionality"""

    @patch('platform.system')
    def test_windows_path_handling(self, mock_system):
        """Test Windows path handling in CLI"""
        mock_system.return_value = 'Windows'

        # Test Windows-specific path validation
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            f.write("""
name: windows_test
steps:
  - name: copy_files
    command: copy C:\\source\\*.* D:\\destination\\
""")
            config_path = f.name

        try:
            result = validate_config_file(config_path)
            assert result is True
        finally:
            os.unlink(config_path)

    @patch('platform.system')
    def test_windows_encoding_handling(self, mock_system):
        """Test Windows encoding handling"""
        mock_system.return_value = 'Windows'

        # Test that Windows-specific encoding issues are handled
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', encoding='utf-8', delete=False) as f:
            f.write("""
name: encoding_test
steps:
  - name: korean_test
    command: echo "한국어 테스트"
""")
            config_path = f.name

        try:
            result = validate_config_file(config_path)
            assert result is True
        finally:
            os.unlink(config_path)

    @patch('platform.system')
    def test_windows_command_validation(self, mock_system):
        """Test Windows command validation"""
        mock_system.return_value = 'Windows'

        # Test Windows-legal commands
        valid_commands = [
            "copy file1.txt file2.txt",
            "xcopy source destination /E /I",
            "robocopy source destination /MIR"
        ]

        for command in valid_commands:
            result = validate_step_command(command)
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])