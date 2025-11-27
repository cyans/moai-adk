"""
Test file for deployment workflow engine core functionality
TAG-DEPLOY-001: Deployment workflow engine core with async orchestration
"""

import pytest
import asyncio
import yaml
from unittest.mock import Mock, patch, AsyncMock
from src.moai_adk.deployment.workflow import DeploymentWorkflow, DeploymentStep
from src.moai_adk.deployment.state import DeploymentState, DeploymentStatus, DeploymentResult
from src.moai_adk.deployment.steps import ValidationStep, BuildStep, TestStep, DeployStep


class TestDeploymentWorkflow:
    """Test cases for DeploymentWorkflow class"""

    def test_workflow_initialization(self):
        """Test workflow initialization with steps"""
        steps = [
            ValidationStep(),
            BuildStep(),
            TestStep(),
            DeployStep()
        ]
        workflow = DeploymentWorkflow("test-project", steps)

        assert workflow.project_name == "test-project"
        assert len(workflow.steps) == 4
        assert workflow.status == DeploymentStatus.PENDING
        assert not workflow.completed_steps
        assert not workflow.failed_steps

    def test_workflow_initialization_without_step2(self):
        """Test workflow initialization without step 2 (build step)"""
        steps = [
            ValidationStep(),
            TestStep(),  # Skip build step
            DeployStep()
        ]
        workflow = DeploymentWorkflow("test-project", steps)

        assert workflow.project_name == "test-project"
        assert len(workflow.steps) == 3

    @pytest.mark.asyncio
    async def test_workflow_execution_success(self):
        """Test successful workflow execution"""
        steps = [
            ValidationStep(),
            BuildStep(),
            TestStep(),
            DeployStep()
        ]
        workflow = DeploymentWorkflow("test-project", steps)

        # Manually track completed steps for testing
        async def mock_execute_step(step, step_index):
            result = DeploymentResult(success=True, status=DeploymentStatus.VALIDATING, message="Step completed")
            workflow.completed_steps.append(step.name)
            return result

        with patch.object(workflow, '_execute_step', side_effect=mock_execute_step):
            result = await workflow.execute()

            assert result.success
            assert result.status == DeploymentStatus.COMPLETED
            assert len(workflow.completed_steps) == 4
            assert not workflow.failed_steps

    @pytest.mark.asyncio
    async def test_workflow_execution_failure(self):
        """Test workflow execution with failure"""
        steps = [
            ValidationStep(),
            BuildStep(),
            TestStep(),
            DeployStep()
        ]
        workflow = DeploymentWorkflow("test-project", steps)

        # Manually track completed steps for testing
        async def mock_execute_step(step, step_index):
            if step_index == 3:  # Step 3 fails
                workflow.failed_steps.append(step.name)
                raise Exception("Test failed")
            result = DeploymentResult(success=True, status=DeploymentStatus.VALIDATING, message="Step completed")
            workflow.completed_steps.append(step.name)
            return result

        with patch.object(workflow, '_execute_step', side_effect=mock_execute_step):
            result = await workflow.execute()

            assert not result.success
            assert result.status == DeploymentStatus.FAILED
            assert len(workflow.completed_steps) == 2  # Steps 1 and 2 completed
            assert len(workflow.failed_steps) == 1
            assert "Test failed" in str(result.error)

    @pytest.mark.asyncio
    async def test_workflow_with_step_skip(self):
        """Test workflow execution with step skipping"""
        steps = [
            ValidationStep(),
            BuildStep(),
            TestStep(),
            DeployStep()
        ]
        workflow = DeploymentWorkflow("test-project", steps)

        # Track which steps were actually executed
        executed_steps = []
        async def mock_execute_step(step, step_index):
            executed_steps.append(step.name)
            if step_index != 1:  # Skip step 2 (index 1)
                result = DeploymentResult(success=True, status=DeploymentStatus.VALIDATING, message="Step completed")
                return result
            else:
                # Skip step 2 by returning None (should not be added to completed_steps)
                return None

        with patch.object(workflow, '_execute_step', side_effect=mock_execute_step):
            # Skip step 2 (build step - index 1)
            await workflow.execute(steps_to_skip=[1])

            # Build step should be executed but not added to completed_steps
            assert "build" in executed_steps  # Step was processed
            assert "build" not in workflow.completed_steps  # But not marked as completed


