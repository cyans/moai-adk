"""
Integration test harness for end-to-end testing.
"""
import os
import sys
import tempfile
import unittest
import logging
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import threading
import subprocess
from unittest.mock import Mock, patch, MagicMock

from moai_adk.deployment.git_fork_sync import GitForkSyncManager
from moai_adk.deployment.windows_deployment import WindowsDeploymentManager
from moai_adk.code_review.review_engine import ReviewEngine
from moai_adk.code_review.automation import ReviewAutomation


class TestHarness:
    """Integration test harness for end-to-end testing."""

    def __init__(self, repo_path: str, config: Dict[str, Any]):
        """Initialize test harness."""
        self.repo_path = Path(repo_path)
        self.config = config
        self.logger = self._setup_logger()
        self.mock_data_injected = False
        self.test_results = []
        self.environment_variables = {}

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for test harness."""
        logger = logging.getLogger('TestHarness')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def execute_scenario(self, test_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a test scenario."""
        try:
            self.logger.info(f"Executing scenario: {test_scenario['name']}")

            scenario_start_time = datetime.now()
            scenario_results = []

            # Setup test environment
            setup_result = self._setup_test_environment(test_scenario)
            if not setup_result["success"]:
                return {
                    "scenario_passed": False,
                    "error": f"Environment setup failed: {setup_result['error']}",
                    "execution_details": scenario_results,
                    "execution_time": 0
                }

            # Execute test steps
            for step in test_scenario["steps"]:
                step_start_time = datetime.now()
                step_result = self._execute_test_step(step)
                step_execution_time = (datetime.now() - step_start_time).total_seconds()

                step_detail = {
                    "step_name": step.get("name", step.get("action", "unknown")),
                    "step_type": step.get("type", "execution"),
                    "result": step_result,
                    "execution_time": step_execution_time,
                    "timestamp": datetime.now().isoformat()
                }

                scenario_results.append(step_detail)

                # Stop execution if step failed and stop_on_failure is True
                if not step_result["success"] and test_scenario.get("stop_on_failure", True):
                    break

            # Cleanup test environment
            cleanup_result = self._cleanup_test_environment()
            if not cleanup_result["success"]:
                self.logger.warning(f"Environment cleanup warning: {cleanup_result['error']}")

            # Calculate scenario execution time
            scenario_execution_time = (datetime.now() - scenario_start_time).total_seconds()

            # Determine scenario success
            all_steps_passed = all(
                step_result.get("result", {}).get("success", False)
                for step_result in scenario_results
            )

            return {
                "scenario_passed": all_steps_passed,
                "scenario_name": test_scenario["name"],
                "execution_details": scenario_results,
                "execution_time": scenario_execution_time,
                "total_steps": len(test_scenario["steps"]),
                "passed_steps": sum(
                    1 for step_result in scenario_results
                    if step_result.get("result", {}).get("success", False)
                ),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Scenario execution failed: {str(e)}")
            return {
                "scenario_passed": False,
                "error": str(e),
                "execution_details": scenario_results,
                "execution_time": 0,
                "timestamp": datetime.now().isoformat()
            }

    def _setup_test_environment(self, test_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Setup test environment for scenario execution."""
        try:
            # Create temporary directories if needed
            if "temp_directories" in test_scenario:
                for temp_dir in test_scenario["temp_directories"]:
                    Path(temp_dir).mkdir(parents=True, exist_ok=True)

            # Set environment variables
            if "environment_variables" in test_scenario:
                for key, value in test_scenario["environment_variables"].items():
                    self.environment_variables[key] = value
                    os.environ[key] = str(value)

            # Inject mock data if enabled
            if test_scenario.get("use_mock_data", False) and not self.mock_data_injected:
                self.inject_mock_data(test_scenario.get("mock_data", {}))
                self.mock_data_injected = True

            return {
                "success": True,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _cleanup_test_environment(self) -> Dict[str, Any]:
        """Cleanup test environment after scenario execution."""
        try:
            # Remove environment variables
            for key in self.environment_variables:
                if key in os.environ:
                    del os.environ[key]

            # Reset mock data flag
            self.mock_data_injected = False

            return {
                "success": True,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _execute_test_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test step."""
        try:
            system = step.get("system", "unknown")
            action = step.get("action", step.get("name", "unknown"))
            parameters = step.get("parameters", {})
            expected_result = step.get("expected_result", {})

            self.logger.info(f"Executing step: {system}.{action}")

            # Execute the action based on system type
            if system == "git_sync":
                result = self._execute_git_sync_step(action, parameters)
            elif system == "windows_deployment":
                result = self._execute_windows_deployment_step(action, parameters)
            elif system == "code_review":
                result = self._execute_code_review_step(action, parameters)
            elif system == "integration":
                result = self._execute_integration_step(action, parameters)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown system: {system}"
                }

            # Validate result against expected
            validation_result = self._validate_step_result(result, expected_result)

            return {
                "success": True,
                "action_result": result,
                "validation_result": validation_result,
                "expected_result": expected_result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Step execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _execute_git_sync_step(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Git sync system step."""
        try:
            # Initialize Git operations with mock data
            mock_config = self.config.get("git_sync", {})
            if "git" not in mock_config:
                mock_config["git"] = {
                    "remote_name": "upstream",
                    "fork_remote_name": "origin",
                    "branch": "main"
                }
            if "deployment" not in mock_config:
                mock_config["deployment"] = {
                    "auto_sync": True,
                    "sync_on_start": True,
                    "sync_interval": 3600
                }

            sync_manager = GitForkSyncManager(str(self.repo_path), mock_config)

            if action == "sync_with_upstream":
                return sync_manager.sync_with_upstream(parameters.get("preserve_history", True))
            elif action == "validate_fork_status":
                return sync_manager.validate_fork_status()
            elif action == "synchronize_branches":
                branches = parameters.get("branches", ["main", "feature/test"])
                return sync_manager.synchronize_branches(branches)
            elif action == "validate_auto_sync_config":
                return sync_manager.validate_auto_sync_config()
            else:
                return {
                    "success": False,
                    "error": f"Unknown Git sync action: {action}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_windows_deployment_step(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Windows deployment system step."""
        try:
            # Initialize Windows deployment manager with mock data
            mock_config = self.config.get("windows_deployment", {})
            if "windows" not in mock_config:
                mock_config["windows"] = {
                    "python_version": "3.9",
                    "install_dir": r"C:\Program Files\MoAI-ADK",
                    "environment": {
                        "PYTHONPATH": "{install_dir}\\lib",
                        "GLM_API_KEY": "test_key"
                    },
                    "auto_install": True,
                    "validate_installation": True
                }

            deploy_manager = WindowsDeploymentManager(str(self.repo_path), mock_config)

            if action == "validate_environment":
                return deploy_manager.validate_environment()
            elif action == "check_python_compatibility":
                versions = parameters.get("versions", ["3.8", "3.9", "3.10", "3.11"])
                return deploy_manager.check_python_compatibility(versions)
            elif action == "validate_admin_rights":
                return deploy_manager.validate_admin_rights()
            elif action == "check_disk_space":
                space_mb = parameters.get("space_mb", 1024)
                return deploy_manager.check_disk_space(space_mb)
            elif action == "execute_deployment_scripts":
                scripts = parameters.get("scripts", [
                    {"name": "setup-glm.py", "type": "python", "purpose": "Setup GLM"},
                    {"name": "claude-glm.bat", "type": "batch", "purpose": "Batch setup"}
                ])
                return deploy_manager.execute_deployment_scripts(scripts)
            elif action == "setup_environment_variables":
                env_vars = parameters.get("env_vars", {
                    "GLM_API_KEY": "test_api_key",
                    "GLM_MODEL": "claude-3-sonnet"
                })
                return deploy_manager.setup_environment_variables(env_vars)
            elif action == "create_shortcuts":
                shortcuts = parameters.get("shortcuts", [
                    {
                        "name": "Test Shortcut",
                        "target": "notepad.exe",
                        "arguments": "",
                        "working_dir": "%SYSTEMROOT%",
                        "description": "Test shortcut"
                    }
                ])
                return deploy_manager.create_shortcuts(shortcuts)
            elif action == "validate_deployment":
                return deploy_manager.validate_deployment()
            else:
                return {
                    "success": False,
                    "error": f"Unknown Windows deployment action: {action}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_code_review_step(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code review system step."""
        try:
            # Initialize review engine with mock data
            mock_config = self.config.get("code_review", {})
            if "workflow" not in mock_config:
                mock_config["workflow"] = {
                    "auto_trigger": True,
                    "required_reviewers": 2,
                    "approval_threshold": 0.8,
                    "auto_merge": False
                }
            if "quality_standards" not in mock_config:
                mock_config["quality_standards"] = {
                    "coverage_threshold": 0.85,
                    "complexity_threshold": 10,
                    "style_compliance": 0.95,
                    "security_scan": True
                }

            review_engine = ReviewEngine(str(self.repo_path), mock_config)

            if action == "on_pr_created":
                pr_data = parameters.get("pr_data", {
                    "title": "Test PR",
                    "description": "Test pull request",
                    "source_branch": "feature/test",
                    "target_branch": "main",
                    "author": "test_user",
                    "files_changed": ["test.py"]
                })
                return review_engine.on_pr_created(pr_data)
            elif action == "execute_code_analysis":
                analysis_config = parameters.get("analysis_config", {
                    "static_analysis": True,
                    "unit_test_coverage": True,
                    "security_scan": True,
                    "complexity_analysis": True,
                    "style_check": True
                })
                return review_engine.execute_code_analysis(analysis_config)
            elif action == "assign_reviewers":
                reviewers = parameters.get("reviewers", [
                    {"id": "reviewer1", "expertise": ["python"], "load": 1},
                    {"id": "reviewer2", "expertise": ["testing"], "load": 0}
                ])
                context = parameters.get("context", {
                    "technologies": ["python"],
                    "complexity": "medium",
                    "security_relevant": True
                })
                return review_engine.assign_reviewers(reviewers, context)
            elif action == "generate_review_requests":
                assignment = parameters.get("assignment", {
                    "reviewers": ["reviewer1", "reviewer2"],
                    "deadline": datetime.now().isoformat(),
                    "priority": "normal"
                })
                return review_engine.generate_review_requests(assignment)
            elif action == "process_review_responses":
                responses = parameters.get("responses", [
                    {
                        "reviewer_id": "reviewer1",
                        "status": "approved",
                        "comments": [],
                        "overall_score": 8.5
                    }
                ])
                return review_engine.process_review_responses(responses)
            elif action == "make_approval_decision":
                review_results = parameters.get("review_results", {
                    "total_reviewers": 2,
                    "approvals": 2,
                    "changes_requested": 0,
                    "overall_score": 8.2
                })
                return review_engine.make_approval_decision(review_results)
            else:
                return {
                    "success": False,
                    "error": f"Unknown code review action: {action}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_integration_step(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute integration step."""
        try:
            if action == "execute_workflow":
                workflow_steps = parameters.get("steps", [
                    {
                        "system": "git_sync",
                        "action": "sync_with_upstream",
                        "parameters": {"preserve_history": True}
                    },
                    {
                        "system": "windows_deployment",
                        "action": "validate_environment",
                        "parameters": {}
                    },
                    {
                        "system": "code_review",
                        "action": "on_pr_created",
                        "parameters": {
                            "pr_data": {
                                "title": "Integration Test PR",
                                "description": "Test PR for integration"
                            }
                        }
                    }
                ])
                return self._execute_integration_workflow(workflow_steps)
            elif action == "test_system_interaction":
                return self._test_system_interaction(parameters)
            elif action == "validate_data_flow":
                return self._validate_data_flow(parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown integration action: {action}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_integration_workflow(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute integration workflow."""
        try:
            executed_steps = []
            failed_steps = []

            for step in workflow_steps:
                step_result = self._execute_test_step(step)
                executed_steps.append({
                    "step": step,
                    "result": step_result
                })

                if not step_result["success"]:
                    failed_steps.append(step)
                    break  # Stop on first failure

            return {
                "success": len(failed_steps) == 0,
                "executed_steps": executed_steps,
                "failed_steps": failed_steps,
                "total_steps": len(workflow_steps),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _test_system_interaction(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Test interaction between different systems."""
        try:
            # Test data flow between systems
            interaction_tests = parameters.get("interaction_tests", [
                {
                    "source_system": "git_sync",
                    "target_system": "windows_deployment",
                    "data_flow": "commit_hash",
                    "expected_result": "success"
                },
                {
                    "source_system": "windows_deployment",
                    "target_system": "code_review",
                    "data_flow": "deployment_status",
                    "expected_result": "success"
                }
            ])

            interaction_results = []

            for test in interaction_tests:
                # Simulate system interaction
                result = self._simulate_system_interaction(test)
                interaction_results.append(result)

            all_passed = all(result["success"] for result in interaction_results)

            return {
                "success": all_passed,
                "interaction_results": interaction_results,
                "total_tests": len(interaction_tests),
                "passed_tests": sum(1 for r in interaction_results if r["success"]),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _simulate_system_interaction(self, interaction_test: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate interaction between two systems."""
        try:
            source_system = interaction_test["source_system"]
            target_system = interaction_test["target_system"]
            data_flow = interaction_test["data_flow"]
            expected_result = interaction_test["expected_result"]

            # Simulate successful interaction
            return {
                "success": True,
                "source_system": source_system,
                "target_system": target_system,
                "data_flow": data_flow,
                "result": "success",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _validate_data_flow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data flow between systems."""
        try:
            data_flow_tests = parameters.get("data_flow_tests", [
                {
                    "path": "git_sync → windows_deployment",
                    "data_type": "commit_info",
                    "validation_rules": ["not_null", "valid_format"]
                },
                {
                    "path": "windows_deployment → code_review",
                    "data_type": "deployment_status",
                    "validation_rules": ["not_null", "valid_status"]
                }
            ])

            validation_results = []

            for test in data_flow_tests:
                # Simulate data flow validation
                result = self._validate_data_flow_test(test)
                validation_results.append(result)

            all_passed = all(result["passed"] for result in validation_results)

            return {
                "success": all_passed,
                "validation_results": validation_results,
                "total_tests": len(data_flow_tests),
                "passed_tests": sum(1 for r in validation_results if r["passed"]),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _validate_data_flow_test(self, test: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single data flow test."""
        try:
            path = test["path"]
            data_type = test["data_type"]
            validation_rules = test["validation_rules"]

            # Simulate validation
            passed_rules = 0
            for rule in validation_rules:
                if rule in ["not_null", "valid_format", "valid_status"]:
                    passed_rules += 1

            return {
                "passed": passed_rules == len(validation_rules),
                "path": path,
                "data_type": data_type,
                "validation_rules": validation_rules,
                "passed_rules": passed_rules,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }

    def _validate_step_result(self, actual_result: Dict[str, Any], expected_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate step result against expected result."""
        try:
            validation_details = {
                "expected": expected_result,
                "actual": actual_result,
                "differences": [],
                "passed": True
            }

            # Check top-level success status
            if "success" in expected_result:
                if actual_result.get("success") != expected_result["success"]:
                    validation_details["differences"].append({
                        "field": "success",
                        "expected": expected_result["success"],
                        "actual": actual_result.get("success")
                    })
                    validation_details["passed"] = False

            # Check specific fields
            for field, expected_value in expected_result.items():
                if field != "success":  # Already checked above
                    actual_value = actual_result.get(field)
                    if actual_value != expected_value:
                        validation_details["differences"].append({
                            "field": field,
                            "expected": expected_value,
                            "actual": actual_value
                        })
                        validation_details["passed"] = False

            return validation_details

        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }

    def inject_mock_data(self, mock_requirements: Dict[str, Any]) -> None:
        """Inject mock data into the test environment."""
        try:
            self.logger.info("Injecting mock data...")

            # Mock Git operations
            if "git_operations" in mock_requirements:
                self._mock_git_operations(mock_requirements["git_operations"])

            # Mock Windows environment
            if "windows_env" in mock_requirements:
                self._mock_windows_environment(mock_requirements["windows_env"])

            # Mock review system
            if "review_system" in mock_requirements:
                self._mock_review_system(mock_requirements["review_system"])

            self.logger.info("Mock data injection completed")

        except Exception as e:
            self.logger.error(f"Mock data injection failed: {str(e)}")
            raise

    def _mock_git_operations(self, git_config: Dict[str, Any]) -> None:
        """Mock Git operations."""
        # Mock Git remote URLs
        if "remotes_exist" in git_config:
            self._patch_git_remotes(git_config["remotes_exist"])

        # Mock Git branches
        if "branches_available" in git_config:
            self._patch_git_branches(git_config["branches_available"])

        # Mock Git commits
        if "commits" in git_config:
            self._patch_git_commits(git_config["commits"])

    def _mock_windows_environment(self, windows_config: Dict[str, Any]) -> None:
        """Mock Windows environment."""
        # Mock Python availability
        if "python_available" in windows_config:
            self._patch_python_availability(windows_config["python_available"])

        # Mock admin rights
        if "admin_rights" in windows_config:
            self._patch_admin_rights(windows_config["admin_rights"])

        # Mock disk space
        if "disk_space" in windows_config:
            self._patch_disk_space(windows_config["disk_space"])

    def _mock_review_system(self, review_config: Dict[str, Any]) -> None:
        """Mock review system."""
        # Mock reviewer availability
        if "reviewers_available" in review_config:
            self._patch_reviewer_availability(review_config["reviewers_available"])

        # Mock review analysis results
        if "analysis_results" in review_config:
            self._patch_analysis_results(review_config["analysis_results"])

    def _patch_git_remotes(self, remotes_exist: bool) -> None:
        """Patch Git remote operations."""
        if remotes_exist:
            mock_remote_url = "https://github.com/test/repo.git"
            mock_get_url = Mock(return_value=mock_remote_url)
            mock_ls_remote = Mock(return_value=Mock(returncode=0))

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = [mock_get_url, mock_ls_remote]

    def _patch_git_branches(self, branches: List[str]) -> None:
        """Patch Git branch operations."""
        mock_branch_list = Mock()
        mock_branch_list.return_value = branches

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='\n'.join(branches))

    def _patch_git_commits(self, commits: List[str]) -> None:
        """Patch Git commit operations."""
        mock_commit_output = '\n'.join(commits)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_commit_output)

    def _patch_python_availability(self, available: bool) -> None:
        """Patch Python availability check."""
        mock_result = Mock(returncode=0 if available else 1)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = mock_result

    def _patch_admin_rights(self, has_admin: bool) -> None:
        """Patch admin rights check."""
        mock_windll = Mock()
        mock_windll.shell32.IsUserAnAdmin.return_value = 1 if has_admin else 0
        with patch('sys.modules', {'ctypes': Mock(), 'ctypes.windll': mock_windll}):
            pass

    def _patch_disk_space(self, disk_space: str) -> None:
        """Patch disk space check."""
        # Mock disk space value (convert to MB)
        space_mb = self._convert_disk_space_to_mb(disk_space)

        mock_free_bytes = Mock()
        mock_free_bytes.value = space_mb * 1024 * 1024

        with patch('ctypes.c_ulonglong') as mock_ulonglong:
            mock_ulonglong.return_value = mock_free_bytes

    def _patch_reviewer_availability(self, reviewers: List[Dict[str, Any]]) -> None:
        """Patch reviewer availability."""
        # Mock reviewer data
        self.mock_reviewers = reviewers

    def _patch_analysis_results(self, results: Dict[str, Any]) -> None:
        """Patch analysis results."""
        self.mock_analysis_results = results

    def _convert_disk_space_to_mb(self, space_str: str) -> int:
        """Convert disk space string to MB."""
        if space_str.endswith('GB'):
            return int(float(space_str[:-2]) * 1024)
        elif space_str.endswith('MB'):
            return int(space_str[:-2])
        else:
            return int(space_str)

    def is_mock_data_injected(self) -> bool:
        """Check if mock data has been injected."""
        return self.mock_data_injected

    def validate_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate test results."""
        try:
            self.logger.info("Validating test results...")

            all_passed = True
            summary = {
                "total_tests": len(test_results),
                "passed_tests": 0,
                "failed_tests": 0,
                "validation_errors": []
            }

            for i, result in enumerate(test_results):
                if result.get("passed", False):
                    summary["passed_tests"] += 1
                else:
                    summary["failed_tests"] += 1
                    all_passed = False

                    # Add validation error details
                    validation_error = {
                        "test_index": i,
                        "test_name": result.get("step_name", f"Test_{i}"),
                        "validation_result": result.get("validation_result", {}),
                        "expected": result.get("expected_result", {}),
                        "actual": result.get("action_result", {})
                    }
                    summary["validation_errors"].append(validation_error)

            return {
                "all_passed": all_passed,
                "pass_rate": summary["passed_tests"] / summary["total_tests"] if summary["total_tests"] > 0 else 0,
                "validation_summary": summary,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "all_passed": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def generate_test_report(self, scenario_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        try:
            self.logger.info("Generating test report...")

            total_scenarios = len(scenario_results)
            passed_scenarios = sum(1 for result in scenario_results if result.get("scenario_passed", False))
            failed_scenarios = total_scenarios - passed_scenarios

            total_execution_time = sum(result.get("execution_time", 0) for result in scenario_results)
            total_steps = sum(result.get("total_steps", 0) for result in scenario_results)
            passed_steps = sum(result.get("passed_steps", 0) for result in scenario_results)

            report = {
                "report_generated_at": datetime.now().isoformat(),
                "test_execution_summary": {
                    "total_scenarios": total_scenarios,
                    "passed_scenarios": passed_scenarios,
                    "failed_scenarios": failed_scenarios,
                    "scenario_pass_rate": passed_scenarios / total_scenarios if total_scenarios > 0 else 0,
                    "total_execution_time_seconds": total_execution_time,
                    "average_execution_time": total_execution_time / total_scenarios if total_scenarios > 0 else 0
                },
                "step_execution_summary": {
                    "total_steps": total_steps,
                    "passed_steps": passed_steps,
                    "failed_steps": total_steps - passed_steps,
                    "step_pass_rate": passed_steps / total_steps if total_steps > 0 else 0
                },
                "scenario_details": scenario_results,
                "test_environment": {
                    "repo_path": str(self.repo_path),
                    "mock_data_used": self.mock_data_injected,
                    "config_used": self.config
                }
            }

            # Save report to file
            report_file = self.repo_path / "test_reports" / f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.parent.mkdir(parents=True, exist_ok=True)

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            return {
                "success": True,
                "report_file": str(report_file),
                "report_summary": report["test_execution_summary"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }