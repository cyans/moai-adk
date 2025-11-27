"""
Deployment engine for orchestrating deployment workflows.
"""
import os
import subprocess
import logging
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json

from moai_adk.deployment.git_fork_sync import GitForkSyncManager
from moai_adk.deployment.windows_deployment import WindowsDeploymentManager


class DeploymentEngine:
    """Main deployment engine that orchestrates the entire deployment process."""

    def __init__(self, repo_path: str, config: Dict[str, Any]):
        """Initialize deployment engine."""
        self.repo_path = Path(repo_path)
        self.config = config
        self.logger = self._setup_logger()
        self.deployment_managers = {}
        self.rollback_points = {}

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for deployment engine."""
        logger = logging.getLogger('DeploymentEngine')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def generate_deployment_plan(self, deployment_plan: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate detailed deployment plan with dependencies."""
        try:
            self.logger.info("Generating deployment plan...")

            execution_order = []
            rollback_plan = []

            # Extract phases and determine execution order
            if "pre_deployment" in deployment_plan:
                execution_order.extend(deployment_plan["pre_deployment"])
                rollback_plan.insert(0, "pre_deployment")

            if "main_deployment" in deployment_plan:
                execution_order.extend(deployment_plan["main_deployment"])
                rollback_plan.insert(0, "main_deployment")

            if "post_deployment" in deployment_plan:
                execution_order.extend(deployment_plan["post_deployment"])
                rollback_plan.insert(0, "post_deployment")

            # Create deployment plan
            plan = {
                "success": True,
                "execution_order": execution_order,
                "rollback_plan": rollback_plan,
                "estimated_duration": self._estimate_deployment_duration(execution_order),
                "required_resources": self._analyze_required_resources(),
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(f"Deployment plan generated: {plan}")
            return plan

        except Exception as e:
            self.logger.error(f"Failed to generate deployment plan: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _estimate_deployment_duration(self, execution_order: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate deployment duration based on execution order."""
        try:
            base_durations = {
                "validate_environment": 30,  # seconds
                "create_backup": 60,
                "install_dependencies": 300,
                "configure_environment": 120,
                "setup_scripts": 60,
                "validate_installation": 90,
                "create_shortcuts": 30,
                "register_services": 120
            }

            total_duration = 0
            step_estimates = []

            for step in execution_order:
                step_name = step.get("action", step.get("name", "unknown"))
                duration = base_durations.get(step_name, 60)  # Default 60 seconds
                total_duration += duration

                step_estimates.append({
                    "step": step_name,
                    "estimated_duration": duration
                })

            return {
                "total_seconds": total_duration,
                "total_minutes": round(total_duration / 60, 1),
                "step_estimates": step_estimates
            }

        except Exception as e:
            return {
                "total_seconds": 0,
                "total_minutes": 0,
                "error": str(e)
            }

    def _analyze_required_resources(self) -> Dict[str, Any]:
        """Analyze required resources for deployment."""
        try:
            resources = {
                "disk_space_mb": 2048,  # 2GB
                "memory_mb": 512,
                "cpu_cores": 2,
                "network_bandwidth": "standard",
                "admin_rights": True
            }

            # Adjust based on configuration
            if "windows" in self.config:
                windows_config = self.config["windows"]
                if "required_disk_space" in windows_config:
                    resources["disk_space_mb"] = windows_config["required_disk_space"]

            return resources

        except Exception as e:
            return {
                "error": str(e)
            }

    def execute_deployment(self) -> Dict[str, Any]:
        """Execute the complete deployment process."""
        try:
            self.logger.info("Starting deployment process...")

            # Track execution
            execution_summary = {
                "started_at": datetime.now().isoformat(),
                "steps_completed": [],
                "steps_failed": [],
                "rollback_executed": False,
                "final_status": "in_progress"
            }

            # Initialize deployment managers
            self._initialize_deployment_managers()

            # Create backup point
            backup_result = self._create_deployment_backup()
            if not backup_result["success"]:
                raise Exception(f"Failed to create backup: {backup_result['error']}")

            self.rollback_points["pre_deployment"] = backup_result["backup_id"]

            try:
                # Execute pre-deployment steps
                pre_deployment_steps = self.config.get("deployment_plan", {}).get("pre_deployment", [])

                for step in pre_deployment_steps:
                    step_result = self._execute_deployment_step(step)
                    execution_summary["steps_completed"].append({
                        "step": step,
                        "result": step_result
                    })

                    if not step_result["success"]:
                        execution_summary["steps_failed"].append(step)
                        raise Exception(f"Pre-deployment step failed: {step}")

                # Execute main deployment steps
                main_deployment_steps = self.config.get("deployment_plan", {}).get("main_deployment", [])

                for step in main_deployment_steps:
                    step_result = self._execute_deployment_step(step)
                    execution_summary["steps_completed"].append({
                        "step": step,
                        "result": step_result
                    })

                    if not step_result["success"]:
                        execution_summary["steps_failed"].append(step)
                        raise Exception(f"Main deployment step failed: {step}")

                # Execute post-deployment steps
                post_deployment_steps = self.config.get("deployment_plan", {}).get("post_deployment", [])

                for step in post_deployment_steps:
                    step_result = self._execute_deployment_step(step)
                    execution_summary["steps_completed"].append({
                        "step": step,
                        "result": step_result
                    })

                    if not step_result["success"]:
                        execution_summary["steps_failed"].append(step)
                        raise Exception(f"Post-deployment step failed: {step}")

                # Deployment completed successfully
                execution_summary["final_status"] = "completed"
                self.logger.info("Deployment completed successfully")

                # Cleanup backup
                self._cleanup_deployment_backup(self.rollback_points["pre_deployment"])

                return {
                    "success": True,
                    "execution_summary": execution_summary,
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                self.logger.error(f"Deployment failed: {str(e)}")
                execution_summary["final_status"] = "failed"

                # Execute rollback if enabled
                if self.config.get("rollback_on_failure", True):
                    rollback_result = self.execute_rollback()
                    execution_summary["rollback_executed"] = rollback_result["success"]
                    execution_summary["rollback_result"] = rollback_result

                return {
                    "success": False,
                    "error": str(e),
                    "execution_summary": execution_summary,
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            self.logger.error(f"Deployment execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _initialize_deployment_managers(self) -> None:
        """Initialize deployment managers for different systems."""
        try:
            # Initialize Windows deployment manager
            if "windows" in self.config:
                self.deployment_managers["windows"] = WindowsDeploymentManager(
                    str(self.repo_path),
                    self.config
                )

            # Initialize Git sync manager
            if "git_sync" in self.config:
                self.deployment_managers["git_sync"] = GitForkSyncManager(
                    str(self.repo_path),
                    self.config
                )

        except Exception as e:
            self.logger.error(f"Failed to initialize deployment managers: {str(e)}")
            raise

    def _execute_deployment_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single deployment step."""
        try:
            system = step["system"]
            action = step["action"]
            parameters = step.get("parameters", {})

            self.logger.info(f"Executing {system}.{action} with parameters: {parameters}")

            if system not in self.deployment_managers:
                return {
                    "success": False,
                    "error": f"Unknown system: {system}"
                }

            manager = self.deployment_managers[system]

            # Execute the action dynamically
            if hasattr(manager, action):
                method = getattr(manager, action)
                result = method(**parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action} for system: {system}"
                }

            return result

        except Exception as e:
            self.logger.error(f"Failed to execute step {step}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_deployment_backup(self) -> Dict[str, Any]:
        """Create backup before deployment."""
        try:
            backup_dir = self.repo_path / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"pre_deployment_{timestamp}"

            # Create backup
            shutil.copytree(self.repo_path, backup_path, ignore=shutil.ignore_patterns(
                "__pycache__", "*.pyc", ".git", "node_modules", "venv", "env"
            ))

            return {
                "success": True,
                "backup_id": f"pre_deployment_{timestamp}",
                "backup_path": str(backup_path),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _cleanup_deployment_backup(self, backup_id: str) -> Dict[str, Any]:
        """Clean up deployment backup."""
        try:
            backup_dir = self.repo_path / "backups"
            backup_path = backup_dir / backup_id

            if backup_path.exists():
                shutil.rmtree(backup_path)

            return {
                "success": True,
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat()
            }

    def execute_rollback(self) -> Dict[str, Any]:
        """Execute rollback to previous backup."""
        try:
            self.logger.info("Executing rollback...")

            if not self.rollback_points:
                return {
                    "success": False,
                    "error": "No rollback points available"
                }

            # Get the latest rollback point
            rollback_point = max(self.rollback_points.keys())
            backup_id = self.rollback_points[rollback_point]

            backup_dir = self.repo_path / "backups" / backup_id
            if not backup_dir.exists():
                return {
                    "success": False,
                    "error": f"Backup not found: {backup_id}"
                }

            # Restore from backup
            if self.repo_path.exists():
                shutil.rmtree(self.repo_path)

            shutil.copytree(backup_dir, self.repo_path)

            return {
                "success": True,
                "rollback_point": rollback_point,
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deployment configuration."""
        try:
            validation_results = {
                "is_valid": True,
                "validation_summary": {},
                "errors": []
            }

            # Validate Windows configuration
            if "windows" in config:
                windows_config = config["windows"]
                windows_validation = self._validate_windows_config(windows_config)
                validation_results["validation_summary"]["windows"] = windows_validation

                if not windows_validation["is_valid"]:
                    validation_results["is_valid"] = False
                    validation_results["errors"].extend(windows_validation["errors"])

            # Validate Git sync configuration
            if "git_sync" in config:
                git_config = config["git_sync"]
                git_validation = self._validate_git_config(git_config)
                validation_results["validation_summary"]["git_sync"] = git_validation

                if not git_validation["is_valid"]:
                    validation_results["is_valid"] = False
                    validation_results["errors"].extend(git_validation["errors"])

            # Validate workflow configuration
            if "workflow" in config:
                workflow_config = config["workflow"]
                workflow_validation = self._validate_workflow_config(workflow_config)
                validation_results["validation_summary"]["workflow"] = workflow_validation

                if not workflow_validation["is_valid"]:
                    validation_results["is_valid"] = False
                    validation_results["errors"].extend(workflow_validation["errors"])

            validation_results["timestamp"] = datetime.now().isoformat()
            return validation_results

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [str(e)],
                "timestamp": datetime.now().isoformat()
            }

    def _validate_windows_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Windows-specific configuration."""
        try:
            errors = []

            # Check required fields
            required_fields = ["install_dir", "python_version"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")

            # Validate install directory
            if "install_dir" in config:
                install_dir = Path(config["install_dir"])
                if not install_dir.is_absolute():
                    errors.append("Install directory must be absolute path")

            # Validate Python version format
            if "python_version" in config:
                python_version = config["python_version"]
                if not isinstance(python_version, str) or not python_version.replace('.', '').isdigit():
                    errors.append("Python version must be in format X.Y")

            return {
                "is_valid": len(errors) == 0,
                "errors": errors
            }

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [str(e)]
            }

    def _validate_git_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Git sync configuration."""
        try:
            errors = []

            # Check required fields
            required_fields = ["remote_name", "fork_remote_name", "branch"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")

            return {
                "is_valid": len(errors) == 0,
                "errors": errors
            }

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [str(e)]
            }

    def _validate_workflow_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow configuration."""
        try:
            errors = []

            # Check required fields
            if "order" not in config:
                errors.append("Missing required field: order")
            else:
                if not isinstance(config["order"], list):
                    errors.append("Order must be a list")
                else:
                    # Check if all systems in order are configured
                    configured_systems = list(self.config.keys())
                    for system in config["order"]:
                        if system not in configured_systems:
                            errors.append(f"System in order not configured: {system}")

            # Check failure handling
            if "failure_handling" in config:
                valid_handling = ["rollback", "continue", "stop"]
                if config["failure_handling"] not in valid_handling:
                    errors.append(f"Invalid failure handling. Must be one of: {valid_handling}")

            return {
                "is_valid": len(errors) == 0,
                "errors": errors
            }

        except Exception as e:
            return {
                "is_valid": False,
                "errors": [str(e)]
            }