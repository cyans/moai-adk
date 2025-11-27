"""
Test suite for Windows optimization layer.
TAG-WIN-003: Windows optimization layer
"""

import pytest
import os
import platform
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the Windows optimization modules to be tested
from moai_adk.platform.windows.path_handler import WindowsPathHandler
from moai_adk.platform.windows.encoding_handler import WindowsEncodingHandler
from moai_adk.platform.windows.wsl_handler import WSLHandler
from moai_adk.platform.windows.command_handler import WindowsCommandHandler
from moai_adk.platform.windows.performance_optimizer import WindowsPerformanceOptimizer
from moai_adk.platform.windows.security_manager import WindowsSecurityManager
from moai_adk.platform.windows.registry_handler import WindowsRegistryHandler
from moai_adk.platform.windows.utils import WindowsUtils
from moai_adk.platform.windows.errors import WindowsError, WSLError, CommandError


class TestWindowsPathHandler:
    """Test cases for WindowsPathHandler class"""

    def test_path_handler_initialization(self):
        """Test WindowsPathHandler initialization"""
        handler = WindowsPathHandler()

        assert handler.is_windows is True
        assert handler.path_separator == "\\"
        assert handler.drive_separator == ":"

    def test_normalize_windows_path(self):
        """Test Windows path normalization"""
        handler = WindowsPathHandler()

        # Test various Windows path formats
        test_cases = [
            ("C:\\Users\\test", "C:\\Users\\test"),
            ("C:/Users/test", "C:\\Users\\test"),
            ("C:\\Users\\test\\", "C:\\Users\\test"),
            ("C:\\Users\\.\\test", "C:\\Users\\test"),
            ("C:\\Users\\..\\test", "C:\\test"),
        ]

        for input_path, expected in test_cases:
            result = handler.normalize_path(input_path)
            assert result == expected

    def test_convert_to_forward_slashes(self):
        """Test converting Windows paths to forward slashes"""
        handler = WindowsPathHandler()

        result = handler.convert_to_forward_slashes("C:\\Users\\test\\file.txt")
        expected = "C:/Users/test/file.txt"

        assert result == expected

    def test_convert_to_back_slashes(self):
        """Test converting forward slashes to Windows backslashes"""
        handler = WindowsPathHandler()

        result = handler.convert_to_back_slashes("C:/Users/test/file.txt")
        expected = "C:\\Users\\test\\file.txt"

        assert result == expected

    def test_join_paths(self):
        """Test joining Windows paths"""
        handler = WindowsPathHandler()

        result = handler.join_paths("C:\\Users", "test", "file.txt")
        expected = "C:\\Users\\test\\file.txt"

        assert result == expected

    def test_validate_windows_path(self):
        """Test Windows path validation"""
        handler = WindowsPathHandler()

        # Valid paths
        assert handler.validate_path("C:\\Users\\test") is True
        assert handler.validate_path("D:\\data\\file.txt") is True
        assert handler.validate_path(r"\\network\share") is True

        # Invalid paths
        assert handler.validate_path("/invalid/path") is False
        assert handler.validate_path("C:InvalidPath") is False
        assert handler.validate_path("") is False

    def test_get_absolute_path(self):
        """Test getting absolute path"""
        handler = WindowsPathHandler()

        with patch('os.path.abspath') as mock_abspath:
            mock_abspath.return_value = "C:\\Users\\test\\absolute"

            result = handler.get_absolute_path("relative\\path")
            expected = "C:\\Users\\test\\absolute"

            assert result == expected
            mock_abspath.assert_called_once_with("relative\\path")

    def test_expand_environment_variables(self):
        """Test expanding environment variables in paths"""
        handler = WindowsPathHandler()

        with patch('os.path.expandvars') as mock_expandvars:
            mock_expandvars.return_value = "C:\\Users\\username\\documents"

            result = handler.expand_environment_variables("%USERPROFILE%\\documents")
            expected = "C:\\Users\\username\\documents"

            assert result == expected
            mock_expandvars.assert_called_once_with("%USERPROFILE%\\documents")

    def test_get_path_permissions(self):
        """Test getting path permissions"""
        handler = WindowsPathHandler()

        with patch('os.access') as mock_access:
            mock_access.side_effect = [True, False, True]  # read, write, execute

            assert handler.has_read_permission("C:\\test") is True
            assert handler.has_write_permission("C:\\test") is False
            assert handler.has_execute_permission("C:\\test") is True

            assert mock_access.call_count == 3

    def test_handle_long_paths(self):
        """Test handling Windows long paths"""
        handler = WindowsPathHandler()

        # Test long path prefix addition
        long_path = "C:\\very\\long\\path\\that\\exceeds\\260\\characters\\..."
        result = handler.handle_long_path(long_path)

        assert result.startswith("\\\\?\\")
        assert "C:" in result

    @patch('platform.system')
    def test_cross_platform_compatibility(self, mock_system):
        """Test cross-platform path handling"""
        mock_system.return_value = 'Windows'
        handler = WindowsPathHandler()

        # Test path conversion for Windows
        assert handler.normalize_path("/unix/path") == "C:\\unix\\path"

        mock_system.return_value = 'Linux'
        unix_handler = WindowsPathHandler()

        # Should handle non-Windows systems gracefully
        assert unix_handler.is_windows is False


