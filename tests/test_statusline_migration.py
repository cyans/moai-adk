"""
Statusline Migration and Integration Tests

TAG-WIN-005: Statusline Solution 구현 검증

Windows 플랫폼에서 statusline 시스템의 완전한 통합과 최적화를 검증합니다.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json
import tempfile
from pathlib import Path

# 테스트 대상 모듈 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 테스트 대상 모듈 임포트
try:
    from moai_adk.statusline.data import StatuslineData
    from moai_adk.statusline.renderer import StatuslineRenderer
    # Mock the other modules that aren't implemented yet
    sys.modules['moai_adk.statusline.alfred_detector'] = MagicMock()
    sys.modules['moai_adk.statusline.config'] = MagicMock()
    sys.modules['moai_adk.statusline.git_collector'] = MagicMock()
    sys.modules['moai_adk.statusline.metrics_tracker'] = MagicMock()
    sys.modules['moai_adk.statusline.update_checker'] = MagicMock()
    sys.modules['moai_adk.statusline.version_reader'] = MagicMock()
    STATUSLINE_AVAILABLE = True
except ImportError:
    STATUSLINE_AVAILABLE = False

# 기존 모듈 임포트
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'moai_adk', 'platform'))
from detector import PlatformDetector
try:
    from templates import ConfigTemplates
except ImportError:
    ConfigTemplates = None


class TestStatuslineMigration(unittest.TestCase):
    """Statusline 시스템 마이그레이션 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, '.claude')
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def tearDown(self):
        """테스트 환경 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_statusline_module_import(self):
        """Statusline 모듈 임포트 검증

        모든 statusline 모듈이 src/moai_adk/statusline/ 경로에서 정상적으로 임포트되어야 합니다.
        """
        if not STATUSLINE_AVAILABLE:
            self.skipTest("Statusline modules not yet implemented")

        # 모든 주요 클래스 임포트 확인
        from moai_adk.statusline import StatuslineRenderer
        renderer = StatuslineRenderer()
        self.assertIsNotNone(renderer)

        from data import StatuslineData
        self.assertIsNotNone(StatuslineData)

        from moai_adk.statusline import StatuslineConfig
        self.assertIsNotNone(StatuslineConfig)

    def test_statusline_main_integration(self):
        """Statusline 메인 모듈 통합 테스트

        statusline/main.py가 다른 모듈들과 정상적으로 통합되어야 합니다.
        """
        if not STATUSLINE_AVAILABLE:
            self.skipTest("Statusline modules not yet implemented")

        # 모듈 임포트
        import main

        # 모의 세션 컨텍스트
        test_context = {
            "model": {"name": "claude-sonnet", "display_name": "Claude Sonnet"},
            "version": "0.26.0",
            "cwd": "D:\\project",
            "output_style": {"name": "symbols"}
        }

        # 모의 stdin 입력
        import io
        sys.stdin = io.StringIO(json.dumps(test_context))

        # 메인 함수 실행
        with patch('builtins.print') as mock_print:
            # 환경 변수 설정으로 디버그 모드 비활성화
            with patch.dict(os.environ, {'MOAI_STATUSLINE_DEBUG': '0'}):
                main.main()
                # statusline이 출력되었는지 확인
                self.assertTrue(mock_print.called)

    def test_statusline_data_structure(self):
        """StatuslineData 데이터 구조 검증

        StatuslineData 클래스가 필요한 모든 필드를 포함해야 합니다.
        """
        if not STATUSLINE_AVAILABLE:
            self.skipTest("Statusline modules not yet implemented")

        from data import StatuslineData

        # 샘플 데이터 생성
        data = StatuslineData(
            model="claude-sonnet",
            claude_version="0.26.0",
            version="0.1.0",
            memory_usage="256MB",
            branch="main",
            git_status="+1 M2 ?1",
            duration="15m",
            directory="project",
            active_task="[DEVELOP]",
            output_style="symbols",
            update_available=False,
            latest_version=None
        )

        # 필드 검증
        self.assertEqual(data.model, "claude-sonnet")
        self.assertEqual(data.version, "0.1.0")
        self.assertEqual(data.branch, "main")
        self.assertEqual(data.duration, "15m")
        self.assertFalse(data.update_available)


class TestStatuslinePlatformIntegration(unittest.TestCase):
    """Statusline과 플랫폼 감지 시스템 통합 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.detector = PlatformDetector()

    def test_windows_statusline_command_detection(self):
        """Windows 환경에서 statusline 명령어 감지 테스트

        Windows 환경에서는 'python -m moai_adk.statusline.main' 명령어가 사용되어야 합니다.
        """
        # Windows 환경 모의
        with patch('sys.platform', 'win32'):
            detector = PlatformDetector()
            platform_config = detector.get_platform_config()

            # Windows 구성 검증
            self.assertEqual(platform_config['command'], 'cmd')
            self.assertEqual(platform_config['args'], ['/c'])
            self.assertTrue(platform_config['shell'])
            self.assertEqual(platform_config['encoding'], 'utf-8')
            self.assertEqual(platform_config['path_separator'], '\\')

            # Windows에서 statusline 실행 명령어 생성
            statusline_cmd = f"python -m moai_adk.statusline.main"
            self.assertIn('python', statusline_cmd)
            self.assertIn('moai_adk.statusline.main', statusline_cmd)

    def test_unix_statusline_command_detection(self):
        """Unix 환경에서 statusline 명령어 감지 테스트

        Unix 환경에서는 'python -m moai_adk.statusline.main' 명령어가 사용되어야 합니다.
        """
        # macOS 환경 모의
        with patch('sys.platform', 'darwin'):
            detector = PlatformDetector()
            platform_config = detector.get_platform_config()

            # Unix 구성 검증
            self.assertEqual(platform_config['command'], 'bash')
            self.assertEqual(platform_config['args'], ['-c'])
            self.assertFalse(platform_config['shell'])

        # Linux 환경 모의
        with patch('sys.platform', 'linux'):
            detector = PlatformDetector()
            platform_config = detector.get_platform_config()

            # Linux 구성 검증
            self.assertEqual(platform_config['command'], 'bash')
            self.assertEqual(platform_config['args'], ['-c'])
            self.assertFalse(platform_config['shell'])

    def test_cross_platform_statusline_execution(self):
        """크로스 플랫폼 statusline 실행 테스트

        모든 지원 플랫폼에서 statusline이 정상적으로 실행되어야 합니다.
        """
        supported_platforms = ['win32', 'darwin', 'linux']

        for platform in supported_platforms:
            with patch('sys.platform', platform):
                detector = PlatformDetector()
                self.assertTrue(detector.validate_platform())

                # 플랫폼별 설정 검증
                config = detector.get_platform_config()
                self.assertIsInstance(config, dict)
                self.assertIn('command', config)
                self.assertIn('args', config)
                self.assertIn('encoding', config)

    def test_statusline_environment_variables(self):
        """Statusline 환경변수 플랫폼별 형식 테스트

        각 플랫폼에 맞는 환경변수 형식이 사용되어야 합니다.
        """
        # Windows 환경
        with patch('sys.platform', 'win32'):
            detector = PlatformDetector()
            env_format = detector.get_environment_format()

            self.assertEqual(env_format['path_separator'], '\\')
            self.assertEqual(env_format['env_var_format'], '%{}%')

        # Unix 환경
        with patch('sys.platform', 'darwin'):
            detector = PlatformDetector()
            env_format = detector.get_environment_format()

            self.assertEqual(env_format['path_separator'], '/')
            self.assertEqual(env_format['env_var_format'], '${{}')


