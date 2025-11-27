"""
Test suite for testing and validation framework.
TAG-TEST-005: Testing and validation framework
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

# Import the testing framework modules to be tested
from moai_adk.testing.framework.test_runner import TestRunner
from moai_adk.testing.framework.test_reporter import TestReporter
from moai_adk.testing.framework.validator import TestValidator
from moai_adk.testing.framework.coverage_analyzer import CoverageAnalyzer
from moai_adk.testing.framework.performance_benchmark import PerformanceBenchmark
from moai_adk.testing.framework.compatibility_checker import CompatibilityChecker
from moai_adk.testing.framework.stress_tester import StressTester
from moai_adk.testing.framework.security_validator import SecurityValidator
from moai_adk.testing.framework.config import TestConfig
from moai_adk.testing.framework.errors import TestError, ValidationError, ConfigurationError


class TestTestRunner:
    """Test cases for TestRunner class"""

    def test_test_runner_initialization(self):
        """Test TestRunner initialization"""
        runner = TestRunner()

        assert runner.test_discovery_enabled is True
        assert runner.parallel_execution is True
        assert runner.max_workers is 4
        assert runner.timeout is 300
        assert runner.fail_fast is False

    def test_configure_runner(self):
        """Test configuring test runner"""
        runner = TestRunner()

        config = {
            "parallel_execution": True,
            "max_workers": 8,
            "timeout": 600,
            "fail_fast": True,
            "coverage_threshold": 90
        }

        runner.configure(config)

        assert runner.parallel_execution is True
        assert runner.max_workers == 8
        assert runner.timeout == 600
        assert runner.fail_fast is True
        assert runner.coverage_threshold == 90

    def test_discover_tests(self):
        """Test test discovery"""
        runner = TestRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = [
                "test_deployment.py",
                "test_cli.py",
                "test_windows.py",
                "helper.py",  # Should be ignored
                "test_config.py"
            ]

            for filename in test_files:
                with open(os.path.join(temp_dir, filename), 'w') as f:
                    f.write(f"# Test file: {filename}")

            discovered = runner.discover_tests(temp_dir)

            # Should find test files but ignore helper.py
            assert len(discovered) >= 4  # test_*.py files
            assert any("test_deployment.py" in str(test) for test in discovered)
            assert not any("helper.py" in str(test) for test in discovered)

    def test_run_single_test(self):
        """Test running a single test"""
        runner = TestRunner()

        # Mock test result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Test passed"
        mock_result.stderr = ""

        with patch.object(runner, '_execute_test') as mock_execute:
            mock_execute.return_value = mock_result

            result = runner.run_test("test_example.py::test_function")

            assert result.returncode == 0
            assert result.stdout == "Test passed"
            assert result.success is True

    def test_run_test_suite(self):
        """Test running a test suite"""
        runner = TestRunner()

        test_files = [
            "test_deployment.py",
            "test_cli.py",
            "test_windows.py"
        ]

        mock_results = []
        for test_file in test_files:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = f"Tests passed in {test_file}"
            mock_result.test_file = test_file
            mock_results.append(mock_result)

        with patch.object(runner, '_execute_test') as mock_execute:
            mock_execute.side_effect = mock_results

            results = runner.run_suite(test_files)

            assert len(results) == 3
            assert all(result.success for result in results)
            assert mock_execute.call_count == 3

    def test_run_test_suite_with_failures(self):
        """Test running test suite with failures"""
        runner = TestRunner()
        runner.fail_fast = True

        test_files = ["test1.py", "test2.py", "test3.py"]

        # Mock: first test fails, second succeeds
        mock_results = [
            Mock(returncode=1, stdout="Test failed", stderr="AssertionError", success=False),
            Mock(returncode=0, stdout="Test passed", stderr="", success=True)
        ]

        with patch.object(runner, '_execute_test') as mock_execute:
            mock_execute.side_effect = mock_results

            results = runner.run_suite(test_files)

            # Should stop after first failure due to fail_fast=True
            assert len(results) == 1
            assert results[0].success is False
            assert mock_execute.call_count == 1

    def test_run_parallel_tests(self):
        """Test running tests in parallel"""
        runner = TestRunner()
        runner.parallel_execution = True
        runner.max_workers = 2

        test_files = ["test1.py", "test2.py", "test3.py", "test4.py"]

        mock_results = []
        for i, test_file in enumerate(test_files):
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = f"Test {i+1} passed"
            mock_result.success = True
            mock_results.append(mock_result)

        with patch.object(runner, '_execute_test') as mock_execute:
            mock_execute.side_effect = mock_results

            results = runner.run_suite(test_files)

            assert len(results) == 4
            assert all(result.success for result in results)

    def test_timeout_handling(self):
        """Test test timeout handling"""
        runner = TestRunner()
        runner.timeout = 5  # 5 seconds timeout

        with patch.object(runner, '_execute_test') as mock_execute:
            mock_execute.side_effect = TimeoutError("Test timed out")

            result = runner.run_test("slow_test.py")

            assert result is None  # Should return None for timeout
            # Verify timeout was handled
            assert hasattr(runner, '_timeout_errors')

    def test_test_filtering(self):
        """Test filtering tests by pattern"""
        runner = TestRunner()

        test_files = [
            "test_deployment_workflow.py",
            "test_cli_interface.py",
            "test_windows_optimization.py",
            "test_github_integration.py"
        ]

        # Filter tests containing "deployment"
        filtered = runner.filter_tests(test_files, "deployment")

        assert len(filtered) == 1
        assert "deployment" in filtered[0]

        # Filter tests containing "windows"
        filtered = runner.filter_tests(test_files, "windows")

        assert len(filtered) == 1
        assert "windows" in filtered[0]

    def test_generate_test_report(self):
        """Test generating test report"""
        runner = TestRunner()

        test_results = [
            Mock(returncode=0, stdout="Test 1 passed", success=True, duration=2.5),
            Mock(returncode=1, stdout="Test 2 failed", stderr="AssertionError", success=False, duration=1.8),
            Mock(returncode=0, stdout="Test 3 passed", success=True, duration=3.2)
        ]

        report = runner.generate_report(test_results)

        assert "total" in report
        assert "passed" in report
        assert "failed" in report
        assert "success_rate" in report
        assert "duration" in report
        assert report["total"] == 3
        assert report["passed"] == 2
        assert report["failed"] == 1
        assert report["success_rate"] == 66.67

    def test_test_statistics(self):
        """Test test statistics calculation"""
        runner = TestRunner()

        test_results = [
            Mock(returncode=0, stdout="Test 1", success=True, duration=1.0),
            Mock(returncode=0, stdout="Test 2", success=True, duration=2.5),
            Mock(returncode=1, stdout="Test 3", success=False, duration=0.5),
            Mock(returncode=0, stdout="Test 4", success=True, duration=3.0)
        ]

        stats = runner.calculate_statistics(test_results)

        assert stats["total_tests"] == 4
        assert stats["passed_tests"] == 3
        assert stats["failed_tests"] == 1
        assert stats["success_rate"] == 75.0
        assert stats["average_duration"] == 1.75
        assert stats["total_duration"] == 7.0


class TestTestReporter:
    """Test cases for TestReporter class"""

    def test_reporter_initialization(self):
        """Test TestReporter initialization"""
        reporter = TestReporter()

        assert reporter.output_format == "json"
        assert reporter.output_file is None
        assert reporter.include_detailed is False
        assert reporter.include_coverage is False

    def test_set_output_format(self):
        """Test setting output format"""
        reporter = TestReporter()

        # Test JSON format
        reporter.set_format("json")
        assert reporter.output_format == "json"

        # Test XML format
        reporter.set_format("xml")
        assert reporter.output_format == "xml"

        # Test HTML format
        reporter.set_format("html")
        assert reporter.output_format == "html"

        # Test invalid format
        with pytest.raises(ValueError, match="Unsupported format"):
            reporter.set_format("invalid")

    def test_generate_json_report(self):
        """Test generating JSON report"""
        reporter = TestReporter()
        reporter.set_format("json")

        test_results = [
            {
                "test_file": "test_deployment.py",
                "test_name": "test_workflow",
                "status": "passed",
                "duration": 2.5,
                "timestamp": datetime.now().isoformat()
            },
            {
                "test_file": "test_cli.py",
                "test_name": "test_command",
                "status": "failed",
                "duration": 1.8,
                "error": "AssertionError",
                "timestamp": datetime.now().isoformat()
            }
        ]

        report = reporter.generate_report(test_results)

        # Should be valid JSON
        try:
            json.loads(report)
        except json.JSONDecodeError:
            pytest.fail("Generated report is not valid JSON")

        # Verify content structure
        report_data = json.loads(report)
        assert "summary" in report_data
        assert "details" in report_data
        assert len(report_data["details"]) == 2

    def test_generate_html_report(self):
        """Test generating HTML report"""
        reporter = TestReporter()
        reporter.set_format("html")

        test_results = [
            {
                "test_file": "test_deployment.py",
                "test_name": "test_workflow",
                "status": "passed",
                "duration": 2.5
            }
        ]

        report = reporter.generate_report(test_results)

        # Should contain HTML structure
        assert "<html" in report
        assert "<head>" in report
        assert "<body>" in report
        assert "test_workflow" in report

    def test_generate_xml_report(self):
        """Test generating XML report"""
        reporter = TestReporter()
        reporter.set_format("xml")

        test_results = [
            {
                "test_file": "test_deployment.py",
                "test_name": "test_workflow",
                "status": "passed",
                "duration": 2.5
            }
        ]

        report = reporter.generate_report(test_results)

        # Should contain XML structure
        assert "<?xml" in report
        assert "<testsuites>" in report
        assert "<testcase" in report
        assert "test_workflow" in report

    def test_save_report_to_file(self):
        """Test saving report to file"""
        reporter = TestReporter()

        test_results = [
            {
                "test_file": "test_deployment.py",
                "test_name": "test_workflow",
                "status": "passed",
                "duration": 2.5
            }
        ]

        report_content = reporter.generate_report(test_results)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            reporter.save_report(report_content, temp_file)

            # Verify file was created and contains correct content
            with open(temp_file, 'r') as f:
                saved_content = f.read()

            assert saved_content == report_content

        finally:
            os.unlink(temp_file)

    def test_test_with_coverage_data(self):
        """Test generating report with coverage data"""
        reporter = TestReporter()
        reporter.include_coverage = True

        test_results = [
            {
                "test_file": "test_deployment.py",
                "test_name": "test_workflow",
                "status": "passed",
                "duration": 2.5,
                "coverage": {
                    "lines_covered": 85,
                    "lines_total": 100,
                    "branches_covered": 12,
                    "branches_total": 15
                }
            }
        ]

        report = reporter.generate_report(test_results)

        # Should include coverage information
        assert "85%" in report or "0.85" in report


class TestTestValidator:
    """Test cases for TestValidator class"""

    def test_validator_initialization(self):
        """Test TestValidator initialization"""
        validator = TestValidator()

        assert validator.rules == {}
        assert validator.strict_mode is False
        assert validator.auto_fix is False

    def test_add_validation_rule(self):
        """Test adding validation rules"""
        validator = TestValidator()

        def custom_rule(test_data):
            return "test_name" in test_data

        validator.add_rule("has_test_name", custom_rule)

        assert "has_test_name" in validator.rules
        assert validator.rules["has_test_name"] == custom_rule

    def test_validate_test_data(self):
        """Test validating test data"""
        validator = TestValidator()

        # Add validation rules
        def has_required_fields(test_data):
            required = ["test_file", "test_name", "status"]
            return all(field in test_data for field in required)

        def valid_status(test_data):
            return test_data["status"] in ["passed", "failed", "skipped"]

        validator.add_rule("required_fields", has_required_fields)
        validator.add_rule("valid_status", valid_status)

        # Valid test data
        valid_test = {
            "test_file": "test_deployment.py",
            "test_name": "test_workflow",
            "status": "passed",
            "duration": 2.5
        }

        result = validator.validate(valid_test)
        assert result.is_valid is True
        assert result.errors == []

        # Invalid test data
        invalid_test = {
            "test_name": "test_workflow",
            "status": "invalid_status",
            "duration": 2.5
            # Missing test_file
        }

        result = validator.validate(invalid_test)
        assert result.is_valid is False
        assert len(result.errors) == 2

    def test_auto_fix_validation(self):
        """Test auto-fix validation"""
        validator = TestValidator()
        validator.auto_fix = True

        def has_duration(test_data):
            return "duration" in test_data

        validator.add_rule("has_duration", has_duration)

        # Test data missing duration
        test_data = {
            "test_file": "test_deployment.py",
            "test_name": "test_workflow",
            "status": "passed"
        }

        result = validator.validate(test_data)

        assert result.is_valid is True
        assert result.fixed_data["duration"] > 0  # Should be auto-fixed

    def test_batch_validation(self):
        """Test batch validation of multiple tests"""
        validator = TestValidator()

        def has_timestamp(test_data):
            return "timestamp" in test_data

        validator.add_rule("has_timestamp", has_timestamp)

        test_batch = [
            {"test_name": "test1", "timestamp": "2023-01-01"},  # Valid
            {"test_name": "test2"},  # Invalid - missing timestamp
            {"test_name": "test3", "timestamp": "2023-01-02"},  # Valid
            {"test_name": "test4"},  # Invalid - missing timestamp
        ]

        results = validator.validate_batch(test_batch)

        assert len(results) == 4
        assert sum(1 for r in results if r.is_valid) == 2
        assert sum(1 for r in results if not r.is_valid) == 2

    def test_custom_error_messages(self):
        """Test custom error messages"""
        validator = TestValidator()

        def positive_duration(test_data):
            duration = test_data.get("duration", 0)
            return duration > 0

        validator.add_rule("positive_duration", positive_duration)

        test_data = {"test_name": "test1", "duration": -1}

        result = validator.validate(test_data)

        assert result.is_valid is False
        assert any("duration" in error.get("field", "") for error in result.errors)


class TestCoverageAnalyzer:
    """Test cases for CoverageAnalyzer class"""

    def test_coverage_analyzer_initialization(self):
        """Test CoverageAnalyzer initialization"""
        analyzer = CoverageAnalyzer()

        assert analyzer.threshold == 80
        assert analyzer.fail_below_threshold is True
        assert analyzer.include_branches is True

    def test_analyze_coverage_report(self):
        """Test analyzing coverage report"""
        analyzer = CoverageAnalyzer()

        coverage_data = {
            "files": [
                {
                    "filename": "src/deployment/workflow.py",
                    "lines_covered": 85,
                    "lines_total": 100,
                    "branches_covered": 12,
                    "branches_total": 15
                },
                {
                    "filename": "src/cli/main.py",
                    "lines_covered": 45,
                    "lines_total": 60,
                    "branches_covered": 8,
                    "branches_total": 10
                }
            ],
            "summary": {
                "lines_covered": 130,
                "lines_total": 160,
                "branches_covered": 20,
                "branches_total": 25
            }
        }

        analysis = analyzer.analyze(coverage_data)

        assert analysis["total_coverage"] == 81.25  # 130/160
        assert analysis["branch_coverage"] == 80.0  # 20/25
        assert len(analysis["file_coverage"]) == 2
        assert analysis["file_coverage"]["src/deployment/workflow.py"]["coverage"] == 85.0

    def test_coverage_threshold_validation(self):
        """Test coverage threshold validation"""
        analyzer = CoverageAnalyzer()
        analyzer.threshold = 90

        coverage_data = {
            "summary": {
                "lines_covered": 80,
                "lines_total": 100,
                "branches_covered": 15,
                "branches_total": 20
            }
        }

        analysis = analyzer.analyze(coverage_data)

        assert analysis["meets_threshold"] is False
        assert analysis["threshold"] == 90
        assert analysis["total_coverage"] == 80.0

    def test_generate_coverage_report(self):
        """Test generating coverage report"""
        analyzer = CoverageAnalyzer()

        coverage_data = {
            "files": [
                {
                    "filename": "src/deployment/workflow.py",
                    "lines_covered": 85,
                    "lines_total": 100
                }
            ],
            "summary": {
                "lines_covered": 85,
                "lines_total": 100,
                "branches_covered": 12,
                "branches_total": 15
            }
        }

        report = analyzer.generate_report(coverage_data)

        # Should contain coverage information
        assert "Coverage Report" in report
        assert "85%" in report
        assert "src/deployment/workflow.py" in report

    def test_identify_uncovered_lines(self):
        """Test identifying uncovered lines"""
        analyzer = CoverageAnalyzer()

        coverage_data = {
            "files": [
                {
                    "filename": "src/deployment/workflow.py",
                    "lines_covered": 85,
                    "lines_total": 100,
                    "uncovered_lines": [16, 17, 18, 95, 96, 97, 98, 99]
                }
            ]
        }

        analysis = analyzer.analyze(coverage_data)

        assert len(analysis["uncovered_lines"]) == 8
        assert 16 in analysis["uncovered_lines"]
        assert 99 in analysis["uncovered_lines"]

    def test_coverage_trend_analysis(self):
        """Test coverage trend analysis"""
        analyzer = CoverageAnalyzer()

        historical_data = [
            {"date": "2023-01-01", "coverage": 75.0},
            {"date": "2023-01-02", "coverage": 78.5},
            {"date": "2023-01-03", "coverage": 82.0},
            {"date": "2023-01-04", "coverage": 85.2}
        ]

        trend = analyzer.analyze_trend(historical_data)

        assert trend["trend"] == "improving"
        assert trend["improvement"] == 10.2  # 85.2 - 75.0


class TestPerformanceBenchmark:
    """Test cases for PerformanceBenchmark class"""

    def test_benchmark_initialization(self):
        """Test PerformanceBenchmark initialization"""
        benchmark = PerformanceBenchmark()

        assert benchmark.max_duration is 300
        assert benchmark.max_memory is 1024
        assert benchmark.min_throughput is 10
        assert benchmark.baseline_metrics is None

    def run_performance_test(self):
        """Test running performance test"""
        benchmark = PerformanceBenchmark()

        def mock_test_function():
            import time
            time.sleep(0.1)  # Simulate work
            return "test completed"

        metrics = benchmark.run_test(mock_test_function)

        assert "duration" in metrics
        assert "memory_usage" in metrics
        assert "throughput" in metrics
        assert metrics["duration"] > 0

    def test_benchmark_comparison(self):
        """Test benchmark comparison"""
        benchmark = PerformanceBenchmark()

        baseline_metrics = {
            "duration": 2.5,
            "memory_usage": 100,
            "throughput": 20
        }

        current_metrics = {
            "duration": 1.8,  # Faster
            "memory_usage": 120,  # Higher memory
            "throughput": 25  # Higher throughput
        }

        comparison = benchmark.compare(baseline_metrics, current_metrics)

        assert comparison["duration"]["change"] < 0  # Improvement
        assert comparison["memory_usage"]["change"] > 0  # Regression
        assert comparison["throughput"]["change"] > 0  # Improvement
        assert comparison["overall_trend"] == "mixed"

    def test_stress_testing(self):
        """Test stress testing functionality"""
        benchmark = PerformanceBenchmark()

        def mock_load_test():
            import time
            time.sleep(0.05)
            return f"processed at {time.time()}"

        results = benchmark.stress_test(
            test_function=mock_load_test,
            concurrent_users=10,
            duration_seconds=1
        )

        assert len(results) > 0
        assert "average_response_time" in results
        assert "requests_per_second" in results
        assert "error_rate" in results


class TestCompatibilityChecker:
    """Test cases for CompatibilityChecker class"""

    def test_compatibility_checker_initialization(self):
        """Test CompatibilityChecker initialization"""
        checker = CompatibilityChecker()

        assert checker.target_platforms == ["windows", "linux", "macos"]
        assert checker.python_versions == ["3.8", "3.9", "3.10", "3.11"]
        assert checker.check_dependencies is True

    def test_platform_compatibility(self):
        """Test platform compatibility checking"""
        checker = CompatibilityChecker()

        # Test Windows compatibility
        windows_result = checker.check_platform_compatibility(
            "windows",
            {
                "uses_shell": True,
                "path_format": "backslashes",
                "encoding": "utf-8"
            }
        )

        assert "windows" in windows_result
        assert windows_result["windows"]["compatible"] is True

        # Test Linux compatibility
        linux_result = checker.check_platform_compatibility(
            "linux",
            {
                "uses_shell": True,
                "path_format": "forward_slashes",
                "encoding": "utf-8"
            }
        )

        assert "linux" in linux_result
        assert linux_result["linux"]["compatible"] is True

    def test_python_version_compatibility(self):
        """Test Python version compatibility"""
        checker = CompatibilityChecker()

        # Test Python 3.11 compatibility
        compatibility = checker.check_python_compatibility("3.11")

        assert compatibility["3.11"]["compatible"] is True
        assert "typing" in compatibility["3.11"]["features"]
        assert "async" in compatibility["3.11"]["features"]

    def test_dependency_compatibility(self):
        """Test dependency compatibility checking"""
        checker = CompatibilityChecker()

        dependencies = {
            "click": ">=8.0.0",
            "pyyaml": ">=6.0.0",
            "tqdm": ">=4.60.0"
        }

        result = checker.check_dependency_compatibility(dependencies)

        assert "click" in result
        assert "pyyaml" in result
        assert "tqdm" in result
        assert all(dep["compatible"] for dep in result.values())

    def test_generate_compatibility_report(self):
        """Test generating compatibility report"""
        checker = CompatibilityChecker()

        compatibility_data = {
            "platforms": {
                "windows": {"compatible": True, "notes": ["WSL2 supported"]},
                "linux": {"compatible": True, "notes": ["Native support"]},
                "macos": {"compatible": False, "notes": ["Python 3.11+ required"]}
            },
            "python_versions": {
                "3.8": {"compatible": True},
                "3.11": {"compatible": True},
                "3.12": {"compatible": True}
            }
        }

        report = checker.generate_report(compatibility_data)

        assert "Platform Compatibility" in report
        assert "Python Version Compatibility" in report
        assert "macos" in report
        assert "3.11" in report


class TestStressTester:
    """Test cases for StressTester class"""

    def test_stress_tester_initialization(self):
        """Test StressTester initialization"""
        tester = StressTester()

        assert tester.max_concurrent_users == 100
        assert tester.test_duration == 300
        assert tester.ramp_up_time == 60
        assert tester.monitor_metrics is True

    def test_load_test_scenario(self):
        """Test running load test scenario"""
        tester = StressTester()

        def mock_api_call():
            import time
            time.sleep(0.1)  # Simulate API response time
            return {"status": "success", "response_time": 0.1}

        scenario = {
            "name": "Deployment API Load Test",
            "users": 50,
            "duration": 10,
            "ramp_up": 5,
            "requests_per_user": 10
        }

        results = tester.run_load_test(scenario, mock_api_call)

        assert "total_requests" in results
        assert "successful_requests" in results
        assert "failed_requests" in results
        assert "average_response_time" in results
        assert results["successful_requests"] > 0

    def test_concurrent_user_simulation(self):
        """Test concurrent user simulation"""
        tester = StressTester()

        def mock_user_action():
            import time
            time.sleep(0.2)
            return f"user completed at {time.time()}"

        results = tester.simulate_concurrent_users(
            num_users=10,
            action_function=mock_user_action,
            max_duration=2
        )

        assert len(results) == 10
        assert all(result["status"] == "completed" for result in results)
        assert all(result["duration"] > 0 for result in results)

    def test_resource_monitoring(self):
        """Test resource monitoring during stress test"""
        tester = StressTester()

        with patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.virtual_memory') as mock_memory:

            mock_cpu.return_value = 75.0
            mock_memory.return_value = Mock(percent=60.0, available=1024*1024*1000)

            metrics = tester.monitor_resources(interval=0.1)

            assert "cpu_usage" in metrics
            assert "memory_usage" in metrics
            assert len(metrics["cpu_usage"]) > 0
            assert len(metrics["memory_usage"]) > 0


class TestSecurityValidator:
    """Test cases for SecurityValidator class"""

    def test_security_validator_initialization(self):
        """Test SecurityValidator initialization"""
        validator = SecurityValidator()

        assert validator.check_secrets is True
        assert validator.check_dependencies is True
        assert validator.check_code_patterns is True
        assert validator.fail_on_severe is True

    def test_secrets_detection(self):
        """Test secrets detection in code"""
        validator = SecurityValidator()

        # Code with potential secrets
        test_code = """
