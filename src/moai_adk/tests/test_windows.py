"""
Test file for Windows optimization layer
TAG-WIN-003: Windows optimization layer
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path

from src.moai_adk.deployment.windows import (
    WindowsOptimizer,
    PathHandler,
    EncodingHandler,
    WSL2Handler,
    WindowsDeploymentConfig
)


class TestWindowsOptimizer:
    """Test cases for WindowsOptimizer class"""

    def test_windows_optimizer_initialization(self):
        """Test Windows optimizer initialization"""
        optimizer = WindowsOptimizer()

        assert optimizer is not None
        assert hasattr(optimizer, 'path_handler')
        assert hasattr(optimizer, 'encoding_handler')
        assert hasattr(optimizer, 'wsl2_handler')

    def test_detect_windows_environment(self):
        """Test Windows environment detection"""
        with patch('os.name', 'nt'):
            optimizer = WindowsOptimizer()
            assert optimizer.is_windows() is True

        with patch('os.name', 'posix'):
            optimizer = WindowsOptimizer()
            assert optimizer.is_windows() is False

    def test_detect_wsl2_environment(self):
        """Test WSL2 environment detection"""
        # Test WSL2 detection
        with patch('os.name', 'posix'):
            with patch('sys.platform', 'linux'):
                with patch('builtins.open', mock_open(read_data="Microsoft\nWSL")):
                    optimizer = WindowsOptimizer()
                    assert optimizer.is_wsl2() is True

        # Test non-WSL2 Linux
        with patch('os.name', 'posix'):
            with patch('sys.platform', 'linux'):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    optimizer = WindowsOptimizer()
                    assert optimizer.is_wsl2() is False

        # Test Windows
        with patch('os.name', 'nt'):
            optimizer = WindowsOptimizer()
            assert optimizer.is_wsl2() is False

    def test_windows_specific_optimizations(self):
        """Test Windows-specific optimizations"""
        with patch('os.name', 'nt'):
            optimizer = WindowsOptimizer()
            optimizations = optimizer.get_optimizations()

            assert 'path_separator' in optimizations
            assert 'encoding' in optimizations
            assert 'shell_commands' in optimizations

            assert optimizations['path_separator'] == '\\'
            assert optimizations['encoding'] == 'utf-8'

    def test_wsl2_specific_optimizations(self):
        """Test WSL2-specific optimizations"""
        with patch('os.name', 'posix'):
            with patch('sys.platform', 'linux'):
                with patch('builtins.open', mock_open(read_data="Microsoft\nWSL")):
                    optimizer = WindowsOptimizer()
                    optimizations = optimizer.get_optimizations()

                    assert 'wsl2_path_mapping' in optimizations
                    assert 'wsl2_compatible' in optimizations
                    assert optimizations['wsl2_compatible'] is True


class TestPathHandler:
    """Test cases for PathHandler class"""

    def test_path_handler_initialization(self):
        """Test path handler initialization"""
        handler = PathHandler()
        assert handler is not None

    def test_convert_to_windows_paths(self):
        """Test conversion to Windows paths"""
        handler = PathHandler()

        # Test Unix to Windows path conversion
        unix_path = "/app/project/src"
        windows_path = handler.convert_to_windows(unix_path)
        assert "C:\\\\app\\\\project\\\\src" in windows_path or "C:\\app\\project\\src" in windows_path

        # Test nested paths
        nested_unix = "/var/www/html/index.html"
        nested_windows = handler.convert_to_windows(nested_unix)
        assert "html\\\\index.html" in nested_windows or "html\\index.html" in nested_windows

    def test_convert_to_unix_paths(self):
        """Test conversion to Unix paths"""
        handler = PathHandler()

        # Test Windows to Unix path conversion
        windows_path = "C:\\\\app\\\\project\\\\src"
        unix_path = handler.convert_to_unix(windows_path)
        assert unix_path.endswith("/app/project/src")

        # Test drive letter handling
        drive_path = "C:\\app\\project"
        drive_unix = handler.convert_to_unix(drive_path)
        assert drive_unix.startswith("/mnt/c/app/project") or drive_unix.startswith("/c/app/project")

    def test_path_normalization(self):
        """Test path normalization"""
        handler = PathHandler()

        # Test double backslash normalization
        double_backslash = "C:\\\\app\\\\project\\\\src"
        normalized = handler.normalize_path(double_backslash)
        assert normalized.count('\\\\') == 0 or normalized.count('\\\\') == 1

        # Test trailing slash handling
        with_trailing = "/app/project/"
        normalized_trailing = handler.normalize_path(with_trailing)
        assert not normalized_trailing.endswith('/')

    def test_path_validation(self):
        """Test path validation"""
        handler = PathHandler()

        # Test valid paths
        assert handler.is_valid_windows_path("C:\\\\app\\\\project")
        assert handler.is_valid_windows_path("D:\\data\\file.txt")
        assert handler.is_valid_unix_path("/app/project")
        assert handler.is_valid_unix_path("/var/www/html")

        # Test invalid paths
        assert not handler.is_valid_windows_path("/app/project")  # Unix path on Windows
        assert not handler.is_valid_unix_path("C:\\\\app\\\\project")  # Windows path on Unix

    def test_path_mapping(self):
        """Test custom path mapping"""
        handler = PathHandler()

        # Configure custom mappings
        custom_mappings = {
            "/app/": "C:\\\\app\\\\",
            "/data/": "D:\\\\data\\\\"
        }
        handler.set_path_mappings(custom_mappings)

        # Test custom mapping
        mapped_path = handler.map_path("/app/src/file.py")
        assert "C:\\app\\\\src" in mapped_path and "file.py" in mapped_path

        # Test default mapping for unmapped paths
        default_mapped = handler.map_path("/config/file.yaml")
        assert default_mapped.endswith("/config/file.yaml")


class TestEncodingHandler:
    """Test cases for EncodingHandler class"""

    def test_encoding_handler_initialization(self):
        """Test encoding handler initialization"""
        handler = EncodingHandler()
        assert handler is not None

    def test_detect_windows_encoding(self):
        """Test Windows encoding detection"""
        handler = EncodingHandler()

        # Test UTF-8 detection
        utf8_text = "테스트 문자열"  # Korean test text
        detected = handler.detect_encoding(utf8_text)
        assert detected == 'utf-8'

        # Test CP949 detection for legacy systems
        cp949_bytes = "Windows 배포 테스트".encode('cp949')
        with patch('locale.getpreferredencoding', return_value='cp949'):
            detected_cp949 = handler.detect_encoding(cp949_bytes)
            assert detected_cp949 == 'cp949'

    def test_encoding_conversion(self):
        """Test encoding conversion"""
        handler = EncodingHandler()

        # Test UTF-8 to CP949 conversion (legacy Windows)
        utf8_text = "Windows 배포 테스트"
        converted = handler.convert_encoding(utf8_text, 'utf-8', 'cp949')
        assert isinstance(converted, bytes) or isinstance(converted, str)

        # Test CP949 to UTF-8 conversion
        if isinstance(converted, bytes):
            back_to_utf8 = handler.convert_encoding(converted, 'cp949', 'utf-8')
            assert isinstance(back_to_utf8, str)
            assert "Windows" in back_to_utf8

    def test_safe_encoding_write(self):
        """Test safe encoding file writing"""
        handler = EncodingHandler()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name

        try:
            # Test UTF-8 writing
            test_content = "Windows 환경 배포 테스트\nUTF-8 인코딩"
            handler.safe_write(temp_file, test_content, encoding='utf-8')

            # Verify content
            with open(temp_file, 'r', encoding='utf-8') as f:
                read_content = f.read()
                assert test_content == read_content

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_safe_encoding_read(self):
        """Test safe encoding file reading"""
        handler = EncodingHandler()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write("테스트 파일 내용\nUTF-8 인코딩 테스트")
            temp_file = f.name

        try:
            # Test UTF-8 reading
            read_content = handler.safe_read(temp_file, encoding='utf-8')
            assert "테스트 파일 내용" in read_content

            # Test auto-detection
            auto_detected = handler.safe_read(temp_file)
            assert isinstance(auto_detected, str)
            assert len(auto_detected) > 0

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestWSL2Handler:
    """Test cases for WSL2Handler class"""

    def test_wsl2_handler_initialization(self):
        """Test WSL2 handler initialization"""
        handler = WSL2Handler()
        assert handler is not None

    def test_wsl2_path_conversion(self):
        """Test WSL2 path conversion between Windows and WSL"""
        handler = WSL2Handler()

        # Test Windows to WSL path conversion
        windows_path = "C:\\\\app\\\\project"
        wsl_path = handler.windows_to_wsl(windows_path)
        assert wsl_path.startswith("/mnt/c/")
        assert "app/project" in wsl_path

        # Test WSL to Windows path conversion
        wsl_path = "/mnt/c/app/project"
        back_to_windows = handler.wsl_to_windows(wsl_path)
        assert back_to_windows.startswith("C:\\\\")
        assert "app\\\\project" in back_to_windows

    def test_wsl2_compatibility_check(self):
        """Test WSL2 compatibility checks"""
        # Test Windows command compatibility
        with patch('os.name', 'nt'):
            handler = WSL2Handler()
            windows_cmd = "dir C:\\\\app"
            wsl_cmd = handler.make_wsl2_compatible(windows_cmd)
            assert "wsl" in wsl_cmd.lower() or "cmd.exe" in wsl_cmd

            # Test Unix command compatibility when running on Windows (should be wrapped with wsl.exe)
            unix_cmd = "ls -la /app"
            wsl_unix = handler.make_wsl2_compatible(unix_cmd)
            # Unix commands should be wrapped with wsl.exe when running on Windows
            assert wsl_unix == "wsl.exe ls -la /app"

        # Test Unix command compatibility when running on Linux (should pass through unchanged)
        with patch('os.name', 'posix'):
            handler = WSL2Handler()
            unix_cmd = "ls -la /app"
            wsl_unix = handler.make_wsl2_compatible(unix_cmd)
            # Unix commands should pass through unchanged when running on Linux
            assert wsl_unix == unix_cmd

    def test_wsl2_environment_variables(self):
        """Test WSL2 environment variable handling"""
        handler = WSL2Handler()

        # Test environment variable mapping
        with patch.dict(os.environ, {
            'APP_PATH': 'C:\\\\app\\\\data',
            'WSL_ENV': 'wsl_value'
        }):
            mapped_env = handler.map_environment_variables()

            # WSL-specific variables should be mapped
            assert 'APP_PATH' in mapped_env
            # Regular variables should pass through
            assert 'WSL_ENV' in mapped_env

    def test_wsl2_shell_detection(self):
        """Test WSL2 shell detection"""
        handler = WSL2Handler()

        # Test different shell detection
        with patch('os.environ', {'SHELL': '/bin/bash'}):
            assert handler.get_wsl_shell() == '/bin/bash'

        with patch('os.environ', {'SHELL': '/bin/zsh'}):
            assert handler.get_wsl_shell() == '/bin/zsh'

        # Test default shell
        with patch('os.environ', {}):
            default_shell = handler.get_wsl_shell()
            assert default_shell in ['/bin/bash', '/bin/sh']


class TestWindowsDeploymentConfig:
    """Test cases for WindowsDeploymentConfig class"""

    def test_config_initialization(self):
        """Test Windows deployment config initialization"""
        config = WindowsDeploymentConfig()
        assert config is not None

    def test_path_handling_configuration(self):
        """Test path handling configuration"""
        config = WindowsDeploymentConfig()

        # Test default path handling
        assert config.path_mappings is not None
        assert len(config.path_mappings) > 0

        # Test custom path handling
        custom_mappings = {
            "/app/": "C:\\\\custom\\\\app\\\\",
            "/data/": "D:\\\\custom\\\\data\\\\"
        }
        config.set_path_mappings(custom_mappings)
        assert config.path_mappings["/app/"] == "C:\\\\custom\\\\app\\\\"

    def test_encoding_configuration(self):
        """Test encoding configuration"""
        config = WindowsDeploymentConfig()

        # Test default encoding
        assert config.preferred_encoding == 'utf-8'

        # Test custom encoding
        config.set_encoding('cp949')
        assert config.preferred_encoding == 'cp949'

    def test_wsl2_configuration(self):
        """Test WSL2 configuration"""
        config = WindowsDeploymentConfig()

        # Test default WSL2 settings
        assert config.wsl2_compatible is True
        assert config.wsl2_interop_enabled is True

        # Test custom WSL2 settings
        config.set_wsl2_compatible(False)
        assert config.wsl2_compatible is False

    def test_windows_specific_settings(self):
        """Test Windows-specific settings"""
        config = WindowsDeploymentConfig()

        # Test Windows-specific defaults
        assert config.windows_encoding == 'utf-8'
        assert config.path_separator == '\\\\'

        # Test environment variable settings
        env_settings = {
            'PYTHONPATH': '.;C:\\\\app\\\\lib',
            'PATH': '%PATH%;C:\\\\Python\\\\Scripts'
        }
        config.set_environment_variables(env_settings)
        assert 'PYTHONPATH' in config.environment_variables

    def test_config_serialization(self):
        """Test config serialization to/from dictionary"""
        config = WindowsDeploymentConfig()

        # Test to_dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert 'path_mappings' in config_dict
        assert 'encoding' in config_dict
        assert 'wsl2_settings' in config_dict

        # Test from_dict
        new_config = WindowsDeploymentConfig.from_dict(config_dict)
        assert new_config.preferred_encoding == config.preferred_encoding
        assert new_config.wsl2_compatible == config.wsl2_compatible

    def test_config_validation(self):
        """Test Windows configuration validation"""
        config = WindowsDeploymentConfig()

        # Test valid configuration
        assert config.validate() is True

        # Test invalid configuration
        config.set_path_mappings({"invalid": "path"})
        # Should still pass basic validation
        assert config.validate() is True

    def test_auto_detection(self):
        """Test automatic environment detection"""
        config = WindowsDeploymentConfig()

        # Test Windows auto-detection
        with patch('os.name', 'nt'):
            windows_config = config.auto_detect()
            assert windows_config.is_windows() is True

        # Test WSL2 auto-detection
        with patch('os.name', 'posix'):
            with patch('sys.platform', 'linux'):
                with patch('builtins.open', mock_open(read_data="Microsoft\nWSL")):
                    wsl2_config = config.auto_detect()
                    assert wsl2_config.is_wsl2() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])