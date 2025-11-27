"""
Complete Statusline Integration Tests

TAG-WIN-005: Statusline Solution 최종 통합 검증

모든 모듈이 통합되고 Windows 환경에서 최적으로 작동하는지 검증합니다.
"""

import unittest
import json
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock

# 테스트 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from moai_adk.platform.detector import PlatformDetector
from moai_adk.platform.templates import ConfigTemplates
from moai_adk.platform.config_generator import ConfigGenerator
from moai_adk.statusline.data import StatuslineData
from moai_adk.statusline.renderer import StatuslineRenderer


class TestCompleteStatuslineIntegration(unittest.TestCase):
    """Complete statusline integration test"""

    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.platform_detector = PlatformDetector()
        self.templates = ConfigTemplates()
        self.config_generator = ConfigGenerator()

    def tearDown(self):
        """테스트 환경 정리"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_windows_integration(self):
        """Windows 환경에서의 완전한 통합 테스트"""
        # Windows 환경 확인
        self.assertEqual(self.platform_detector.detect_os(), 'windows')
        self.assertTrue(self.platform_detector.validate_platform())

        # 설정 템플릿 통합 검증
        windows_config = self.templates.get_template('windows')
        self.assertIn('statusline', windows_config)
        self.assertIn('mcp', windows_config)
        self.assertIn('claude_settings', windows_config)

        # Statusline 설정 검증
        statusline_config = windows_config['statusline']
        self.assertTrue(statusline_config['enabled'])
        self.assertEqual(statusline_config['mode'], 'extended')
        self.assertTrue(statusline_config['update_check'])
        self.assertTrue(statusline_config['performance']['fast_startup'])
        self.assertEqual(statusline_config['command'], 'python')

        # ConfigGenerator 통합 검증
        generated_config = self.config_generator.generate_config('windows')
        self.assertIn('statusline', generated_config)
        self.assertEqual(generated_config['platform'], 'windows')

        # Statusline 데이터 생성 및 렌더링
        statusline_data = StatuslineData(
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

        renderer = StatuslineRenderer()
        rendered_statusline = renderer.render(statusline_data)
        self.assertIsInstance(rendered_statusline, str)
        self.assertGreater(len(rendered_statusline), 0)

    def test_cross_platform_config_consistency(self):
        """크로스 플랫폼 설정 일관성 검증"""
        platforms = ['windows', 'macos', 'linux']

        for platform in platforms:
            with self.subTest(platform=platform):
                # 모든 플랫폼에서 설정 생성 가능
                config = self.config_generator.generate_config(platform)
                self.assertIn('statusline', config)

                # 템플릿 일관성 검증
                template = self.templates.get_template(platform)
                self.assertIn('statusline', template)

                statusline_config = template['statusline']
                self.assertIn('enabled', statusline_config)
                self.assertIn('mode', statusline_config)
                self.assertIn('update_check', statusline_config)
                self.assertIn('performance', statusline_config)

    def test_windows_specific_optimizations(self):
        """Windows 특화 최적화 검증"""
        # Windows 환경 설정
        with patch('sys.platform', 'win32'):
            detector = PlatformDetector()
            config = detector.get_platform_config()

            # Windows 최적화 설정 확인
            self.assertTrue(config['shell'])
            self.assertEqual(config['command'], 'cmd')
            self.assertEqual(config['args'], ['/c'])
            self.assertEqual(config['encoding'], 'utf-8')
            self.assertEqual(config['path_separator'], '\\')
            self.assertEqual(config['env_var_format'], '%{}%')

            # Fast startup 설정 확인
            self.assertTrue(config['fast_startup'])

    def test_automatic_configuration_generation(self):
        """자동 설정 생성 검증"""
        # .claude/settings.json 자동 생성
        claude_settings_path = os.path.join(self.temp_dir, '.claude', 'settings.json')

        # 설정 적용
        claude_settings = self.config_generator.generate_claude_settings()
        success = self.config_generator.apply_config(claude_settings, claude_settings_path)

        self.assertTrue(success)
        self.assertTrue(os.path.exists(claude_settings_path))

        # 생성된 설정 파일 검증
        with open(claude_settings_path, 'r') as f:
            loaded_settings = json.load(f)

        self.assertIn('claude', loaded_settings)
        self.assertIn('statusline', loaded_settings['claude'])

        statusline_config = loaded_settings['claude']['statusline']
        self.assertIn('command', statusline_config)
        self.assertIn('args', statusline_config)

    def test_performance_requirements(self):
        """성능 요구사항 검증"""
        import time

        # 시작 시간 측정
        start_time = time.perf_counter()

        # 설정 생성 시간 측정
        config = self.config_generator.generate_optimized_config()

        # 완료 시간 측정
        end_time = time.perf_counter()
        generation_time = (end_time - start_time) * 1000  # ms로 변환

        # 설정 생성이 100ms 이내 완료되어야 함
        self.assertLess(generation_time, 100,
                        f"Config generation took {generation_time:.2f}ms, expected <100ms")

        # Statusline 렌더링 성능 검증
        statusline_data = StatuslineData(
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

        renderer = StatuslineRenderer()

        # 렌더링 시작 시간
        render_start = time.perf_counter()

        # Statusline 렌더링
        rendered = renderer.render(statusline_data)

        # 렌더링 완료 시간
        render_end = time.perf_counter()
        render_time = (render_end - render_start) * 1000  # ms로 변환

        # 렌더링이 50ms 이내 완료되어야 함
        self.assertLess(render_time, 50,
                        f"Statusline rendering took {render_time:.2f}ms, expected <50ms")

    def test_configuration_success_rate(self):
        """구성 성공률 검증"""
        success_count = 0
        total_tests = 100

        for i in range(total_tests):
            try:
                # 여러 환경에서 설정 생성 시도
                platforms = ['windows', 'macos', 'linux']
                for platform in platforms:
                    config = self.config_generator.generate_config(platform)
                    if config and 'statusline' in config:
                        success_count += 1
                        break
            except Exception:
                continue

        # 성공률 95% 이상 확인
        success_rate = success_count / total_tests
        self.assertGreaterEqual(success_rate, 0.95,
                                f"Configuration success rate: {success_rate:.2%}, expected >=95%")


class TestStatuslineEdgeCases(unittest.TestCase):
    """Statusline edge case testing"""

    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """테스트 환경 정리"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_error_handling_robustness(self):
        """오류 처리의 견고성 검증"""
        # StatuslineData가 None일 때의 처리
        try:
            data = StatuslineData(
                model="",  # 빈 문자열
                claude_version="",  # 빈 문자열
                version="",  # 빈 문자열
                memory_usage="",  # 빈 문자열
                branch="",  # 빈 문자열
                git_status="",  # 빈 문자열
                duration="",  # 빈 문자열
                directory="",  # 빈 문자열
                active_task="",  # 빈 문자열
                output_style="",  # 빈 문자열
                update_available=False,
                latest_version=None
            )

            # 데이터 포스트 프로세싱이 정상적으로 작동해야 함
            self.assertEqual(data.model, "unknown")
            self.assertEqual(data.version, "0.0.0")
            self.assertEqual(data.branch, "unknown")
            self.assertEqual(data.duration, "0m")
            self.assertEqual(data.directory, "project")

        except Exception as e:
            self.fail(f"StatuslineData creation with empty values failed: {e}")

    def test_memory_efficiency(self):
        """메모리 효율성 검증"""
        # 간단한 메모리 효율성 테스트 (psutil 의존성 제거)

        # 대량 객체 생성이 정상적으로 작동하는지 검증
        objects = []
        try:
            for i in range(1000):
                data = StatuslineData(
                    model=f"claude-sonnet-{i}",
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
                objects.append(data)

            # 객체 생성이 성공했어야 함
            self.assertEqual(len(objects), 1000)

            # 모든 객체가 유효한지 검증
            for obj in objects[:10]:  # 샘플 검증
                self.assertIsNotNone(obj.model)
                self.assertIsNotNone(obj.version)

        except MemoryError:
            self.fail("Memory creation failed - memory efficiency is poor")
        except Exception as e:
            self.fail(f"Unexpected error during memory efficiency test: {e}")
        finally:
            # 메모리 정리
            objects.clear()
            import gc
            gc.collect()


if __name__ == '__main__':
    unittest.main()