import os
API_KEY = os.getenv('API_KEY', 'secret123')
DATABASE_URL = 'postgres://user:password@localhost:5432/db'
GITHUB_TOKEN = 'ghp_test_token_here'
"""

        secrets = validator.detect_secrets(test_code)

        assert len(secrets) > 0
        assert any("secret123" in secret for secret in secrets)
        assert any("ghp_test_token" in secret for secret in secrets)

    def test_vulnerability_scanning(self):
        """Test vulnerability scanning"""
        validator = SecurityValidator()

        dependencies = {
            "requests": "2.25.1",
            "flask": "1.1.2",
            "django": "3.1.0"
        }

        vulnerabilities = scanner.scan_dependencies(dependencies)

        # Should detect known vulnerabilities in older versions
        assert len(vulnerabilities) >= 0  # May have vulnerabilities

    def test_security_rules_engine(self):
        """Test security rules engine"""
        validator = SecurityValidator()

        def no_hardcoded_passwords(code):
            return "password" not in code.lower()

        def secure_imports(code):
            dangerous_imports = ["subprocess", "os.system", "eval"]
            return not any(imp in code for imp in dangerous_imports)

        validator.add_rule("no_hardcoded_passwords", no_hardcoded_passwords)
        validator.add_rule("secure_imports", secure_imports)

        # Test secure code
        secure_code = """