class TestWindowsEncodingHandler:
    """Test cases for WindowsEncodingHandler class"""

    def test_encoding_handler_initialization(self):
        """Test WindowsEncodingHandler initialization"""
        handler = WindowsEncodingHandler()

        assert handler.default_encoding == 'utf-8'
        assert handler.fallback_encoding == 'cp949'  # Korean Windows encoding

    def test_detect_encoding(self):
        """Test encoding detection"""
        handler = WindowsEncodingHandler()

        # Test UTF-8 detection
        utf8_text = "한국어 테스트".encode('utf-8')
        detected = handler.detect_encoding(utf8_text)
        assert detected == 'utf-8'

        # Test CP949 detection
        cp949_text = "한국어 테스트".encode('cp949')
        detected = handler.detect_encoding(cp949_text)
        assert detected == 'cp949'

    def test_convert_encoding(self):
        """Test encoding conversion"""
        handler = WindowsEncodingHandler()

        # Test UTF-8 to CP949 conversion
        text = "한국어 테스트"
        utf8_bytes = text.encode('utf-8')
        converted = handler.convert_encoding(utf8_bytes, 'utf-8', 'cp949')

        assert isinstance(converted, bytes)
        # Convert back to string to verify
        converted_text = converted.decode('cp949')
        assert converted_text == text

    def test_handle_korean_text(self):
        """Test handling Korean text"""
        handler = WindowsEncodingHandler()

        korean_text = "한국어 테스트 파일명"

        # Test different encodings
        encodings = ['utf-8', 'cp949', 'euc-kr']

        for encoding in encodings:
            encoded = handler.encode_text(korean_text, encoding)
            decoded = handler.decode_text(encoded, encoding)
            assert decoded == korean_text

    def test_normalize_line_endings(self):
        """Test normalizing line endings for Windows"""
        handler = WindowsEncodingHandler()

        # Test Unix to Windows line ending conversion
        unix_text = "Line1\nLine2\nLine3"
        normalized = handler.normalize_line_endings(unix_text)

        assert normalized == "Line1\r\nLine2\r\nLine3"

        # Test Windows line endings (should remain unchanged)
        windows_text = "Line1\r\nLine2\r\nLine3"
        normalized = handler.normalize_line_endings(windows_text)

        assert normalized == windows_text

    def test_preserve_bom(self):
        """Test handling BOM (Byte Order Mark)"""
        handler = WindowsEncodingHandler()

        # Test UTF-8 with BOM
        text_with_bom = "한국어 테스트".encode('utf-8-sig')
        result = handler.preserve_bom(text_with_bom)

        assert result.startswith(b'\xef\xbb\xbf')

        # Test removing BOM
        cleaned = handler.remove_bom(text_with_bom)
        assert not cleaned.startswith(b'\xef\xbb\xbf')

    def test_file_encoding_validation(self):
        """Test file encoding validation"""
        handler = WindowsEncodingHandler()

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write("테스트 파일")
            temp_path = f.name

        try:
            # Test valid UTF-8 file
            assert handler.validate_file_encoding(temp_path, 'utf-8') is True

            # Test invalid encoding
            assert handler.validate_file_encoding(temp_path, 'ascii') is False

        finally:
            os.unlink(temp_path)

    @patch('locale.getpreferredencoding')
    def test_automatic_encoding_detection(self, mock_locale):
        """Test automatic encoding detection based on system"""
        handler = WindowsEncodingHandler()

        # Test Korean Windows
        mock_locale.return_value = 'cp949'
        handler.detect_system_encoding()
        assert handler.system_encoding == 'cp949'

        # Test English Windows
        mock_locale.return_value = 'utf-8'
        handler.detect_system_encoding()
        assert handler.system_encoding == 'utf-8'

    def test_encoding_error_recovery(self):
        """Test encoding error recovery mechanisms"""
        handler = WindowsEncodingHandler()

        # Test with corrupted encoding
        corrupted_bytes = b'\xff\xfe\xfd'  # Invalid UTF-8 sequence

        # Should fallback to system encoding
        recovered = handler.recover_from_encoding_error(corrupted_bytes)
        assert isinstance(recovered, str)