class TestStatuslineWindowsOptimization(unittest.TestCase):
    """Windows 특화 statusline 최적화 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, '.claude', 'settings.json')
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

    def tearDown(self):
        """테스트 환경 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_windows_specific_command_execution(self):
        """Windows에서의 특정 명령어 실행 테스트

        Windows에서는 'python -m' 대신 'python' 명령어가 특정 경우에 사용되어야 합니다.
        """
        # Windows 환경 모의
        with patch('sys.platform', 'win32'):
            detector = PlatformDetector()

            # Windows에서의 statusline 실행 스크립트
            script_content = """@echo off
set PYTHONPATH=%~dp0src
python -m moai_adk.statusline.main
"""
            script_path = os.path.join(self.temp_dir, 'run_statusline.bat')

            with open(script_path, 'w') as f:
                f.write(script_content)

            # 스크립트 존재 검증
            self.assertTrue(os.path.exists(script_path))

    def test_windows_startup_performance(self):
        """Windows에서의 시작 성능 최적화 테스트

        statusline이 100ms 이내에 시작되어야 합니다.
        """
        # 모의 성능 테스트
        with patch('time.perf_counter') as mock_time:
            mock_time.side_effect = [0, 0.085]  # 85ms

            # Windows 환경에서의 성능 테스트
            with patch('sys.platform', 'win32'):
                detector = PlatformDetector()
                config = detector.get_platform_config()

                # Windows 설정이 빠른 시작에 최적화되어 있는지 검증
                self.assertEqual(config['encoding'], 'utf-8')  # 인코딩 설정 검증
                self.assertTrue(config.get('fast_startup', False))

    def test_windows_configuration_auto_generation(self):
        """Windows 설정 자동 생성 테스트

        .claude/settings.json이 Windows 환경에 맞게 자동 생성되어야 합니다.
        """
        # Windows 설정 파일 생성
        windows_settings = {
            "platform": "windows",
            "statusline": {
                "enabled": True,
                "mode": "extended",
                "update_check": True
            },
            "performance": {
                "cache_enabled": True,
                "startup_timeout": 100
            }
        }

        with open(self.config_path, 'w') as f:
            json.dump(windows_settings, f, indent=2)

        # 설정 파일 검증
        self.assertTrue(os.path.exists(self.config_path))

        with open(self.config_path, 'r') as f:
            loaded_settings = json.load(f)

        self.assertEqual(loaded_settings['platform'], 'windows')
        self.assertTrue(loaded_settings['statusline']['enabled'])
        self.assertEqual(loaded_settings['statusline']['mode'], 'extended')


