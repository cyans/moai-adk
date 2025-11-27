"""
Deployment state management for Windows deployment engine
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


class DeploymentStatus(Enum):
    """Deployment status enumeration"""
    PENDING = "pending"
    VALIDATING = "validating"
    BUILDING = "building"
    TESTING = "testing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    success: bool
    status: DeploymentStatus
    message: str = ""
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentState:
    """State tracking for deployment operations"""
    status: DeploymentStatus = DeploymentStatus.PENDING
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    step_results: Dict[str, DeploymentResult] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    progress: float = 0.0  # Progress percentage (0.0 to 1.0)

    def update_status(self, status: DeploymentStatus, current_step: Optional[str] = None):
        """Update deployment status and current step"""
        self.status = status
        self.current_step = current_step

        # Update timestamps
        if status in [DeploymentStatus.VALIDATING, DeploymentStatus.BUILDING,
                     DeploymentStatus.TESTING, DeploymentStatus.DEPLOYING]:
            if not self.start_time:
                self.start_time = datetime.now()
        elif status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.ABORTED]:
            self.end_time = datetime.now()

    def mark_step_completed(self, step_name: str, result: DeploymentResult):
        """Mark a step as completed"""
        self.completed_steps.append(step_name)
        self.step_results[step_name] = result
        self.update_progress()

    def mark_step_failed(self, step_name: str, result: DeploymentResult):
        """Mark a step as failed"""
        self.failed_steps.append(step_name)
        self.step_results[step_name] = result
        self.status = DeploymentStatus.FAILED
        self.error = result.error
        self.update_progress()

    def update_progress(self):
        """Update progress percentage based on completed steps"""
        # This will be enhanced based on total step count
        if self.completed_steps:
            self.progress = min(1.0, len(self.completed_steps) * 0.25)  # Approximate progress

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            'status': self.status.value,
            'current_step': self.current_step,
            'completed_steps': self.completed_steps,
            'failed_steps': self.failed_steps,
            'step_results': {
                step: {
                    'success': result.success,
                    'status': result.status.value,
                    'message': result.message,
                    'error': result.error,
                    'data': result.data
                }
                for step, result in self.step_results.items()
            },
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error': self.error,
            'progress': self.progress
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeploymentState':
        """Create state from dictionary"""
        state = cls()
        state.status = DeploymentStatus(data.get('status', DeploymentStatus.PENDING.value))
        state.current_step = data.get('current_step')
        state.completed_steps = data.get('completed_steps', [])
        state.failed_steps = data.get('failed_steps', [])
        state.start_time = datetime.fromisoformat(data['start_time']) if data.get('start_time') else None
        state.end_time = datetime.fromisoformat(data['end_time']) if data.get('end_time') else None
        state.error = data.get('error')
        state.progress = data.get('progress', 0.0)

        # Reconstruct step results
        step_results_data = data.get('step_results', {})
        state.step_results = {}
        for step, result_data in step_results_data.items():
            result = DeploymentResult(
                success=result_data['success'],
                status=DeploymentStatus(result_data['status']),
                message=result_data['message'],
                error=result_data['error'],
                data=result_data['data']
            )
            state.step_results[step] = result

        return state