class TestWSLHandler:
    """Test cases for WSLHandler class"""

    def test_wsl_handler_initialization(self):
        """Test WSLHandler initialization"""
        handler = WSLHandler()

        assert handler.wsl_available is False  # Initially not detected
        assert handler.default_distribution == 'Ubuntu'
        assert handler.use_wsl_by_default is False

    def test_detect_wsl(self):
        """Test WSL detection"""
        handler = WSLHandler()

        with patch('subprocess.run') as mock_run:
            # WSL available
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Ubuntu 20.04 LTS"

            detected = handler.detect_wsl()
            assert detected is True

            # WSL not available
            mock_run.return_value.returncode = 1
            detected = handler.detect_wsl()
            assert detected is False

    def test_convert_windows_to_wsl_path(self):
        """Test Windows to WSL path conversion"""
        handler = WSLHandler()
        handler.wsl_available = True

        test_cases = [
            ("C:\\Users\\test", "/mnt/c/Users/test"),
            ("D:\\data\\file.txt", "/mnt/d/data/file.txt"),
            ("C:\\Program Files", "/mnt/c/Program Files"),
        ]

        for windows_path, expected_wsl_path in test_cases:
            result = handler.windows_to_wsl_path(windows_path)
            assert result == expected_wsl_path

    def test_convert_wsl_to_windows_path(self):
        """Test WSL to Windows path conversion"""
        handler = WSLHandler()
        handler.wsl_available = True

        test_cases = [
            ("/mnt/c/Users/test", "C:\\Users\\test"),
            ("/mnt/d/data/file.txt", "D:\\data\\file.txt"),
            ("/mnt/c/Program Files", "C:\\Program Files"),
        ]

        for wsl_path, expected_windows_path in test_cases:
            result = handler.wsl_to_windows_path(wsl_path)
            assert result == expected_windows_path

    @patch('subprocess.run')
    def test_execute_wsl_command(self, mock_run):
        """Test executing commands in WSL"""
        handler = WSLHandler()
        handler.wsl_available = True

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Command executed successfully"
        mock_run.return_value = mock_process

        result = handler.execute_wsl_command("echo hello")
        assert result == "Command executed successfully"
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_execute_wsl_command_failure(self, mock_run):
        """Test WSL command execution failure"""
        handler = WSLHandler()
        handler.wsl_available = True

        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stderr = "Command failed"
        mock_run.return_value = mock_process

        with pytest.raises(WSLError, match="Command failed"):
            handler.execute_wsl_command("failing_command")

    def test_check_wsl_path_access(self):
        """Test checking WSL path accessibility"""
        handler = WSLHandler()
        handler.wsl_available = True

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            result = handler.check_path_access("/mnt/c/Users")
            assert result is True
            mock_run.assert_called_once()

    def test_sync_file_to_wsl(self):
        """Test syncing files to WSL"""
        handler = WSLHandler()
        handler.wsl_available = True

        with patch('shutil.copy2') as mock_copy:
            handler.sync_to_wsl("C:\\windows\\file.txt", "/mnt/c/wsl/file.txt")
            mock_copy.assert_called_once()

    def test_sync_file_from_wsl(self):
        """Test syncing files from WSL"""
        handler = WSLHandler()
        handler.wsl_available = True

        with patch('shutil.copy2') as mock_copy:
            handler.sync_from_wsl("/mnt/c/wsl/file.txt", "C:\\windows\\file.txt")
            mock_copy.assert_called_once()

    @patch('subprocess.run')
    def test_wsl_integration_workflow(self, mock_run):
        """Test complete WSL integration workflow"""
        handler = WSLHandler()
        handler.wsl_available = True

        # Mock multiple subprocess calls
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Success"
        mock_run.return_value = mock_process

        # Test complete workflow: Windows -> WSL -> Windows
        windows_path = "C:\\test\\file.txt"
        wsl_path = handler.windows_to_wsl_path(windows_path)

        # Sync to WSL
        handler.sync_to_wsl(windows_path, wsl_path)

        # Execute command in WSL
        result = handler.execute_wsl_command(f"ls {wsl_path}")

        # Sync back to Windows
        result_path = handler.wsl_to_windows_path(wsl_path)

        assert result == "Success"

    def test_wsl_path_validation(self):
        """Test WSL path validation"""
        handler = WSLHandler()

        # Valid WSL paths
        valid_paths = [
            "/mnt/c/Users",
            "/mnt/d/data",
            "/mnt/c/Program Files",
        ]

        for path in valid_paths:
            assert handler.validate_wsl_path(path) is True

        # Invalid WSL paths
        invalid_paths = [
            "C:\\Windows",
            "/invalid/path",
            "/mnt/invalid_drive",
        ]

        for path in invalid_paths:
            assert handler.validate_wsl_path(path) is False