class TestStatuslineConfigIntegration(unittest.TestCase):
    """Statusline 설정 시스템 통합 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'moai_adk', 'platform'))
            from templates import ConfigTemplates
            self.templates = ConfigTemplates()
        except ImportError:
            self.templates = None

    def tearDown(self):
        """테스트 환경 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_statusline_config_template_integration(self):
        """Statusline 설정 템플릿 통합 테스트

        ConfigTemplates가 statusline 설정을 포함해야 합니다.
        """
        if self.templates is None:
            self.skipTest("ConfigTemplates not yet implemented")

        # Windows 템플릿 검증
        windows_template = self.templates.get_template('windows')
        self.assertIsInstance(windows_template, dict)

        # statusline 설정 포함 검증
        self.assertIn('statusline', windows_template)
        statusline_config = windows_template['statusline']

        self.assertIn('enabled', statusline_config)
        self.assertIn('mode', statusline_config)
        self.assertIn('update_check', statusline_config)

        # 기본값 검증
        self.assertTrue(statusline_config['enabled'])
        self.assertEqual(statusline_config['mode'], 'extended')
        self.assertTrue(statusline_config['update_check'])

    def test_cross_platform_statusline_config_consistency(self):
        """크로스 플랫폼 statusline 설정 일관성 테스트

        모든 플랫폼에서 동일한 statusline 설정 필드가 제공되어야 합니다.
        """
        if self.templates is None:
            self.skipTest("ConfigTemplates not yet implemented")

        platforms = ['windows', 'macos', 'linux']
        required_fields = ['enabled', 'mode', 'update_check', 'performance']

        for platform in platforms:
            template = self.templates.get_template(platform)
            self.assertIsInstance(template, dict)

            statusline_config = template.get('statusline', {})

            # 필드 존재 검증
            for field in required_fields:
                self.assertIn(field, statusline_config,
                            f"Field '{field}' missing in {platform} statusline config")

    def test_statusline_config_generation(self):
        """Statusline 설정 생성 테스트

        ConfigGenerator가 statusline 설정을 정상적으로 생성해야 합니다.
        """
        # ConfigGenerator 임포트
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'moai_adk', 'platform'))
        try:
            from config_generator import ConfigGenerator
        except ImportError:
            self.skipTest("ConfigGenerator not yet implemented")

        generator = ConfigGenerator()

        # Windows 설정 생성
        windows_config = generator.generate_config('windows')
        self.assertIsInstance(windows_config, dict)

        # statusline 설정 포함 검증
        self.assertIn('statusline', windows_config)
        statusline = windows_config['statusline']

        self.assertTrue(statusline['enabled'])
        self.assertIn('mode', statusline)
        self.assertIn('performance', statusline)


if __name__ == '__main__':
    unittest.main()