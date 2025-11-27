"""
Deployment step implementations for Windows deployment workflow
"""

import subprocess
import yaml
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .state import DeploymentResult, DeploymentStatus


class DeploymentStep(ABC):
    """Abstract base class for deployment steps"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> DeploymentResult:
        """Execute the deployment step"""
        pass

    def _validate_step_parameters(self, context: Dict[str, Any], required_params: list) -> bool:
        """Validate that required parameters are present in context"""
        for param in required_params:
            if param not in context:
                return False
        return True


class ValidationStep(DeploymentStep):
    """Step 1: Validate configuration and environment"""

    def __init__(self):
        super().__init__("validation", "Validating configuration and environment")

    async def execute(self, context: Dict[str, Any]) -> DeploymentResult:
        """Execute validation step"""
        try:
            # Load configuration
            config_data = context.get('config_data')
            if not config_data:
                return DeploymentResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    error="No configuration data provided"
                )

            # Parse YAML configuration
            if isinstance(config_data, str):
                config = yaml.safe_load(config_data)
            else:
                config = config_data  # Already parsed dict

            # Validate required fields
            required_fields = ['project', 'deployment']
            for field in required_fields:
                if field not in config:
                    return DeploymentResult(
                        success=False,
                        status=DeploymentStatus.FAILED,
                        error=f"Missing required field: {field}"
                    )

            # Validate project structure
            project_config = config['project']
            if not project_config.get('name'):
                return DeploymentResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    error="Project name is required"
                )

            # Validate deployment steps
            deployment_config = config['deployment']
            steps = deployment_config.get('steps', [])
            if not steps:
                return DeploymentResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    error="No deployment steps configured"
                )

            # Validate step sequence (should be 1,3,4,5 - skipping step 2)
            expected_steps = [1, 3, 4, 5]
            if not all(step in expected_steps for step in steps):
                return DeploymentResult(
                    success=False,
                    status=DeploymentStatus.FAILED,
                    error=f"Invalid step sequence. Expected subset of {expected_steps}"
                )

            return DeploymentResult(
                success=True,
                status=DeploymentStatus.VALIDATING,
                message="Configuration validated successfully",
                data={'config': config}
            )

        except yaml.YAMLError as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                error=f"Invalid YAML configuration: {str(e)}"
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                error=f"Validation failed: {str(e)}"
            )


class BuildStep(DeploymentStep):
    """Step 2: Build project (skipped by default)"""

    def __init__(self):
        super().__init__("build", "Building project")

    async def execute(self, context: Dict[str, Any]) -> DeploymentResult:
        """Execute build step"""
        try:
            build_command = context.get('build_command', 'python setup.py build')

            # Execute build command
            process = subprocess.run(
                build_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )

            return DeploymentResult(
                success=True,
                status=DeploymentStatus.BUILDING,
                message="Build completed successfully",
                data={'output': process.stdout}
            )

        except subprocess.CalledProcessError as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                error=f"Build failed: {e.stderr}"
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                error=f"Build error: {str(e)}"
            )


class TestStep(DeploymentStep):
    """Step 3: Run tests"""

    def __init__(self):
        super().__init__("test", "Running tests")

    async def execute(self, context: Dict[str, Any]) -> DeploymentResult:
        """Execute test step"""
        try:
            test_command = context.get('test_command', 'python -m pytest')

            # Execute test command
            process = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )

            return DeploymentResult(
                success=True,
                status=DeploymentStatus.TESTING,
                message="Tests completed successfully",
                data={'output': process.stdout}
            )

        except subprocess.CalledProcessError as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                error=f"Tests failed: {e.stderr}"
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                error=f"Test error: {str(e)}"
            )


class DeployStep(DeploymentStep):
    """Step 4: Deploy to target environment"""

    def __init__(self):
        super().__init__("deploy", "Deploying to target environment")

    async def execute(self, context: Dict[str, Any]) -> DeploymentResult:
        """Execute deploy step"""
        try:
            deploy_command = context.get('deploy_command', 'python deploy.py')

            # Execute deploy command
            process = subprocess.run(
                deploy_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )

            return DeploymentResult(
                success=True,
                status=DeploymentStatus.DEPLOYING,
                message="Deployment completed successfully",
                data={'output': process.stdout}
            )

        except subprocess.CalledProcessError as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                error=f"Deployment failed: {e.stderr}"
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                error=f"Deployment error: {str(e)}"
            )


class WorkflowStepFactory:
    """Factory for creating deployment steps"""

    @staticmethod
    def create_step(step_number: int) -> Optional[DeploymentStep]:
        """Create a deployment step by number"""
        step_mapping = {
            1: ValidationStep,
            2: BuildStep,
            3: TestStep,
            4: DeployStep,
            5: DeployStep  # Step 5 is also deploy
        }

        step_class = step_mapping.get(step_number)
        return step_class() if step_class else None

    @staticmethod
    def create_steps_from_config(step_numbers: list) -> list:
        """Create steps from configuration"""
        steps = []
        for step_number in step_numbers:
            step = WorkflowStepFactory.create_step(step_number)
            if step:
                steps.append(step)
        return steps