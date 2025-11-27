"""
Windows deployment automation system.
"""
import os
import sys
import subprocess
import logging
import tempfile
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json


class WindowsDeploymentManager:
    """Manages Windows deployment automation for MoAI-ADK."""

    def __init__(self, repo_path: str, config: Dict[str, Any]):
        """Initialize Windows deployment manager."""
        self.repo_path = Path(repo_path)
        self.config = config
        self.install_dir = Path(config.get("windows", {}).get("install_dir", r"C:\Program Files\MoAI-ADK"))
        self.logger = self._setup_logger()
        self.backup_points = {}

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for deployment manager."""
        logger = logging.getLogger('WindowsDeploymentManager')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def validate_environment(self) -> Dict[str, Any]:
        """Validate deployment environment requirements."""
        try:
            self.logger.info("Validating deployment environment...")

            performed_checks = []
            issues = []

            # 1. Python version check
            performed_checks.append("python_version")
            python_check = self.check_python_compatibility(
                self.config.get("windows", {}).get("supported_python_versions", ["3.8", "3.9", "3.10", "3.11"])
            )
            if not python_check["is_compatible"]:
                issues.extend(python_check["issues"])

            # 2. Admin rights validation
            performed_checks.append("admin_rights")
            admin_check = self.validate_admin_rights()
            if not admin_check["has_admin_rights"]:
                issues.append("Administrator rights required for installation")

            # 3. Disk space check
            performed_checks.append("disk_space")
            required_space_mb = self.config.get("windows", {}).get("required_disk_space_mb", 1024)
            disk_check = self.check_disk_space(required_space_mb)
            if not disk_check["has_sufficient_space"]:
                issues.append(f"Insufficient disk space: {disk_check['available_space_mb']}MB available, {required_space_mb}MB required")

            # 4. Network connectivity check
            performed_checks.append("network_connectivity")
            network_check = self.check_network_connectivity()
            if not network_check["is_connected"]:
                issues.append("Network connectivity issues detected")

            # 5. Windows version compatibility
            performed_checks.append("windows_version")
            windows_check = self.check_windows_version()
            if not windows_check["is_compatible"]:
                issues.append(f"Windows version not compatible: {windows_check['current_version']}")

            result = {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "performed_checks": performed_checks,
                "check_results": {
                    "python_version": python_check,
                    "admin_rights": admin_check,
                    "disk_space": disk_check,
                    "network_connectivity": network_check,
                    "windows_version": windows_check
                },
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(f"Environment validation completed: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Environment validation failed: {str(e)}")
            return {
                "is_valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "performed_checks": [],
                "timestamp": datetime.now().isoformat()
            }

    def check_python_compatibility(self, required_versions: List[str]) -> Dict[str, Any]:
        """Check Python version compatibility."""
        try:
            # Get current Python version
            result = subprocess.run([sys.executable, "--version"],
                                  capture_output=True, text=True)

            if result.returncode != 0:
                return {
                    "is_compatible": False,
                    "issues": ["Python not found or not accessible"],
                    "current_version": None,
                    "recommended_version": None
                }

            # Extract version (e.g., "Python 3.9.7" -> "3.9")
            version_str = result.stdout.strip().split()[1]
            current_version = version_str.split('.')[0] + '.' + version_str.split('.')[1]

            # Check compatibility
            is_compatible = current_version in required_versions

            return {
                "is_compatible": is_compatible,
                "issues": [] if is_compatible else [f"Python {current_version} not in supported versions: {required_versions}"],
                "current_version": current_version,
                "recommended_version": required_versions[0] if required_versions else None
            }

        except Exception as e:
            return {
                "is_compatible": False,
                "issues": [f"Python version check failed: {str(e)}"],
                "current_version": None,
                "recommended_version": None
            }

    def validate_admin_rights(self) -> Dict[str, Any]:
        """Check if the process has administrator rights."""
        try:
            import ctypes

            # Check admin rights using Windows API
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

            return {
                "has_admin_rights": is_admin,
                "can_install_systemwide": is_admin,
                "system_rights_level": "administrator" if is_admin else "user"
            }

        except Exception as e:
            self.logger.error(f"Admin rights check failed: {str(e)}")
            return {
                "has_admin_rights": False,
                "can_install_systemwide": False,
                "system_rights_level": "unknown",
                "error": str(e)
            }

    def check_disk_space(self, required_space_mb: int) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            import ctypes
            import ctypes.wintypes

            # Get free space on the installation drive
            drive = os.path.splitdrive(self.install_dir)[0] + "\\"
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(drive),
                None, None, ctypes.pointer(free_bytes)
            )

            free_space_mb = free_bytes.value // (1024 * 1024)
            has_sufficient_space = free_space_mb >= required_space_mb

            return {
                "has_sufficient_space": has_sufficient_space,
                "available_space_mb": free_space_mb,
                "required_space_mb": required_space_mb,
                "drive": drive
            }

        except Exception as e:
            self.logger.error(f"Disk space check failed: {str(e)}")
            return {
                "has_sufficient_space": False,
                "available_space_mb": 0,
                "required_space_mb": required_space_mb,
                "error": str(e)
            }

    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity."""
        try:
            # Test basic connectivity to GitHub
            result = subprocess.run(
                ["ping", "-n", "1", "github.com"],
                capture_output=True,
                text=True,
                timeout=10
            )

            is_connected = result.returncode == 0

            return {
                "is_connected": is_connected,
                "latency_ms": self._extract_ping_latency(result.stdout) if is_connected else None,
                "test_url": "github.com"
            }

        except Exception as e:
            return {
                "is_connected": False,
                "error": str(e),
                "test_url": "github.com"
            }

    def _extract_ping_latency(self, ping_output: str) -> Optional[int]:
        """Extract latency from ping output."""
        try:
            # Example: "Average = 15ms"
            lines = ping_output.split('\n')
            for line in lines:
                if 'Average =' in line:
                    avg_part = line.split('Average =')[1].strip()
                    return int(avg_part.replace('ms', '').strip())
            return None
        except:
            return None

    def check_windows_version(self) -> Dict[str, Any]:
        """Check Windows version compatibility."""
        try:
            import platform
            import sys

            # Get Windows version info
            win_version = sys.getwindowsversion()
            version_str = f"{win_version.major}.{win_version.minor}"
            build_number = win_version.build

            # Define compatibility thresholds
            min_version = "10.0"  # Windows 10
            required_build = 10240  # Windows 10 threshold

            is_compatible = (version_str >= min_version and
                           build_number >= required_build)

            return {
                "is_compatible": is_compatible,
                "current_version": version_str,
                "build_number": build_number,
                "required_version": min_version,
                "required_build": required_build,
                "os_name": platform.system()
            }

        except Exception as e:
            return {
                "is_compatible": False,
                "current_version": "unknown",
                "error": str(e)
            }

    def execute_deployment_scripts(self, scripts: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Execute deployment scripts."""
        results = []

        for script in scripts:
            try:
                script_name = script["name"]
                script_type = script["type"]
                purpose = script.get("purpose", "")

                self.logger.info(f"Executing {script_name} ({purpose})...")

                start_time = datetime.now()

                if script_type == "python":
                    result = self._execute_python_script(script_name)
                elif script_type == "batch":
                    result = self._execute_batch_script(script_name)
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown script type: {script_type}"
                    }

                execution_time = (datetime.now() - start_time).total_seconds()

                result.update({
                    "script_name": script_name,
                    "script_type": script_type,
                    "purpose": purpose,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                })

                results.append(result)

                if not result["success"]:
                    self.logger.error(f"Script {script_name} failed: {result.get('error', 'Unknown error')}")
                    break  # Stop execution on failure

            except Exception as e:
                error_result = {
                    "success": False,
                    "error": str(e),
                    "script_name": script.get("name", "unknown"),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(error_result)
                self.logger.error(f"Script execution error: {str(e)}")
                break

        return results

    def _execute_python_script(self, script_name: str) -> Dict[str, Any]:
        """Execute Python script."""
        script_path = self.repo_path / "scripts" / script_name

        if not script_path.exists():
            return {
                "success": False,
                "error": f"Script not found: {script_path}"
            }

        try:
            # Set environment variables
            env = os.environ.copy()
            env.update(self._get_environment_variables())

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "error_output": result.stderr
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "error_code": result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_batch_script(self, script_name: str) -> Dict[str, Any]:
        """Execute batch script."""
        script_path = self.repo_path / "scripts" / script_name

        if not script_path.exists():
            return {
                "success": False,
                "error": f"Script not found: {script_path}"
            }

        try:
            result = subprocess.run(
                ["cmd.exe", "/c", str(script_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "error_output": result.stderr
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "error_code": result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def setup_environment_variables(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Set up environment variables."""
        try:
            set_variables = []
            errors = []

            for var_name, var_value in env_vars.items():
                try:
                    # Handle Windows environment variable expansion
                    if var_value.startswith('%') and var_value.endswith('%'):
                        # Expand existing environment variables
                        expanded_value = os.path.expandvars(var_value)
                    else:
                        expanded_value = var_value

                    # Set the environment variable
                    os.environ[var_name] = expanded_value
                    set_variables.append(var_name)

                    # For permanent setup, also write to the system registry
                    if self.config.get("windows", {}).get("permanent_environment", True):
                        self._set_system_environment_variable(var_name, expanded_value)

                except Exception as e:
                    errors.append({
                        "variable": var_name,
                        "error": str(e)
                    })

            return {
                "success": len(errors) == 0,
                "set_variables": set_variables,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "set_variables": [],
                "errors": [str(e)],
                "timestamp": datetime.now().isoformat()
            }

    def _set_system_environment_variable(self, name: str, value: str) -> None:
        """Set system environment variable through registry (requires admin rights)."""
        try:
            import winreg

            # Open the registry key for system environment variables
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                0,
                winreg.KEY_SET_VALUE
            )

            # Set the environment variable
            winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
            winreg.CloseKey(key)

            # Notify the system about the change
            ctypes.windll.kernel32.SetEnvironmentVariableW(name, value)
            ctypes.windll.user32.SendMessageTimeoutW(
                0xFFFF, 0x001A, 0, None, 0x0002, 5000, None
            )

        except Exception as e:
            self.logger.warning(f"Failed to set system environment variable {name}: {str(e)}")

    def _get_environment_variables(self) -> Dict[str, str]:
        """Get environment variables to set for deployment."""
        env_vars = {}

        if "environment" in self.config.get("windows", {}):
            for key, value in self.config["windows"]["environment"].items():
                if key == "PYTHONPATH" and value == "{install_dir}\\lib":
                    # Replace placeholder with actual install directory
                    env_vars[key] = str(self.install_dir / "lib")
                else:
                    env_vars[key] = value

        # Add Python and script directories to PATH
        paths_to_add = [
            str(self.install_dir / "bin"),
            str(self.install_dir / "scripts")
        ]

        # Update PATH if not already present
        current_path = os.environ.get("PATH", "")
        for path in paths_to_add:
            if path not in current_path:
                env_vars["PATH"] = f"{path};{current_path}"

        return env_vars

    def create_shortcuts(self, shortcuts: List[Dict[str, str]]) -> Dict[str, Any]:
        """Create Windows shortcuts."""
        try:
            created_shortcuts = []
            failed_shortcuts = []

            for shortcut in shortcuts:
                try:
                    shortcut_name = shortcut["name"]
                    target = shortcut["target"]
                    arguments = shortcut.get("arguments", "")
                    working_dir = shortcut.get("working_dir", "")
                    description = shortcut.get("description", "")

                    # Expand environment variables in paths
                    target = os.path.expandvars(target)
                    working_dir = os.path.expandvars(working_dir)

                    shortcut_path = self._create_windows_shortcut(
                        shortcut_name, target, arguments, working_dir, description
                    )

                    if shortcut_path:
                        created_shortcuts.append({
                            "name": shortcut_name,
                            "path": str(shortcut_path)
                        })
                    else:
                        failed_shortcuts.append({
                            "name": shortcut_name,
                            "error": "Failed to create shortcut"
                        })

                except Exception as e:
                    failed_shortcuts.append({
                        "name": shortcut.get("name", "unknown"),
                        "error": str(e)
                    })

            return {
                "success": len(failed_shortcuts) == 0,
                "created_shortcuts": created_shortcuts,
                "failed_shortcuts": failed_shortcuts,
                "total_shortcuts": len(shortcuts),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "created_shortcuts": [],
                "failed_shortcuts": [{"error": str(e)}],
                "timestamp": datetime.now().isoformat()
            }

    def _create_windows_shortcut(self, name: str, target: str, arguments: str,
                                working_dir: str, description: str) -> Optional[Path]:
        """Create Windows shortcut using COM."""
        try:
            import pythoncom
            from win32com.shell import shell, shellcon

            # Initialize COM
            pythoncom.CoInitialize()

            # Create shortcut
            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink,
                None,
                pythoncom.CLSCTX_INPROC_SERVER,
                shell.IID_IShellLink
            )

            # Set shortcut properties
            shortcut.SetPath(target)
            shortcut.SetArguments(arguments)
            shortcut.SetWorkingDirectory(working_dir)
            shortcut.SetDescription(description)

            # Get desktop path
            desktop_path = Path(os.path.expandvars("%USERPROFILE%\\Desktop"))
            shortcut_file = desktop_path / f"{name}.lnk"

            # Save shortcut
            persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            persist_file.Save(str(shortcut_file), 0)

            pythoncom.CoUninitialize()
            return shortcut_file

        except Exception as e:
            self.logger.error(f"Failed to create shortcut {name}: {str(e)}")
            return None

    def validate_deployment(self) -> Dict[str, Any]:
        """Validate deployment after installation."""
        try:
            self.logger.info("Validating deployment...")

            performed_checks = []
            check_results = {}

            # 1. Check executables
            performed_checks.append("check_executables")
            executable_check = self._validate_executables()
            check_results["executables"] = executable_check

            # 2. Check configuration
            performed_checks.append("check_configuration")
            config_check = self._validate_configuration()
            check_results["configuration"] = config_check

            # 3. Check environment setup
            performed_checks.append("check_environment")
            env_check = self._validate_environment()
            check_results["environment"] = env_check

            # 4. Test basic functionality
            performed_checks.append("test_basic_functionality")
            functionality_check = self._test_basic_functionality()
            check_results["functionality"] = functionality_check

            # Overall validation
            all_checks_passed = all(
                check.get("success", False) for check in check_results.values()
            )

            return {
                "is_valid": all_checks_passed,
                "performed_checks": performed_checks,
                "results": check_results,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Deployment validation failed: {str(e)}")
            return {
                "is_valid": False,
                "performed_checks": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _validate_executables(self) -> Dict[str, Any]:
        """Validate that required executables exist."""
        try:
            required_executables = [
                self.install_dir / "bin" / "python.exe",
                self.install_dir / "scripts" / "claude-glm.bat"
            ]

            existing_executables = []
            missing_executables = []

            for executable in required_executables:
                if executable.exists():
                    existing_executables.append(str(executable))
                else:
                    missing_executables.append(str(executable))

            return {
                "success": len(missing_executables) == 0,
                "existing_executables": existing_executables,
                "missing_executables": missing_executables
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration files."""
        try:
            required_configs = [
                self.repo_path / ".moai" / "config" / "config.json",
                self.repo_path / ".env"
            ]

            existing_configs = []
            missing_configs = []

            for config in required_configs:
                if config.exists():
                    existing_configs.append(str(config))
                else:
                    missing_configs.append(str(config))

            return {
                "success": len(missing_configs) == 0,
                "existing_configs": existing_configs,
                "missing_configs": missing_configs
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _validate_environment(self) -> Dict[str, Any]:
        """Validate environment setup."""
        try:
            # Check if environment variables are set
            env_vars_to_check = [
                "GLM_API_KEY",
                "GLM_MODEL",
                "MOAI_CONFIG_PATH"
            ]

            set_vars = []
            missing_vars = []

            for var in env_vars_to_check:
                if var in os.environ:
                    set_vars.append(var)
                else:
                    missing_vars.append(var)

            # Check PATH includes install directory
            current_path = os.environ.get("PATH", "")
            install_path = str(self.install_dir / "bin")
            path_includes_install = install_path in current_path

            return {
                "success": len(missing_vars) == 0 and path_includes_install,
                "set_variables": set_vars,
                "missing_variables": missing_vars,
                "path_includes_install_dir": path_includes_install
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _test_basic_functionality(self) -> Dict[str, Any]:
        """Test basic functionality of installed components."""
        try:
            tests_passed = 0
            tests_failed = 0
            test_results = []

            # Test 1: Python import test
            try:
                result = subprocess.run(
                    [sys.executable, "-c", "import sys; print(sys.version)"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    tests_passed += 1
                    test_results.append({
                        "test": "python_version",
                        "passed": True,
                        "result": result.stdout.strip()
                    })
                else:
                    tests_failed += 1
                    test_results.append({
                        "test": "python_version",
                        "passed": False,
                        "error": result.stderr
                    })
            except Exception as e:
                tests_failed += 1
                test_results.append({
                    "test": "python_version",
                    "passed": False,
                    "error": str(e)
                })

            # Test 2: Configuration access test
            try:
                config_file = self.repo_path / ".moai" / "config" / "config.json"
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        import json
                        config_data = json.load(f)
                        tests_passed += 1
                        test_results.append({
                            "test": "configuration_access",
                            "passed": True,
                            "result": "Configuration file loaded successfully"
                        })
                else:
                    tests_failed += 1
                    test_results.append({
                        "test": "configuration_access",
                        "passed": False,
                        "error": "Configuration file not found"
                    })
            except Exception as e:
                tests_failed += 1
                test_results.append({
                    "test": "configuration_access",
                    "passed": False,
                    "error": str(e)
                })

            return {
                "success": tests_failed == 0,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "total_tests": tests_passed + tests_failed,
                "test_results": test_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_installation_log(self) -> Dict[str, Any]:
        """Generate detailed installation log."""
        try:
            log_file = self.repo_path / "logs" / f"deployment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            # Ensure logs directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("MoAI-ADK Windows Deployment Log\n")
                f.write("=" * 50 + "\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Installation Directory: {self.install_dir}\n")
                f.write(f"Repository Path: {self.repo_path}\n\n")

                # Environment validation
                f.write("Environment Validation:\n")
                f.write("-" * 30 + "\n")
                env_result = self.validate_environment()
                f.write(f"Overall Status: {'PASS' if env_result['is_valid'] else 'FAIL'}\n")
                f.write(f"Issues: {', '.join(env_result['issues']) if env_result['issues'] else 'None'}\n\n")

                # System information
                f.write("System Information:\n")
                f.write("-" * 30 + "\n")
                try:
                    import platform
                    f.write(f"OS: {platform.system()} {platform.version()}\n")
                    f.write(f"Python Version: {platform.python_version()}\n")
                    f.write(f"Architecture: {platform.machine()}\n")
                except Exception as e:
                    f.write(f"Error getting system info: {e}\n")
                f.write("\n")

                # Installed files
                f.write("Installed Files:\n")
                f.write("-" * 30 + "\n")
                try:
                    for root, dirs, files in os.walk(self.install_dir):
                        for file in files:
                            file_path = Path(root) / file
                            rel_path = file_path.relative_to(self.install_dir)
                            f.write(f"{rel_path}\n")
                except Exception as e:
                    f.write(f"Error listing files: {e}\n")
                f.write("\n")

                # Environment variables
                f.write("Environment Variables:\n")
                f.write("-" * 30 + "\n")
                for key, value in os.environ.items():
                    if key.startswith(('GLM_', 'MOAI_', 'PYTHON')):
                        f.write(f"{key}={value}\n")
                f.write("\n")

            return {
                "success": True,
                "log_file_path": str(log_file),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }