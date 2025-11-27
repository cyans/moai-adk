"""
PlatformDetector 테스트 파일

TAG-WIN-001: OS 자동 감지 모듈 검증
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 테스트 대상 모듈 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'moai_adk', 'platform'))

from detector import PlatformDetector


class TestPlatformDetector(unittest.TestCase):
    """PlatformDetector 클래스 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.detector = PlatformDetector()

    def test_detect_os_windows(self):
        """Windows OS 감지 테스트"""
        with patch('detector.sys.platform', 'win32'):
            os_type = self.detector.detect_os()
            self.assertEqual(os_type, 'windows')

    def test_detect_os_macos(self):
        """macOS 감지 테스트"""
        with patch('detector.sys.platform', 'darwin'):
            os_type = self.detector.detect_os()
            self.assertEqual(os_type, 'macos')

    def test_detect_os_linux(self):
        """Linux 감지 테스트"""
        with patch('detector.sys.platform', 'linux'):
            os_type = self.detector.detect_os()
            self.assertEqual(os_type, 'linux')

    def test_detect_os_unknown(self):
        """알 수 없는 OS 감지 테스트"""
        with patch('detector.sys.platform', 'unknown_os'):
            os_type = self.detector.detect_os()
            self.assertEqual(os_type, 'unknown')

    def test_get_platform_config_windows(self):
        """Windows 플랫폼 설정 반환 테스트"""
        with patch('detector.sys.platform', 'win32'):
            config = self.detector.get_platform_config()
            self.assertIn('command', config)
            self.assertIn('args', config)
            self.assertEqual(config['command'], 'cmd')

    def test_get_platform_config_macos(self):
        """macOS 플랫폼 설정 반환 테스트"""
        with patch('detector.sys.platform', 'darwin'):
            config = self.detector.get_platform_config()
            self.assertIn('command', config)
            self.assertIn('args', config)
            self.assertEqual(config['command'], 'bash')

    def test_get_platform_config_linux(self):
        """Linux 플랫폼 설정 반환 테스트"""
        with patch('detector.sys.platform', 'linux'):
            config = self.detector.get_platform_config()
            self.assertIn('command', config)
            self.assertIn('args', config)
            self.assertEqual(config['command'], 'bash')

    def test_validate_platform_windows(self):
        """Windows 플랫폼 유효성 검사 테스트"""
        with patch('detector.sys.platform', 'win32'):
            is_valid = self.detector.validate_platform()
            self.assertTrue(is_valid)

    def test_validate_platform_macos(self):
        """macOS 플랫폼 유효성 검사 테스트"""
        with patch('detector.sys.platform', 'darwin'):
            is_valid = self.detector.validate_platform()
            self.assertTrue(is_valid)

    def test_validate_platform_linux(self):
        """Linux 플랫폼 유효성 검사 테스트"""
        with patch('detector.sys.platform', 'linux'):
            is_valid = self.detector.validate_platform()
            self.assertTrue(is_valid)

    def test_validate_platform_unknown(self):
        """알 수 없는 OS 유효성 검사 테스트"""
        with patch('detector.sys.platform', 'unknown_os'):
            is_valid = self.detector.validate_platform()
            self.assertFalse(is_valid)

    def test_platform_detector_initialization(self):
        """PlatformDetector 초기화 테스트"""
        detector = PlatformDetector()
        self.assertIsNotNone(detector)
        self.assertTrue(hasattr(detector, 'detect_os'))
        self.assertTrue(hasattr(detector, 'get_platform_config'))
        self.assertTrue(hasattr(detector, 'validate_platform'))

    def test_comprehensive_platform_detection(self):
        """종합 플랫폼 감지 테스트 - 실제 환경에서의 동작"""
        # 실제 시스템 환경에서 테스트 (테스트 환경에 따라 다를 수 있음)
        detected_os = self.detector.detect_os()
        self.assertIn(detected_os, ['windows', 'macos', 'linux', 'unknown'])

        # 플랫폼 설정 검증
        config = self.detector.get_platform_config()
        self.assertIsInstance(config, dict)
        self.assertIn('command', config)

        # 유효성 검사
        is_valid = self.detector.validate_platform()
        self.assertIsInstance(is_valid, bool)


if __name__ == '__main__':
    unittest.main()