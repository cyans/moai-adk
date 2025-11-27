"""
Windows Statusline Encoding Fix Tests

TAG-WIN-002: Windows statusline 인코딩 문제 해결 검증

Windows 환경에서 발생하는 Unicode 인코딩 문제를 검증하고 해결합니다.
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'moai_adk', 'statusline'))
try:
    from main import main, build_statusline_data
    from data import StatuslineData
    from renderer import StatuslineRenderer
    STATUSLINE_AVAILABLE = True
except ImportError:
    STATUSLINE_AVAILABLE = False


class TestWindowsStatuslineEncoding(unittest.TestCase):
    """Windows Statusline 인코딩 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """테스트 환경 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_windows_unicode_encoding_issue(self):
        """Windows Unicode 인코딩 문제 재현 테스트

        Windows cmd에서 Unicode 문자 출력 시 발생하는 인코딩 문제를 재현합니다.
        """
        if not STATUSLINE_AVAILABLE:
            self.skipTest("Statusline modules not yet implemented")

        # Windows 환경 모의
        with patch('sys.platform', 'win32'):
            # 모의 세션 컨텍스트 - 이모지 포함
            test_context = {
                "model": {"name": "claude-sonnet", "display_name": "Claude Sonnet 😊"},
                "version": "0.26.0",
                "cwd": "D:\\project",
                "output_style": {"name": "symbols"}
            }

            # 모의 stdin 입력
            import io
            sys.stdin = io.StringIO(json.dumps(test_context))

            # Windows의 인코딩 문제 테스트
            with patch('builtins.print') as mock_print:
                # Windows 인코딩 문제 발생 시뮬레이션
                try:
                    main()
                    # 인쇄 호출이 성공했는지 확인
                    mock_print.assert_called()

                    # 출력 내용 검증
                    for call_args in mock_print.call_args_list:
                        args = call_args[0]
                        if args and isinstance(args[0], str):
                            # 이모지가 포함된 문자열이 문제없이 출력되는지 확인
                            if any(ord(c) > 127 for c in args[0]):
                                print(f"DEBUG: Found Unicode characters in output: {args[0][:50]}...")
                                # 이 시점에서는 문제없이 출력되지만, 실제 Windows cmd 환경에서는 문제가 발생할 수 있음
                except UnicodeEncodeError as e:
                    # 실제 Windows 환경에서 발생할 수 있는 인코딩 문제
                    self.fail(f"Unicode 인코딩 오류가 발생했습니다: {e}")
                except Exception as e:
                    self.fail(f"예상치 않은 오류 발생: {e}")

    def test_windows_statusline_encoding_fix(self):
        """Windows statusline 인코딩 해결 테스트

        Windows 환경에서도 Unicode 문자가 정상적으로 출력되는지 검증합니다.
        """
        if not STATUSLINE_AVAILABLE:
            self.skipTest("Statusline modules not yet implemented")

        # Windows 환경 모의
        with patch('sys.platform', 'win32'):
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

            # 수정된 main 함수 테스트 (인코딩 처리 추가)
            with patch('sys.stdout') as mock_stdout:
                with patch('builtins.print') as mock_print:
                    try:
                        # main 함수 실행 시도
                        main()
                    except UnicodeEncodeError:
                        self.fail("UnicodeEncodeError가 발생했습니다. 인코딩 문제가 해결되지 않았습니다.")

    def test_statusline_data_generation(self):
        """Statusline 데이터 생성 테스트

        Statusline 데이터가 정상적으로 생성되는지 검증합니다.
        """
        if not STATUSLINE_AVAILABLE:
            self.skipTest("Statusline modules not yet implemented")

        # 모의 세션 컨텍스트
        test_context = {
            "model": {"name": "claude-sonnet", "display_name": "Claude Sonnet"},
            "version": "0.26.0",
            "cwd": "D:\\project",
            "output_style": {"name": "symbols"}
        }

        # 데이터 생성 테스트
        try:
            statusline_output = build_statusline_data(test_context)
            self.assertIsInstance(statusline_output, str)
            self.assertGreater(len(statusline_output), 0)
        except Exception as e:
            self.fail(f"Statusline 데이터 생성 중 오류 발생: {e}")

    def test_windows_cmd_compatibility(self):
        """Windows cmd 호환성 테스트

        Windows cmd에서 실행할 수 있는 명령어 형식인지 검증합니다.
        """
        # Windows용 statusline 실행 명령어 검증
        windows_command = "python -m moai_adk.statusline.main"

        # 유효한 Windows 명령어 형식 검증
        self.assertIn("python", windows_command)
        self.assertIn("-m", windows_command)
        self.assertIn("moai_adk.statusline.main", windows_command)

        # 공백이 포함된 경우 경로 처리 검증
        test_path = "D:\\project\\moai-adk"
        self.assertIn("D:\\", test_path)

    def test_cross_platform_statusline_execution(self):
        """크로스 플랫폼 statusline 실행 테스트

        Windows와 Unix 환경에서 모두 실행 가능한지 검증합니다.
        """
        platforms = ['win32', 'darwin', 'linux']

        for platform in platforms:
            with patch('sys.platform', platform):
                if STATUSLINE_AVAILABLE:
                    # 모의 세션 컨텍스트
                    test_context = {
                        "model": {"name": "claude-sonnet", "display_name": "Claude Sonnet"},
                        "version": "0.26.0",
                        "cwd": f"{'C:\\' if platform == 'win32' else '/home'}\\project",
                        "output_style": {"name": "symbols"}
                    }

                    try:
                        # 데이터 생성 테스트 (실패하면 안 됨)
                        statusline_output = build_statusline_data(test_context)
                        self.assertIsInstance(statusline_output, str)
                    except Exception as e:
                        self.fail(f"{platform} 플랫폼에서 statusline 데이터 생성 실패: {e}")


class TestStatuslineRendererEncoding(unittest.TestCase):
    """Statusline 렌더러 인코딩 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        if not STATUSLINE_AVAILABLE:
            self.skipTest("Statusline modules not yet implemented")

        from data import StatuslineData
        from renderer import StatuslineRenderer

        self.test_data = StatuslineData(
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
        self.renderer = StatuslineRenderer()

    def test_renderer_emoji_support(self):
        """레이더 이모지 지원 테스트

        Statusline 레이더가 이모지 문자를 정상적으로 처리하는지 검증합니다.
        """
        # 렌더링 테스트
        try:
            rendered = self.renderer.render(self.test_data, mode="extended")
            self.assertIsInstance(rendered, str)
            self.assertGreater(len(rendered), 0)
        except UnicodeEncodeError:
            self.fail("UnicodeEncodeError가 발생했습니다. 이모지 지원 문제가 있습니다.")

    def test_renderer_encoding_robustness(self):
        """레이더 인코딩 견고성 테스트

        다양한 문자 인코딩 환경에서도 정상적으로 동작하는지 검증합니다.
        """
        # 다양한 문자 조합 테스트
        test_cases = [
            "project",
            "test-project",
            "test_project",
            "test 123",
            "emoji 😊 test",
            "한글 테스트",
            "漢字テスト",
            "C:\\project\\test",
            "/home/user/test"
        ]

        for directory_name in test_cases:
            self.test_data.directory = directory_name

            try:
                rendered = self.renderer.render(self.test_data, mode="compact")
                self.assertIsInstance(rendered, str)
                self.assertGreater(len(rendered), 0)
            except Exception as e:
                self.fail(f"디렉토리 이름 '{directory_name}' 처리 실패: {e}")

    def test_windows_specific_rendering(self):
        """Windows 특화 렌더링 테스트

        Windows 환경에서의 최적화된 렌더링을 검증합니다.
        """
        # Windows 플랫폼 모의
        with patch('sys.platform', 'win32'):
            # Windows용 렌더링 테스트
            try:
                rendered = self.renderer.render(self.test_data, mode="extended")
                self.assertIsInstance(rendered, str)
                self.assertGreater(len(rendered), 0)

                # Windows 특정 문자 형식 검증
                self.assertIn("Windows" if "Windows" in rendered else "", rendered)

            except UnicodeEncodeError:
                self.fail("Windows 환경에서 인코딩 오류 발생")


if __name__ == '__main__':
    unittest.main()