class TestWindowsCommandHandler:
    """Test cases for WindowsCommandHandler class"""

    def test_command_handler_initialization(self):
        """Test WindowsCommandHandler initialization"""
        handler = WindowsCommandHandler()

        assert handler.timeout == 300  # 5 minutes default
        assert handler.shell is True
        assert handler.encoding == 'utf-8'

    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test successful command execution"""
        handler = WindowsCommandHandler()

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Command completed successfully"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        result = handler.execute("echo hello")

        assert result.returncode == 0
        assert result.stdout == "Command completed successfully"
        assert result.stderr == ""
        assert result.success is True

    @patch('subprocess.run')
    def test_execute_command_failure(self, mock_run):
        """Test command execution failure"""
        handler = WindowsCommandHandler()

        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "Command failed"
        mock_run.return_value = mock_process

        result = handler.execute("failing_command")

        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == "Command failed"
        assert result.success is False

    @patch('subprocess.run')
    def test_execute_command_with_timeout(self, mock_run):
        """Test command execution with timeout"""
        handler = WindowsCommandHandler()
        handler.timeout = 10

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Quick command"
        mock_run.return_value = mock_process

        result = handler.execute("echo quick", timeout=10)

        assert result.success is True
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_execute_command_timeout(self, mock_run):
        """Test command timeout"""
        handler = WindowsCommandHandler()

        from unittest.mock import patch
        with patch('time.sleep', side_effect=TimeoutError("Timeout")):
            with pytest.raises(CommandError, match="Command timed out"):
                handler.execute("sleep 10", timeout=1)

    def test_build_command_args(self):
        """Test building command arguments"""
        handler = WindowsCommandHandler()

        # Test basic command
        args = handler.build_args("echo hello")
        assert args == ["echo", "hello"]

        # Test command with complex arguments
        args = handler.build_args('copy "C:\\test file.txt" "D:\\destination\\"')
        assert "C:\\test file.txt" in str(args)
        assert "D:\\destination\\" in str(args)

    def test_execute_admin_command(self):
        """Test executing admin commands"""
        handler = WindowsCommandHandler()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            result = handler.execute_admin("net user")

            assert result.success is True
            mock_run.assert_called_once()

    def test_run_batch_file(self):
        """Test running batch files"""
        handler = WindowsCommandHandler()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False) as f:
            f.write("@echo off\necho Hello from batch\n")
            batch_path = f.name

        try:
            with patch('subprocess.run') as mock_run:
                mock_process = Mock()
                mock_process.returncode = 0
                mock_process.stdout = "Hello from batch"
                mock_run.return_value = mock_process

                result = handler.run_batch(batch_path)

                assert result.success is True
                assert result.stdout == "Hello from batch"

        finally:
            os.unlink(batch_path)

    def test_execute_powershell_command(self):
        """Test executing PowerShell commands"""
        handler = WindowsCommandHandler()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "PowerShell output"
            mock_run.return_value = mock_process

            result = handler.execute_powershell("Get-Process")

            assert result.success is True
            assert result.stdout == "PowerShell output"

    def test_command_output_capture(self):
        """Test capturing command output"""
        handler = WindowsCommandHandler()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "Line1\nLine2\nLine3"
            mock_run.return_value = mock_process

            result = handler.execute("echo Line1 & echo Line2 & echo Line3")

            assert result.returncode == 0
            assert "Line1" in result.stdout
            assert "Line2" in result.stdout
            assert "Line3" in result.stdout

    def test_command_error_handling(self):
        """Test command error handling"""
        handler = WindowsCommandHandler()

        # Test with non-existent command
        with pytest.raises(CommandError, match="Command not found"):
            handler.execute("nonexistent_command")

        # Test with permission denied
        with pytest.raises(CommandError, match="Permission denied"):
            handler.execute("runas_command")  # Would require admin rights

    def test_windows_specific_commands(self):
        """Test Windows-specific commands"""
        handler = WindowsCommandHandler()

        # Test robocopy
        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "Robocopy completed"
            mock_run.return_value = mock_process

            result = handler.robocopy("source", "destination")

            assert result.success is True
            mock_run.assert_called_once()

        # Test xcopy
        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "Xcopy completed"
            mock_run.return_value = mock_process

            result = handler.xcopy("source", "destination")

            assert result.success is True
            mock_run.assert_called_once()


class TestWindowsPerformanceOptimizer:
    """Test cases for WindowsPerformanceOptimizer class"""

    def test_performance_optimizer_initialization(self):
        """Test WindowsPerformanceOptimizer initialization"""
        optimizer = WindowsPerformanceOptimizer()

        assert optimizer.enabled is True
        assert optimizer.priority_boost is True
        assert optimizer.memory_optimization is True

    def test_optimize_process_priority(self):
        """Test process priority optimization"""
        optimizer = WindowsPerformanceOptimizer()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            result = optimizer.optimize_process_priority("python.exe", "high")

            assert result is True
            mock_run.assert_called_once()

    def test_optimize_memory_usage(self):
        """Test memory usage optimization"""
        optimizer = WindowsPerformanceOptimizer()

        with patch('psutil.Process') as mock_process:
            mock_instance = Mock()
            mock_instance.memory_info.return_value = Mock(rss=1000000)
            mock_process.return_value = mock_instance

            result = optimizer.optimize_memory_usage("python.exe")

            assert result is True

    def test_enable_write_caching(self):
        """Test enabling write caching"""
        optimizer = WindowsPerformanceOptimizer()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            result = optimizer.enable_write_caching()

            assert result is True
            mock_run.assert_called_once()

    def test_disable_windows_defender_realtime(self):
        """Test disabling Windows Defender temporarily"""
        optimizer = WindowsPerformanceOptimizer()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            result = optimizer.disable_defender_realtime()

            assert result is True

    def test_optimize_network_performance(self):
        """Test network performance optimization"""
        optimizer = WindowsPerformanceOptimizer()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            result = optimizer.optimize_network_performance()

            assert result is True
            mock_run.assert_called_once()

    def test_create_performance_profile(self):
        """Test creating performance profile"""
        optimizer = WindowsPerformanceOptimizer()

        profile = optimizer.create_performance_profile("deployment")

        assert profile["name"] == "deployment"
        assert "process_priority" in profile
        assert "memory_optimization" in profile
        assert "write_caching" in profile

    def test_apply_performance_profile(self):
        """Test applying performance profile"""
        optimizer = WindowsPerformanceOptimizer()

        profile = {
            "process_priority": "high",
            "memory_optimization": True,
            "write_caching": True
        }

        with patch.object(optimizer, 'optimize_process_priority') as mock_priority, \
             patch.object(optimizer, 'optimize_memory_usage') as mock_memory, \
             patch.object(optimizer, 'enable_write_caching') as mock_cache:

            result = optimizer.apply_performance_profile(profile)

            assert result is True
            mock_priority.assert_called_once()
            mock_memory.assert_called_once()
            mock_cache.assert_called_once()


class TestWindowsSecurityManager:
    """Test cases for WindowsSecurityManager class"""

    def test_security_manager_initialization(self):
        """Test WindowsSecurityManager initialization"""
        manager = WindowsSecurityManager()

        assert manager.enabled is True
        assert manager.audit_logging is True

    def test_validate_admin_rights(self):
        """Test admin rights validation"""
        manager = WindowsSecurityManager()

        with patch('ctypes.windll.shell32.IsUserAnAdmin') as mock_admin:
            mock_admin.return_value = 1  # True

            result = manager.validate_admin_rights()
            assert result is True

            mock_admin.return_value = 0  # False
            result = manager.validate_admin_rights()
            assert result is False

    def test_check_file_security(self):
        """Test file security checking"""
        manager = WindowsSecurityManager()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            with patch('os.stat') as mock_stat:
                mock_stat_result = Mock()
                mock_stat_result.st_mode = 0o644  # rw-r--r--
                mock_stat.return_value = mock_stat_result

                result = manager.check_file_security(temp_path)

                assert "permissions" in result
                assert "owner" in result
                assert "security_level" in result

        finally:
            os.unlink(temp_path)

    def test_validate_command_safety(self):
        """Test command safety validation"""
        manager = WindowsSecurityManager()

        # Safe commands
        safe_commands = [
            "echo hello",
            "copy file1.txt file2.txt",
            "python script.py"
        ]

        for cmd in safe_commands:
            assert manager.validate_command_safety(cmd) is True

        # Dangerous commands
        dangerous_commands = [
            "rm -rf /",
            "del /s /q *.*",
            "format c:",
            "shutdown /s /t 0"
        ]

        for cmd in dangerous_commands:
            assert manager.validate_command_safety(cmd) is False

    def test_scan_for_malicious_patterns(self):
        """Test scanning for malicious patterns"""
        manager = WindowsSecurityManager()

        safe_text = "This is a safe deployment script"
        malicious_text = "rm -rf / && format c:"

        assert manager.scan_for_malicious_patterns(safe_text) == []
        assert len(manager.scan_for_malicious_patterns(malicious_text)) > 0

    def test_enable_audit_logging(self):
        """Test enabling audit logging"""
        manager = WindowsSecurityManager()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            result = manager.enable_audit_logging()

            assert result is True
            mock_run.assert_called_once()

    def test_log_security_event(self):
        """Test logging security events"""
        manager = WindowsSecurityManager()

        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value = mock_file

            manager.log_security_event("command_execution", "echo hello")

            # Verify logging was called
            assert mock_file.write.called

    def test_validate_certificate(self):
        """Test certificate validation"""
        manager = WindowsSecurityManager()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "Certificate is valid"
            mock_run.return_value = mock_process

            result = manager.validate_certificate("certificate.pem")

            assert result is True


class TestWindowsRegistryHandler:
    """Test cases for WindowsRegistryHandler class"""

    def test_registry_handler_initialization(self):
        """Test WindowsRegistryHandler initialization"""
        handler = WindowsRegistryHandler()

        assert handler.enabled is True
        assert handler.backup_before_change is True

    def test_read_registry_value(self):
        """Test reading registry values"""
        handler = WindowsRegistryHandler()

        with patch('winreg.OpenKey') as mock_open, \
             patch('winreg.QueryValueEx') as mock_query:

            mock_query.return_value = ("Registry Value", 1)  # (value, type)

            result = handler.read_value("HKEY_LOCAL_MACHINE\\SOFTWARE\\Test", "TestKey")

            assert result == "Registry Value"
            mock_open.assert_called_once()
            mock_query.assert_called_once()

    def test_write_registry_value(self):
        """Test writing registry values"""
        handler = WindowsRegistryHandler()

        with patch('winreg.OpenKey') as mock_open, \
             patch('winreg.SetValueEx') as mock_set:

            result = handler.write_value("HKEY_LOCAL_MACHINE\\SOFTWARE\\Test", "TestKey", "TestValue")

            assert result is True
            mock_open.assert_called_once()
            mock_set.assert_called_once()

    def test_create_registry_key(self):
        """Test creating registry keys"""
        handler = WindowsRegistryHandler()

        with patch('winreg.CreateKey') as mock_create:

            result = handler.create_key("HKEY_LOCAL_MACHINE\\SOFTWARE\\NewKey")

            assert result is True
            mock_create.assert_called_once()

    def test_delete_registry_key(self):
        """Test deleting registry keys"""
        handler = WindowsRegistryHandler()

        with patch('winreg.DeleteKey') as mock_delete:

            result = handler.delete_key("HKEY_LOCAL_MACHINE\\SOFTWARE\\TestKey")

            assert result is True
            mock_delete.assert_called_once()

    def test_backup_registry(self):
        """Test registry backup"""
        handler = WindowsRegistryHandler()

        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            result = handler.backup_registry("HKEY_LOCAL_MACHINE\\SOFTWARE")

            assert result is True
            mock_run.assert_called_once()

    def test_registry_value_validation(self):
        """Test registry value validation"""
        handler = WindowsRegistryHandler()

        # Valid registry paths
        valid_paths = [
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\Test",
            "HKEY_CURRENT_USER\\Software\\Test",
            "HKEY_CLASSES_ROOT\\Test"
        ]

        for path in valid_paths:
            assert handler.validate_registry_path(path) is True

        # Invalid registry paths
        invalid_paths = [
            "INVALID\\PATH",
            "HKEY_INVALID_HIVE\\Test",
            ""
        ]

        for path in invalid_paths:
            assert handler.validate_registry_path(path) is False


class TestWindowsUtils:
    """Test cases for WindowsUtils class"""

    def test_windows_utils_initialization(self):
        """Test WindowsUtils initialization"""
        utils = WindowsUtils()

        assert utils.is_windows is True
        assert utils.version is not None
        assert utils.architecture is not None

    def test_get_windows_version(self):
        """Test getting Windows version"""
        utils = WindowsUtils()

        with patch('platform.win32_ver') as mock_win32:
            mock_win32.return_value = ("10", "10.0.19041", "SP0", "Multiprocessor Free")

            version = utils.get_windows_version()

            assert version == "10.0.19041"

    def test_get_system_info(self):
        """Test getting system information"""
        utils = WindowsUtils()

        with patch('platform.machine') as mock_machine, \
             patch('platform.processor') as mock_processor, \
             patch('platform.win32_ver') as mock_win32:

            mock_machine.return_value = "AMD64"
            mock_processor.return_value = "Intel64 Family 6 Model 158 Stepping 10"
            mock_win32.return_value = ("10", "10.0.19041", "SP0", "Multiprocessor Free")

            info = utils.get_system_info()

            assert "architecture" in info
            assert "processor" in info
            assert "version" in info
            assert info["architecture"] == "AMD64"

    def test_check_admin_rights(self):
        """Test checking admin rights"""
        utils = WindowsUtils()

        with patch('ctypes.windll.shell32.IsUserAnAdmin') as mock_admin:
            mock_admin.return_value = 1

            assert utils.is_admin() is True

            mock_admin.return_value = 0
            assert utils.is_admin() is False

    def test_get_disk_space(self):
        """Test getting disk space information"""
        utils = WindowsUtils()

        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value = Mock(
                total=1000000000,
                used=500000000,
                free=500000000
            )

            space = utils.get_disk_space("C:\\")
            assert space["total"] == 1000000000
            assert space["used"] == 500000000
            assert space["free"] == 500000000

    def test_check_filesystem_compatibility(self):
        """Test filesystem compatibility checking"""
        utils = WindowsUtils()

        # Test NTFS compatibility
        assert utils.is_filesystem_supported("NTFS") is True

        # Test unsupported filesystems
        assert utils.is_filesystem_supported("ext4") is False
        assert utils.is_filesystem_supported("APFS") is False

    def test_optimize_for_deployment(self):
        """Test system optimization for deployment"""
        utils = WindowsUtils()

        with patch.object(WindowsPerformanceOptimizer, '__init__', return_value=None), \
             patch.object(WindowsSecurityManager, '__init__', return_value=None):

            with patch.object(WindowsPerformanceOptimizer(), 'apply_performance_profile') as mock_perf, \
                 patch.object(WindowsSecurityManager(), 'validate_admin_rights') as mock_sec:

                utils.optimize_for_deployment()

                mock_perf.assert_called_once()
                mock_sec.assert_called_once()

    def test_get_environment_variables(self):
        """Test getting environment variables"""
        utils = WindowsUtils()

        with patch('os.environ') as mock_environ:
            mock_environ.__getitem__ = Mock(return_value="test_value")
            mock_environ.__contains__ = Mock(return_value=True)

            env = utils.get_environment_variables(["PATH", "TEMP"])

            assert "PATH" in env
            assert "TEMP" in env
            assert env["PATH"] == "test_value"

    def test_create_windows_shortcut(self):
        """Test creating Windows shortcuts"""
        utils = WindowsUtils()

        with patch('pythoncom.CoInitialize'), \
             patch('win32com.client.Dispatch') as mock_dispatch:

            mock_shell = Mock()
            mock_dispatch.return_value = mock_shell

            result = utils.create_shortcut(
                target="C:\\test.exe",
                shortcut_path="C:\\Users\\test\\Desktop\\Test.lnk",
                description="Test shortcut"
            )

            assert result is True
            mock_shell.CreateShortCut.assert_called_once()


class TestWindowsErrorHandling:
    """Test Windows error handling scenarios"""

    def test_windows_error_creation(self):
        """Test WindowsError creation"""
        error = WindowsError("Test Windows error")

        assert str(error) == "Test Windows error"
        assert isinstance(error, Exception)

    def test_wsl_error_creation(self):
        """Test WSLError creation"""
        error = WSLError("Test WSL error")

        assert str(error) == "Test WSL error"
        assert isinstance(error, WindowsError)

    def test_command_error_creation(self):
        """Test CommandError creation"""
        error = CommandError("Test command error", 1, "stderr output")

        assert str(error) == "Test command error"
        assert error.returncode == 1
        assert error.stderr == "stderr output"

    def test_error_hierarchy(self):
        """Test error class hierarchy"""
        assert issubclass(WSLError, WindowsError)
        assert issubclass(CommandError, WindowsError)

    def test_error_recovery(self):
        """Test error recovery mechanisms"""
        handler = WindowsCommandHandler()

        # Test command execution with error recovery
        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 1
            mock_process.stderr = "Error occurred"
            mock_run.return_value = mock_process

            try:
                handler.execute("failing_command")
            except CommandError as e:
                assert e.returncode == 1
                assert e.stderr == "Error occurred"


class TestWindowsIntegration:
    """Integration tests for Windows optimization components"""

    def test_complete_windows_deployment_workflow(self):
        """Test complete Windows deployment workflow"""
        # Initialize all components
        path_handler = WindowsPathHandler()
        encoding_handler = WindowsEncodingHandler()
        command_handler = WindowsCommandHandler()
        security_manager = WindowsSecurityManager()
        performance_optimizer = WindowsPerformanceOptimizer()

        # Step 1: Validate and normalize paths
        source_path = "C:\\source\\deployment"
        normalized_path = path_handler.normalize_path(source_path)

        assert normalized_path == source_path

        # Step 2: Check encoding
        korean_text = "한국어 배포 스크립트"
        encoded_text = encoding_handler.encode_text(korean_text, 'utf-8')

        assert encoded_text is not None

        # Step 3: Validate command safety
        safe_command = "echo \"배포 시작\""
        is_safe = security_manager.validate_command_safety(safe_command)

        assert is_safe is True

        # Step 4: Execute deployment command
        with patch('subprocess.run') as mock_run:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.stdout = "Deployment completed"
            mock_run.return_value = mock_process

            result = command_handler.execute(safe_command)

            assert result.success is True

        # Step 5: Optimize performance
        profile = performance_optimizer.create_performance_profile("deployment")
        optimization_result = performance_optimizer.apply_performance_profile(profile)

        assert optimization_result is True

    def test_wsl_integration_workflow(self):
        """Test WSL integration workflow"""
        wsl_handler = WSLHandler()
        path_handler = WindowsPathHandler()

        # Enable WSL handling
        wsl_handler.wsl_available = True

        # Test Windows to WSL path conversion
        windows_path = "C:\\Users\\developer\\project"
        wsl_path = wsl_handler.windows_to_wsl_path(windows_path)

        assert wsl_path == "/mnt/c/Users/developer/project"

        # Test bidirectional file sync
        with patch('shutil.copy2') as mock_copy:
            # Sync to WSL
            wsl_handler.sync_to_wsl(windows_path, wsl_path)
            assert mock_copy.call_count == 1

            # Sync from WSL
            wsl_handler.sync_from_wsl(wsl_path, windows_path)
            assert mock_copy.call_count == 2

    @patch('platform.system')
    def test_cross_platform_behavior(self, mock_system):
        """Test behavior on different platforms"""
        # Test on Windows
        mock_system.return_value = 'Windows'
        path_handler = WindowsPathHandler()

        assert path_handler.is_windows is True
        assert path_handler.path_separator == "\\"

        # Test on Linux
        mock_system.return_value = 'Linux'
        linux_handler = WindowsPathHandler()

        assert linux_handler.is_windows is False
        # Should still handle Windows paths correctly
        result = linux_handler.normalize_path("C:\\Windows\\Test")
        assert "C:\\Windows\\Test" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])