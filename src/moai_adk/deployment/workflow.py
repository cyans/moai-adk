"""
Deployment workflow orchestration engine for Windows deployment
"""

import asyncio
import traceback
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from .state import DeploymentResult, DeploymentState, DeploymentStatus
from .steps import DeploymentStep, WorkflowStepFactory


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    success: bool
    status: DeploymentStatus
    message: str = ""
    error: Optional[str] = None
    data: Dict[str, Any] = None


class DeploymentWorkflow:
    """Main deployment workflow orchestrator"""

    def __init__(self, project_name: str, steps: List[DeploymentStep]):
        self.project_name = project_name
        self.steps = steps
        self.state = DeploymentState()
        self.context: Dict[str, Any] = {}
        self.status = DeploymentStatus.PENDING  # Backward compatibility for tests
        self.completed_steps = []  # Backward compatibility for tests
        self.failed_steps = []  # Backward compatibility for tests

    def set_context(self, context: Dict[str, Any]):
        """Set the context for workflow execution"""
        self.context.update(context)

    async def execute(self, steps_to_skip: Optional[List[int]] = None) -> WorkflowResult:
        """Execute the deployment workflow"""
        if steps_to_skip is None:
            steps_to_skip = []

        try:
            self.state.update_status(DeploymentStatus.VALIDATING, f"Starting deployment for {self.project_name}")

            # Execute steps in sequence
            for i, step in enumerate(self.steps):
                step_index = i + 1  # 1-based indexing

                # Skip specified steps
                if step_index in steps_to_skip:
                    continue

                # Execute step
                step_result = await self._execute_step(step, step_index)

                if step_result.success:
                    self.state.mark_step_completed(step.name, step_result)
                    self.state.update_status(
                        self._get_next_status(step_index),
                        f"Completed {step.description}"
                    )
                else:
                    self.state.mark_step_failed(step.name, step_result)
                    return WorkflowResult(
                        success=False,
                        status=DeploymentStatus.FAILED,
                        message=f"Step {step_index} ({step.name}) failed",
                        error=step_result.error,
                        data=self.state.to_dict()
                    )

            # All steps completed successfully
            self.state.update_status(DeploymentStatus.COMPLETED, "Deployment completed")
            return WorkflowResult(
                success=True,
                status=DeploymentStatus.COMPLETED,
                message=f"Deployment completed successfully for {self.project_name}",
                data=self.state.to_dict()
            )

        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Unexpected error during deployment: {str(e)}"
            self.state.update_status(DeploymentStatus.FAILED, error_msg)
            self.state.error = error_msg

            return WorkflowResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message="Deployment failed due to unexpected error",
                error=error_msg,
                data=self.state.to_dict()
            )

    async def _execute_step(self, step: DeploymentStep, step_index: int) -> DeploymentResult:
        """Execute a single deployment step"""
        try:
            self.state.update_status(
                self._get_step_status(step_index),
                f"Executing {step.description}"
            )

            # Add step index to context for reference
            execution_context = self.context.copy()
            execution_context['step_index'] = step_index
            execution_context['step_name'] = step.name

            # Execute the step
            result = await step.execute(execution_context)

            return result

        except Exception as e:
            # Wrap any unexpected errors
            return DeploymentResult(
                success=False,
                status=DeploymentStatus.FAILED,
                error=f"Step {step_index} execution failed: {str(e)}"
            )

    def _get_step_status(self, step_index: int) -> DeploymentStatus:
        """Get the status for a specific step"""
        status_mapping = {
            1: DeploymentStatus.VALIDATING,
            2: DeploymentStatus.BUILDING,
            3: DeploymentStatus.TESTING,
            4: DeploymentStatus.DEPLOYING,
            5: DeploymentStatus.DEPLOYING
        }
        return status_mapping.get(step_index, DeploymentStatus.VALIDATING)

    def _get_next_status(self, step_index: int) -> DeploymentStatus:
        """Get the next status after completing a step"""
        if step_index < len(self.steps):
            return self._get_step_status(step_index + 1)
        return DeploymentStatus.COMPLETED

    def get_state(self) -> DeploymentState:
        """Get the current deployment state"""
        return self.state

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary for serialization"""
        return {
            'project_name': self.project_name,
            'steps': [{'name': step.name, 'description': step.description} for step in self.steps],
            'state': self.state.to_dict(),
            'context': self.context
        }

    @classmethod
    def from_config(cls, project_name: str, config_data: Dict[str, Any]) -> 'DeploymentWorkflow':
        """Create workflow from configuration"""
        deployment_config = config_data.get('deployment', {})
        step_numbers = deployment_config.get('steps', [1, 3, 4, 5])  # Default: skip step 2

        # Create steps from configuration
        steps = WorkflowStepFactory.create_steps_from_config(step_numbers)

        workflow = cls(project_name, steps)
        workflow.set_context(config_data)

        return workflow


class DeploymentOrchestrator:
    """High-level deployment orchestrator with multiple workflow support"""

    def __init__(self):
        self.workflows: Dict[str, DeploymentWorkflow] = {}
        self.active_workflows: Dict[str, asyncio.Task] = {}

    async def start_deployment(self, workflow_id: str, project_name: str, config_data: Dict[str, Any]) -> WorkflowResult:
        """Start a new deployment workflow"""
        if workflow_id in self.active_workflows:
            return WorkflowResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"Workflow {workflow_id} is already running",
                error="Workflow already in progress"
            )

        # Create and start workflow
        workflow = DeploymentWorkflow.from_config(project_name, config_data)
        self.workflows[workflow_id] = workflow

        # Start execution in background
        task = asyncio.create_task(workflow.execute())
        self.active_workflows[workflow_id] = task

        return WorkflowResult(
            success=True,
            status=DeploymentStatus.VALIDATING,
            message=f"Started deployment workflow for {project_name}",
            data={'workflow_id': workflow_id}
        )

    async def get_deployment_status(self, workflow_id: str) -> Optional[DeploymentState]:
        """Get status of a deployment workflow"""
        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]

        # Check if workflow is still running
        if workflow_id in self.active_workflows:
            task = self.active_workflows[workflow_id]
            if not task.done():
                return workflow.get_state()

        # Workflow completed, remove from active
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]

        return workflow.get_state()

    async def abort_deployment(self, workflow_id: str) -> WorkflowResult:
        """Abort a running deployment workflow"""
        if workflow_id not in self.active_workflows:
            return WorkflowResult(
                success=False,
                status=DeploymentStatus.FAILED,
                message=f"No active workflow found with ID: {workflow_id}",
                error="Workflow not found or not running"
            )

        # Cancel the task
        task = self.active_workflows[workflow_id]
        task.cancel()

        # Update workflow state
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow.state.update_status(DeploymentStatus.ABORTED, "Deployment aborted by user")
            workflow.state.error = "Deployment aborted by user"

        del self.active_workflows[workflow_id]

        return WorkflowResult(
            success=True,
            status=DeploymentStatus.ABORTED,
            message=f"Deployment workflow {workflow_id} aborted",
            data={'workflow_id': workflow_id}
        )