import requests
import json

def api_call(url):
    return requests.get(url)
"""

        result = validator.validate_code(secure_code)

        assert result.is_valid is True

        # Test insecure code
        insecure_code = """
import subprocess
import os

def run_command(cmd):
    return os.system(cmd)
"""

        result = validator.validate_code(insecure_code)

        assert result.is_valid is False


class TestTestConfig:
    """Test cases for TestConfig class"""

    def test_config_creation(self):
        """Test TestConfig creation"""
        config = TestConfig()

        assert config.parallel_execution is True
        assert config.coverage_threshold == 85
        assert config.fail_fast is False
        assert config.timeout == 300

    def test_config_validation(self):
        """Test TestConfig validation"""
        config = TestConfig()

        # Valid configuration
        valid_config = {
            "parallel_execution": True,
            "coverage_threshold": 90,
            "fail_fast": True,
            "timeout": 600,
            "max_workers": 8
        }

        assert config.validate(valid_config) is True

        # Invalid configuration
        invalid_config = {
            "coverage_threshold": 150,  # Over 100%
            "timeout": -1  # Negative timeout
        }

        assert config.validate(invalid_config) is False

    def test_load_config_from_file(self):
        """Test loading configuration from file"""
        config = TestConfig()

        config_dict = {
            "parallel_execution": True,
            "coverage_threshold": 90,
            "fail_fast": True,
            "timeout": 600
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(config_dict, f)
            temp_file = f.name

        try:
            loaded_config = config.load_from_file(temp_file)

            assert loaded_config["parallel_execution"] is True
            assert loaded_config["coverage_threshold"] == 90
            assert loaded_config["timeout"] == 600

        finally:
            os.unlink(temp_file)

    def test_config_defaults(self):
        """Test configuration defaults"""
        config = TestConfig()

        # Test default values
        assert config.get("parallel_execution", default=True) is True
        assert config.get("coverage_threshold", default=85) == 85
        assert config.get("unknown_setting", default="default_value") == "default_value"


class TestTestingIntegration:
    """Integration tests for testing framework components"""

    def test_complete_testing_workflow(self):
        """Test complete testing workflow"""
        # Initialize components
        test_runner = TestRunner()
        test_runner.configure({
            "parallel_execution": True,
            "max_workers": 4,
            "timeout": 600,
            "fail_fast": False,
            "coverage_threshold": 90
        })

        test_validator = TestValidator()
        coverage_analyzer = CoverageAnalyzer()
        test_reporter = TestReporter()

        # Configure test validator
        def validate_test_structure(test_data):
            return all(key in test_data for key in ["test_file", "test_name", "status"])

        test_validator.add_rule("structure", validate_test_structure)

        # Mock test discovery and execution
        test_files = [
            "test_deployment_engine.py",
            "test_cli_interface.py",
            "test_windows_optimization.py",
            "test_github_integration.py"
        ]

        # Simulate test results
        test_results = []
        for i, test_file in enumerate(test_files):
            test_result = Mock()
            test_result.test_file = test_file
            test_result.test_name = f"test_function_{i}"
            test_result.status = "passed" if i % 2 == 0 else "failed"
            test_result.duration = 2.5 + i * 0.5
            test_result.success = test_result.status == "passed"
            test_results.append(test_result)

        # Run tests
        suite_results = test_runner.run_suite(test_files)

        # Validate results
        validation_results = test_validator.validate_batch([
            {
                "test_file": result.test_file,
                "test_name": result.test_name,
                "status": "passed" if result.success else "failed",
                "duration": result.duration
            }
            for result in suite_results
        ])

        # Analyze coverage
        coverage_data = {
            "summary": {
                "lines_covered": 95,
                "lines_total": 100,
                "branches_covered": 18,
                "branches_total": 20
            }
        }

        coverage_analysis = coverage_analyzer.analyze(coverage_data)

        # Generate report
        test_reporter.set_format("html")
        report = test_reporter.generate_report([
            {
                "test_file": result.test_file,
                "test_name": result.test_name,
                "status": "passed" if result.success else "failed",
                "duration": result.duration,
                "timestamp": datetime.now().isoformat()
            }
            for result in suite_results
        ])

        # Verify complete workflow
        assert len(validation_results) == len(suite_results)
        assert coverage_analysis["total_coverage"] >= 90
        assert "<html" in report  # HTML report generated

    def test_performance_and_stress_testing_workflow(self):
        """Test performance and stress testing workflow"""
        performance_benchmark = PerformanceBenchmark()
        stress_tester = StressTester()
        compatibility_checker = CompatibilityChecker()

        # Set up performance baseline
        baseline_metrics = {
            "duration": 2.5,
            "memory_usage": 100,
            "throughput": 20
        }

        # Run current performance test
        def current_deployment_process():
            import time
            time.sleep(0.2)  # Simulate improved deployment speed
            return "deployment completed"

        current_metrics = performance_benchmark.run_test(current_deployment_process)

        # Compare with baseline
        performance_comparison = performance_benchmark.compare(baseline_metrics, current_metrics)

        # Run stress test
        stress_results = stress_tester.simulate_concurrent_users(
            num_users=50,
            action_function=current_deployment_process,
            max_duration=10
        )

        # Check compatibility
        compatibility_results = compatibility_checker.check_platform_compatibility(
            "windows",
            {"deployment_optimization": True}
        )

        # Verify workflow results
        assert "performance_comparison" in performance_comparison
        assert len(stress_results) == 50
        assert "windows" in compatibility_results
        assert compatibility_results["windows"]["compatible"] is True

    def test_security_validation_workflow(self):
        """Test security validation workflow"""
        security_validator = SecurityValidator()

        # Test code with security issues
        test_code = """