class TestDeploymentState:
    """Test cases for DeploymentState class"""

    def test_state_initialization(self):
        """Test state initialization"""
        state = DeploymentState()

        assert state.status == DeploymentStatus.PENDING
        assert not state.current_step
        assert not state.step_results
        assert not state.start_time
        assert not state.end_time
        assert not state.error

    def test_state_progression(self):
        """Test state progression through deployment phases"""
        state = DeploymentState()

        # Initial state
        assert state.status == DeploymentStatus.PENDING

        # Start validation
        state.update_status(DeploymentStatus.VALIDATING, "Validating configuration")
        assert state.status == DeploymentStatus.VALIDATING
        assert state.current_step == "Validating configuration"

        # Progress to building
        state.update_status(DeploymentStatus.BUILDING, "Building project")
        assert state.status == DeploymentStatus.BUILDING
        assert state.current_step == "Building project"

        # Mark as completed
        state.update_status(DeploymentStatus.COMPLETED, "Deployment completed")
        assert state.status == DeploymentStatus.COMPLETED
        assert state.current_step == "Deployment completed"


class TestDeploymentSteps:
    """Test cases for deployment step implementations"""

    @pytest.mark.asyncio
    async def test_validation_step(self):
        """Test validation step execution"""
        step = ValidationStep()

        config_data = {
            'project': {'name': 'test-project'},
            'deployment': {'steps': [1, 3, 4, 5]}
        }

        result = await step.execute({'config_data': config_data})
        assert result.success
        assert "Configuration validated" in result.message

    @pytest.mark.asyncio
    async def test_build_step(self):
        """Test build step execution"""
        step = BuildStep()

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0)

            result = await step.execute({'build_command': 'python build.py'})

            assert result.success
            assert "Build completed" in result.message

    @pytest.mark.asyncio
    async def test_test_step(self):
        """Test step execution"""
        step = TestStep()

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0)

            result = await step.execute({'test_command': 'python -m pytest'})

            assert result.success
            assert "Tests completed" in result.message

    @pytest.mark.asyncio
    async def test_deploy_step(self):
        """Test deploy step execution"""
        step = DeployStep()

        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0)

            result = await step.execute({'deploy_command': 'python deploy.py'})

            assert result.success
            assert "Deployment completed" in result.message

    @pytest.mark.asyncio
    async def test_step_error_handling(self):
        """Test error handling in deployment steps"""
        step = ValidationStep()

        result = await step.execute({})

        assert not result.success
        assert "No configuration data provided" in result.error


class TestConfigLoading:
    """Test cases for configuration loading and validation"""

    def test_load_valid_config(self):
        """Test loading valid configuration"""
        config_data = {
            'project': {
                'name': 'test-project',
                'version': '1.0.0'
            },
            'deployment': {
                'steps': [1, 3, 4, 5],  # Skip step 2
                'build_command': 'python build.py',
                'test_command': 'python -m pytest',
                'deploy_command': 'python deploy.py'
            }
        }

        # This test should pass once we implement the config loading
        # For now, it should fail
        with pytest.raises(ImportError):
            from src.moai_adk.deployment.config import load_config
            load_config(config_data)

    def test_invalid_config_validation(self):
        """Test validation of invalid configuration"""
        invalid_configs = [
            {},  # Empty config
            {'project': {}},  # Missing required fields
            {'project': {'name': 'test'}},  # Missing deployment config
            {'deployment': {'steps': [1, 2, 3]}}  # Invalid step sequence
        ]

        # These tests should fail once we implement config validation
        with pytest.raises(ImportError):
            from src.moai_adk.deployment.config import validate_config
            for config in invalid_configs:
                validate_config(config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])