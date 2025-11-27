"""
Test suite for deployment workflow engine core functionality.
TAG-DEPLOY-001: Deployment workflow engine core
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Import the classes to be tested (will be implemented in GREEN phase)
from moai_adk.deployment.workflow import DeploymentWorkflow
from moai_adk.deployment.engine import DeploymentEngine
from moai_adk.deployment.steps import DeploymentStep, StepStatus
from moai_adk.deployment.config import DeploymentConfig
from moai_adk.deployment.events import DeploymentEvent, EventType
from moai_adk.deployment.errors import DeploymentError, StepError, ConfigurationError


class TestDeploymentStep:
    """Test cases for DeploymentStep class"""

    def test_step_creation_with_valid_config(self):
        """Test creating a deployment step with valid configuration"""
        step_config = {
            "name": "test_step",
            "description": "Test deployment step",
            "command": "echo hello",
            "enabled": True,
            "dependencies": []
        }

        step = DeploymentStep(step_config)

        assert step.name == "test_step"
        assert step.description == "Test deployment step"
        assert step.command == "echo hello"
        assert step.enabled is True
        assert step.status == StepStatus.PENDING
        assert step.dependencies == []
        assert step.timeout == 300  # default timeout

    def test_step_creation_with_dependencies(self):
        """Test creating a step with dependencies"""
        step_config = {
            "name": "dependent_step",
            "description": "Deploys after prerequisite",
            "command": "npm run build",
            "dependencies": ["setup", "install"]
        }

        step = DeploymentStep(step_config)

        assert step.dependencies == ["setup", "install"]
        assert not step.can_execute()

    def test_step_can_execute_without_dependencies(self):
        """Test that step can execute without dependencies"""
        step_config = {
            "name": "standalone_step",
            "command": "echo standalone"
        }

        step = DeploymentStep(step_config)

        assert step.can_execute()

    def test_step_can_execute_with_completed_dependencies(self):
        """Test that step can execute when dependencies are completed"""
        step_config = {
            "name": "dependent_step",
            "command": "echo after deps",
            "dependencies": ["step1", "step2"]
        }

        step = DeploymentStep(step_config)
        # Mark dependencies as completed
        step.dependencies_status = {"step1": StepStatus.COMPLETED, "step2": StepStatus.COMPLETED}

        assert step.can_execute()

    def test_step_mark_completed(self):
        """Test marking a step as completed"""
        step_config = {"name": "test_step", "command": "echo test"}
        step = DeploymentStep(step_config)

        step.mark_completed()

        assert step.status == StepStatus.COMPLETED
        assert step.completed_at is not None

    def test_step_mark_failed(self):
        """Test marking a step as failed"""
        step_config = {"name": "test_step", "command": "exit 1"}
        step = DeploymentStep(step_config)

        step.mark_failed("Test error")

        assert step.status == StepStatus.FAILED
        assert step.error == "Test error"

    @pytest.mark.asyncio
    async def test_step_execute_success(self):
        """Test successful step execution"""
        step_config = {"name": "success_step", "command": "echo success"}
        step = DeploymentStep(step_config)

        with patch('asyncio.create_subprocess_shell') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_subprocess.return_value = (mock_process, AsyncMock())

            result = await step.execute()

            assert result is True
            assert step.status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_step_execute_failure(self):
        """Test step execution failure"""
        step_config = {"name": "fail_step", "command": "exit 1"}
        step = DeploymentStep(step_config)

        with patch('asyncio.create_subprocess_shell') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_subprocess.return_value = (mock_process, AsyncMock())

            result = await step.execute()

            assert result is False
            assert step.status == StepStatus.FAILED

    def test_step_timeout_configuration(self):
        """Test step timeout configuration"""
        step_config = {
            "name": "long_step",
            "command": "sleep 10",
            "timeout": 60
        }

        step = DeploymentStep(step_config)

        assert step.timeout == 60


class TestDeploymentConfig:
    """Test cases for DeploymentConfig class"""

    def test_config_creation_from_dict(self):
        """Test creating config from dictionary"""
        config_dict = {
            "name": "test_deployment",
            "description": "Test deployment configuration",
            "steps": [
                {"name": "step1", "command": "echo step1"},
                {"name": "step2", "command": "echo step2"}
            ],
            "environment": {"ENV_VAR": "value"},
            "timeout": 1800
        }

        config = DeploymentConfig(config_dict)

        assert config.name == "test_deployment"
        assert config.description == "Test deployment configuration"
        assert len(config.steps) == 2
        assert config.environment == {"ENV_VAR": "value"}
        assert config.timeout == 1800

    def test_config_validation_success(self):
        """Test successful config validation"""
        config_dict = {
            "name": "valid_config",
            "steps": [
                {"name": "step1", "command": "echo hello"}
            ]
        }

        config = DeploymentConfig(config_dict)

        assert config.validate() is True

    def test_config_validation_missing_name(self):
        """Test config validation fails without name"""
        config_dict = {
            "steps": [
                {"name": "step1", "command": "echo hello"}
            ]
        }

        config = DeploymentConfig(config_dict)

        assert config.validate() is False
        assert "name" in config.errors

    def test_config_validation_empty_steps(self):
        """Test config validation fails with empty steps"""
        config_dict = {"name": "empty_config", "steps": []}

        config = DeploymentConfig(config_dict)

        assert config.validate() is False
        assert "steps" in config.errors

    def test_config_step_name_conflict(self):
        """Test config validation catches duplicate step names"""
        config_dict = {
            "name": "conflict_config",
            "steps": [
                {"name": "duplicate", "command": "echo 1"},
                {"name": "duplicate", "command": "echo 2"}
            ]
        }

        config = DeploymentConfig(config_dict)

        assert config.validate() is False
        assert "duplicate step names" in str(config.errors).lower()

    def test_config_to_dict(self):
        """Test converting config back to dictionary"""
        config_dict = {
            "name": "roundtrip_test",
            "steps": [{"name": "step1", "command": "echo test"}]
        }

        config = DeploymentConfig(config_dict)
        result = config.to_dict()

        assert result == config_dict


class TestDeploymentEvent:
    """Test cases for DeploymentEvent class"""

    def test_event_creation(self):
        """Test creating deployment events"""
        event = DeploymentEvent(
            event_type=EventType.STARTED,
            step_name="test_step",
            timestamp=1234567890,
            data={"key": "value"}
        )

        assert event.event_type == EventType.STARTED
        assert event.step_name == "test_step"
        assert event.timestamp == 1234567890
        assert event.data == {"key": "value"}

    def test_event_creation_without_data(self):
        """Test creating events without data"""
        event = DeploymentEvent(EventType.COMPLETED, "test_step", 1234567890)

        assert event.data is None

    def test_event_to_dict(self):
        """Test converting event to dictionary"""
        event = DeploymentEvent(EventType.FAILED, "test_step", 1234567890, {"error": "test"})

        result = event.to_dict()

        expected = {
            "event_type": "FAILED",
            "step_name": "test_step",
            "timestamp": 1234567890,
            "data": {"error": "test"}
        }

        assert result == expected


class TestDeploymentWorkflow:
    """Test cases for DeploymentWorkflow class"""

    def test_workflow_creation(self):
        """Test creating a deployment workflow"""
        config = DeploymentConfig({
            "name": "test_workflow",
            "steps": [{"name": "step1", "command": "echo hello"}]
        })

        workflow = DeploymentWorkflow(config)

        assert workflow.config == config
        assert workflow.status == "pending"
        assert len(workflow.steps) == 1
        assert workflow.steps["step1"].name == "step1"

    def test_workflow_build_from_config(self):
        """Test building workflow from configuration"""
        config = DeploymentConfig({
            "name": "build_test",
            "steps": [
                {"name": "setup", "command": "echo setup", "dependencies": []},
                {"name": "build", "command": "echo build", "dependencies": ["setup"]}
            ]
        })

        workflow = DeploymentWorkflow(config)

        assert len(workflow.execution_order) == 2
        assert workflow.execution_order[0].name == "setup"
        assert workflow.execution_order[1].name == "build"

    def test_workflow_execute_empty_config(self):
        """Test workflow execution with empty config"""
        empty_config = DeploymentConfig({"name": "empty", "steps": []})
        workflow = DeploymentWorkflow(empty_config)

        with pytest.raises(StepError, match="No steps to execute"):
            workflow.execute()

    @pytest.mark.asyncio
    async def test_workflow_execute_success(self):
        """Test successful workflow execution"""
        config = DeploymentConfig({
            "name": "success_workflow",
            "steps": [
                {"name": "step1", "command": "echo step1"},
                {"name": "step2", "command": "echo step2"}
            ]
        })

        workflow = DeploymentWorkflow(config)

        # Mock step execution to always succeed
        for step in workflow.steps.values():
            step.execute = AsyncMock(return_value=True)

        result = await workflow.execute()

        assert result is True
        assert workflow.status == "completed"

        # Verify all steps were executed
        for step in workflow.steps.values():
            step.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_execute_step_failure(self):
        """Test workflow execution when a step fails"""
        config = DeploymentConfig({
            "name": "fail_workflow",
            "steps": [
                {"name": "success_step", "command": "echo success"},
                {"name": "fail_step", "command": "exit 1"},
                {"name": "skipped_step", "command": "echo skipped"}
            ]
        })

        workflow = DeploymentWorkflow(config)

        # Mock first step success, second step failure
        workflow.steps["success_step"].execute = AsyncMock(return_value=True)
        workflow.steps["fail_step"].execute = AsyncMock(return_value=False)

        result = await workflow.execute()

        assert result is False
        assert workflow.status == "failed"

        # Verify skipped step was not executed
        assert not workflow.steps["skipped_step"].execute.called

    @pytest.mark.asyncio
    async def test_workflow_with_dependencies(self):
        """Test workflow execution with dependencies"""
        config = DeploymentConfig({
            "name": "dependency_workflow",
            "steps": [
                {"name": "setup", "command": "echo setup"},
                {"name": "build", "command": "echo build", "dependencies": ["setup"]},
                {"name": "deploy", "command": "echo deploy", "dependencies": ["build"]}
            ]
        })

        workflow = DeploymentWorkflow(config)

        # Mock all steps as successful
        for step in workflow.steps.values():
            step.execute = AsyncMock(return_value=True)

        result = await workflow.execute()

        assert result is True

        # Verify execution order
        calls = [step.execute.call_count for step in workflow.execution_order]
        assert all(call == 1 for call in calls)

    def test_workflow_event_emission(self):
        """Test that workflow emits events"""
        config = DeploymentConfig({
            "name": "event_test",
            "steps": [{"name": "test_step", "command": "echo test"}]
        })

        workflow = DeploymentWorkflow(config)

        # Mock event handler
        events_received = []
        def handle_event(event):
            events_received.append(event)

        workflow.add_event_handler(handle_event)

        # Execute workflow
        async def run_workflow():
            workflow.steps["test_step"].execute = AsyncMock(return_value=True)
            await workflow.execute()

        # Run the async test
        import asyncio
        asyncio.run(run_workflow())

        # Verify events were emitted
        assert len(events_received) > 0

        # Check for key event types
        event_types = [event.event_type.value for event in events_received]
        assert EventType.STARTED.value in event_types
        assert EventType.COMPLETED.value in event_types


class TestDeploymentEngine:
    """Test cases for DeploymentEngine class"""

    def test_engine_creation(self):
        """Test creating deployment engine"""
        engine = DeploymentEngine()

        assert engine.workflows == {}
        assert engine.event_handlers == []

    def test_engine_register_workflow(self):
        """Test registering a workflow with the engine"""
        engine = DeploymentEngine()
        config = DeploymentConfig({"name": "test_workflow", "steps": []})
        workflow = DeploymentWorkflow(config)

        engine.register_workflow("test", workflow)

        assert "test" in engine.workflows
        assert engine.workflows["test"] == workflow

    def test_engine_get_workflow(self):
        """Test getting a workflow from engine"""
        engine = DeploymentEngine()
        config = DeploymentConfig({"name": "get_test", "steps": []})
        workflow = DeploymentWorkflow(config)

        engine.register_workflow("get_test", workflow)

        retrieved = engine.get_workflow("get_test")
        assert retrieved == workflow

    def test_engine_get_nonexistent_workflow(self):
        """Test getting nonexistent workflow raises error"""
        engine = DeploymentEngine()

        with pytest.raises(DeploymentError, match="Workflow not found"):
            engine.get_workflow("nonexistent")

    @pytest.mark.asyncio
    async def test_engine_execute_workflow_success(self):
        """Test engine executes workflow successfully"""
        engine = DeploymentEngine()
        config = DeploymentConfig({
            "name": "engine_test",
            "steps": [{"name": "step1", "command": "echo test"}]
        })
        workflow = DeploymentWorkflow(config)

        engine.register_workflow("engine_test", workflow)

        # Mock successful execution
        workflow.execute = AsyncMock(return_value=True)

        result = await engine.execute_workflow("engine_test")

        assert result is True
        workflow.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_engine_execute_nonexistent_workflow(self):
        """Test executing nonexistent workflow raises error"""
        engine = DeploymentEngine()

        with pytest.raises(DeploymentError, match="Workflow not found"):
            await engine.execute_workflow("nonexistent")

    def test_engine_event_handling(self):
        """Test engine event handling"""
        engine = DeploymentEngine()
        events_received = []

        def event_handler(event):
            events_received.append(event)

        engine.add_event_handler(event_handler)

        # Verify handler was added
        assert event_handler in engine.event_handlers

        # Test event propagation would happen during workflow execution
        # (actual event propagation tested in workflow tests)


class TestDeploymentErrors:
    """Test cases for custom error classes"""

    def test_deployment_error(self):
        """Test DeploymentError creation"""
        error = DeploymentError("Test error message")

        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_step_error(self):
        """Test StepError creation"""
        error = StepError("Step failed", "test_step")

        assert str(error) == "Step failed in test_step"
        assert error.step_name == "test_step"

    def test_configuration_error(self):
        """Test ConfigurationError creation"""
        error = ConfigurationError("Invalid config")

        assert str(error) == "Invalid config"
        assert isinstance(error, DeploymentError)

    def test_error_hierarchy(self):
        """Test error class hierarchy"""
        assert issubclass(StepError, DeploymentError)
        assert issubclass(ConfigurationError, DeploymentError)


class TestIntegrationScenarios:
    """Integration test scenarios for the deployment system"""

    @pytest.mark.asyncio
    async def test_complete_deployment_scenario(self):
        """Test a complete deployment scenario"""
        # Create configuration for a typical deployment
        config_dict = {
            "name": "webapp_deployment",
            "description": "Deploy web application to production",
            "timeout": 3600,
            "environment": {
                "NODE_ENV": "production",
                "PORT": "3000"
            },
            "steps": [
                {
                    "name": "setup_environment",
                    "description": "Setup production environment",
                    "command": "npm ci",
                    "dependencies": []
                },
                {
                    "name": "build_application",
                    "description": "Build application assets",
                    "command": "npm run build",
                    "dependencies": ["setup_environment"]
                },
                {
                    "name": "run_tests",
                    "description": "Run production tests",
                    "command": "npm test",
                    "dependencies": ["build_application"],
                    "enabled": True
                },
                {
                    "name": "deploy_to_server",
                    "description": "Deploy to production server",
                    "command": "rsync -av dist/ server:/var/www/",
                    "dependencies": ["run_tests"]
                }
            ]
        }

        # Create workflow and engine
        config = DeploymentConfig(config_dict)
        workflow = DeploymentWorkflow(config)
        engine = DeploymentEngine()
        engine.register_workflow("webapp_deployment", workflow)

        # Mock step executions for successful deployment
        for step in workflow.steps.values():
            step.execute = AsyncMock(return_value=True)

        # Execute deployment
        result = await engine.execute_workflow("webapp_deployment")

        # Verify deployment succeeded
        assert result is True
        assert workflow.status == "completed"

        # Verify execution order
        assert len(workflow.execution_order) == 4
        expected_order = ["setup_environment", "build_application", "run_tests", "deploy_to_server"]
        actual_order = [step.name for step in workflow.execution_order]
        assert actual_order == expected_order

    def test_configuration_validation_scenario(self):
        """Test configuration validation catches common issues"""
        # Invalid configuration with multiple issues
        invalid_config = {
            "name": "",  # Empty name
            "steps": [
                {"name": "step1", "command": "echo 1"},
                {"name": "step1", "command": "echo 2"},  # Duplicate name
                {"command": "echo 3"}  # Missing name
            ]
        }

        config = DeploymentConfig(invalid_config)

        assert config.validate() is False

        # Check that all errors are captured
        assert "name" in config.errors
        assert "duplicate" in str(config.errors).lower()
        assert "step name" in str(config.errors).lower()

    @pytest.mark.asyncio
    async def test_rollback_scenario(self):
        """Test rollback mechanism when deployment fails"""
        config_dict = {
            "name": "deployment_with_rollback",
            "steps": [
                {"name": "setup", "command": "echo setup"},
                {"name": "deploy", "command": "exit 1"},  # This will fail
                {"name": "rollback", "command": "echo rollback"}
            ]
        }

        config = DeploymentConfig(config_dict)
        workflow = DeploymentWorkflow(config)
        engine = DeploymentEngine()
        engine.register_workflow("rollback_test", workflow)

        # Mock setup success, deploy failure, rollback not called initially
        workflow.steps["setup"].execute = AsyncMock(return_value=True)
        workflow.steps["deploy"].execute = AsyncMock(return_value=False)
        workflow.steps["rollback"].execute = AsyncMock(return_value=True)

        result = await engine.execute_workflow("rollback_test")

        assert result is False
        assert workflow.status == "failed"

        # Verify setup was executed, deploy failed, rollback was NOT executed
        # (rollback logic would be implemented in workflow engine)

    def test_windows_path_handling_scenario(self):
        """Test Windows-specific path handling"""
        # Configuration with Windows paths
        config_dict = {
            "name": "windows_deployment",
            "steps": [
                {
                    "name": "copy_files",
                    "command": "copy C:\\source\\*.* D:\\destination\\",
                    "working_directory": "C:\\project\\build"
                }
            ]
        }

        config = DeploymentConfig(config_dict)
        workflow = DeploymentWorkflow(config)

        # Verify step configuration includes Windows paths
        step = workflow.steps["copy_files"]
        assert step.command == "copy C:\\source\\*.* D:\\destination\\"
        assert step.working_directory == "C:\\project\\build"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])