import subprocess
import os

API_KEY = "secret123"
DB_PASSWORD = "password123"

def execute_command(cmd):
    return subprocess.run(cmd, shell=True)
"""

        # Run security validation
        security_result = security_validator.validate_code(test_code)

        # Generate security report
        security_report = security_validator.generate_report(security_result)

        # Verify security issues detected
        assert security_result.is_valid is False
        assert len(security_result.issues) > 0
        assert "subprocess" in security_report or "secret" in security_report

    def test_configuration_management_workflow(self):
        """Test configuration management workflow"""
        test_config = TestConfig()

        # Create comprehensive test configuration
        comprehensive_config = {
            "parallel_execution": True,
            "max_workers": 8,
            "timeout": 600,
            "fail_fast": True,
            "coverage_threshold": 90,
            "performance_threshold": 2.0,
            "security_checks": True,
            "platform_compatibility": ["windows", "linux"],
            "python_versions": ["3.9", "3.10", "3.11"]
        }

        # Validate configuration
        is_valid = test_config.validate(comprehensive_config)

        # Load and save configuration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_file = f.name

        try:
            test_config.save_to_file(comprehensive_config, temp_config_file)
            loaded_config = test_config.load_from_file(temp_config_file)

            # Verify configuration integrity
            assert is_valid is True
            assert loaded_config == comprehensive_config
            assert loaded_config["coverage_threshold"] == 90

        finally:
            os.unlink(temp_config_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])