"""
Statusline Cleanup Feature Tests

TAG-STATUSLINE-CLEANUP-001: Test suite for statusline cleanup feature removals

Tests that validate the removal of time displays, [DEVELOP] indicators,
and duration/active_task fields from StatuslineData class.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# 테스트 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from moai_adk.statusline.data import StatuslineData
from moai_adk.statusline.renderer import StatuslineRenderer
from moai_adk.statusline.main import build_statusline_data


class TestStatuslineCleanupTimeDisplayRemoval(unittest.TestCase):
    """Test time display removal from statusline"""

    def setUp(self):
        """테스트 환경 설정"""
        self.renderer = StatuslineRenderer()
        self.test_data = StatuslineData(
            model="claude-sonnet",
            claude_version="0.26.0",
            version="0.1.0",
            memory_usage="256MB",
            branch="main",
            git_status="+1 M2 ?1",
            directory="project",
            output_style="symbols",
            update_available=False,
            latest_version=None
        )

    def test_time_display_not_in_powerline_render(self):
        """⏰ 타임 디스플레이가 Powerline 렌더링에 포함되지 않아야 함"""
        rendered = self.renderer._render_powerline(self.test_data)

        # 타임스탬프가 포함되지 않아야 함
        self.assertNotIn("⏰", rendered)
        self.assertNotIn("timestamp", rendered.lower())

        # 시간 형식도 포함되지 않아야 함
        self.assertNotIn(datetime.now().strftime("%H:%M:%S"), rendered)

    def test_time_display_not_in_extended_render(self):
        """⏰ 타임 디스플레이가 Extended 렌더링에 포함되지 않아야 함"""
        rendered = self.renderer._render_extended(self.test_data)

        # 타임스탬프가 포함되지 않아야 함
        self.assertNotIn("⏰", rendered)
        self.assertNotIn("timestamp", rendered.lower())

        # 날짜 형식도 포함되지 않아야 함
        self.assertNotIn(datetime.now().strftime("%m/%d %H:%M:%S"), rendered)

    def test_time_display_not_in_simple_powerline_render(self):
        """⏰ 타임 디스플레이가 Simple Powerline 렌더링에 포함되지 않아야 함"""
        rendered = self.renderer._render_simple_powerline(self.test_data)

        # 타임스탬프 형식 [HH:MM:SS] 이 포함되지 않아야 함
        import re
        timestamp_pattern = r'\[\d{2}:\d{2}:\d{2}\]'
        self.assertNotRegex(rendered, timestamp_pattern)

        # 시간 형식이 포함되지 않아야 함
        current_time = datetime.now().strftime("%H:%M:%S")
        self.assertNotIn(current_time, rendered)

    def test_time_display_colors_removed(self):
        """⏰ 타임 디스플레이 관련 색상이 제거되었는지 확인"""
        # bg_time, fg_time 색상이 제거되었는지 확인
        self.assertNotIn('bg_time', self.renderer.colors)
        self.assertNotIn('fg_time', self.renderer.colors)

        # 다른 색상들은 유지되어야 함
        self.assertIn('bg_model', self.renderer.colors)
        self.assertIn('bg_directory', self.renderer.colors)
        self.assertIn('bg_git', self.renderer.colors)

    def test_time_related_code_removed_from_renderer(self):
        """⏰ 렌더러에서 시간 관련 코드가 제거되었는지 확인"""
        # _render_powerline 메서드에서 타임스탬프 생성 코드 제거 확인
        import inspect
        source = inspect.getsource(self.renderer._render_powerline)

        # 타임스탬프 관련 코드가 없어야 함
        self.assertNotIn("datetime.datetime.now()", source)
        self.assertNotIn("timestamp", source.lower())
        self.assertNotIn("⏰", source)

        # 날짜 관련 코드도 없어야 함
        self.assertNotIn("strftime", source.lower())

    def test_extended_mode_no_timestamp_segment(self):
        """⏰ Extended 모드에서 타임스탬프 세그먼트가 없는지 확인"""
        rendered = self.renderer._render_extended(self.test_data)
        segments = rendered.split(" │ ")

        # 모든 세그먼트가 타임스탬프가 아니어야 함
        for segment in segments:
            self.assertNotIn("⏰", segment)
            self.assertNotIn("timestamp", segment.lower())


class TestStatuslineCleanupDevelopIndicatorRemoval(unittest.TestCase):
    """Test [DEVELOP] indicator removal from statusline"""

    def setUp(self):
        """테스트 환경 설정"""
        self.renderer = StatuslineRenderer()
        self.test_data = StatuslineData(
            model="claude-sonnet",
            claude_version="0.26.0",
            version="0.1.0",
            memory_usage="256MB",
            branch="main",
            git_status="+1 M2 ?1",
            directory="project",
            output_style="symbols",
            update_available=False,
            latest_version=None
        )

    def test_develop_indicator_not_in_powerline_render(self):
        """[DEVELOP] 인디케이터가 Powerline 렌더링에 포함되지 않아야 함"""
        rendered = self.renderer._render_powerline(self.test_data)

        # [DEVELOP] 텍스트가 포함되지 않아야 함
        self.assertNotIn("[DEVELOP]", rendered)
        self.assertNotIn("DEVELOP", rendered)

    def test_develop_indicator_not_in_extended_render(self):
        """[DEVELOP] 인디케이터가 Extended 렌더링에 포함되지 않아야 함"""
        rendered = self.renderer._render_extended(self.test_data)

        # [DEVELOP] 텍스트가 포함되지 않아야 함
        self.assertNotIn("[DEVELOP]", rendered)
        self.assertNotIn("DEVELOP", rendered)

    def test_develop_indicator_not_in_simple_powerline_render(self):
        """[DEVELOP] 인디케이터가 Simple Powerline 렌더링에 포함되지 않아야 함"""
        rendered = self.renderer._render_simple_powerline(self.test_data)

        # [DEVELOP] 텍스트가 포함되지 않아야 함
        self.assertNotIn("[DEVELOP]", rendered)
        self.assertNotIn("DEVELOP", rendered)

    
    def test_develop_indicator_removal_from_data_source(self):
        """[DEVELOP] 인디케이터가 데이터 소스에서 제거되는지 확인"""
        # 세션 컨텍스트 테스트
        session_context = {
            "model": {"name": "claude-sonnet"},
            "version": "0.26.0",
            "output_style": {"name": "symbols"},
            "cwd": "D:\\test\\project"
        }

        statusline = build_statusline_data(session_context)

        # [DEVELOP]가 최종 출력에 포함되지 않아야 함
        self.assertNotIn("[DEVELOP]", statusline)

    

class TestStatuslineCleanupDataFieldRemoval(unittest.TestCase):
    """Test duration and active_task field removal from StatuslineData"""

    def test_duration_field_removal(self):
        """⏱️ duration 필드가 StatuslineData 클래스에서 제거되었는지 확인"""
        # duration 필드가 데이터 클래스에 없어야 함
        import inspect
        source = inspect.getsource(StatuslineData)

        self.assertNotIn("duration: str", source)
        self.assertNotIn("duration", source.split("field")[0].split("Optional")[0])

    def test_active_task_field_removal(self):
        """💭 active_task 필드가 StatuslineData 클래스에서 제거되는지 확인"""
        # active_task 필드가 데이터 클래스에 없어야 함
        import inspect
        source = inspect.getsource(StatuslineData)

        self.assertNotIn("active_task: str", source)
        self.assertNotIn("active_task", source.split("field")[0].split("Optional")[0])

    def test_post_init_no_duration_default(self):
        """⏱️ __post_init__에서 duration 기본값 설정이 제거되었는지 확인"""
        # duration 필드가 없으므로 해당 처리도 없어야 함
        import inspect
        source = inspect.getsource(StatuslineData)

        self.assertNotIn("self.duration", source)
        self.assertNotIn("duration = ", source)

    def test_post_init_no_active_task_default(self):
        """💭 __post_init__에서 active_task 기본값 설정이 제거되는지 확인"""
        # active_task 필드가 없으므로 해당 처리도 없어야 함
        import inspect
        source = inspect.getsource(StatuslineData)

        self.assertNotIn("self.active_task", source)
        self.assertNotIn("active_task", source)

    def test_statusline_data_creation_without_removed_fields(self):
        """📝 StatuslineData 생성 시 제거된 필드 없이도 작동하는지 확인"""
        # duration과 active_task 필드 없이도 StatuslineData 생성 가능
        try:
            data = StatuslineData(
                model="claude-sonnet",
                claude_version="0.26.0",
                version="0.1.0",
                memory_usage="256MB",
                branch="main",
                git_status="+1 M2 ?1",
                directory="project",
                output_style="symbols",
                update_available=False,
                latest_version=None
            )

            # 필드 접근 테스트
            self.assertEqual(data.model, "claude-sonnet")
            self.assertEqual(data.branch, "main")
            self.assertEqual(data.directory, "project")
            self.assertEqual(data.output_style, "symbols")

            # 제거된 필드에 접근하려고 하면 AttributeError 발생해야 함
            with self.assertRaises(AttributeError):
                _ = data.duration

            with self.assertRaises(AttributeError):
                _ = data.active_task

        except Exception as e:
            self.fail(f"StatuslineData creation failed: {e}")

    def test_dataclass_fields_validation(self):
        """📝 데이터 클래스 필드 유효성 검증"""
        import dataclasses

        # StatuslineData 필드 목록 확인
        fields = dataclasses.fields(StatuslineData)
        field_names = [f.name for f in fields]

        # 제거된 필드가 없어야 함
        self.assertNotIn("duration", field_names)
        self.assertNotIn("active_task", field_names)

        # 필수 필드는 유지되어야 함
        required_fields = ["model", "claude_version", "version", "memory_usage",
                          "branch", "git_status", "directory", "output_style"]
        for field in required_fields:
            self.assertIn(field, field_names)


class TestStatuslineCleanupDevelopModeConfigRemoval(unittest.TestCase):
    """Test develop mode configuration removal from main.py"""

    
    def test_build_statusline_data_no_develop_inclusion(self):
        """🔧 build_statusline_data가 [DEVELOP]를 포함하지 않는지 확인"""
        # 세션 컨텍스트 테스트
        session_context = {
            "model": {"name": "claude-sonnet"},
            "version": "0.26.0",
            "output_style": {"name": "symbols"},
            "cwd": "D:\\test\\project"
        }

        statusline = build_statusline_data(session_context)

        # 최종 결과물에 [DEVELOP]가 포함되지 않아야 함
        self.assertNotIn("[DEVELOP]", statusline)

    def test_main_py_no_develop_hardcoding(self):
        """🔧 main.py에 [DEVELOP] 하드코딩이 제거되었는지 확인"""
        import inspect

        # main.py 소스 코드 확인
        main_source = inspect.getsource(build_statusline_data)

        # [DEVELOP] 하드코딩이 없어야 함
        self.assertNotIn('"[DEVELOP]"', main_source)
        self.assertNotIn("'[DEVELOP]'", main_source)

    def test_develop_mode_config_removal_from_context_building(self):
        """🔧 컨텍스트 빌딩에서 develop 모드 설정 제거 확인"""
        # build_statusline_data 함수에서 duration 설정 확인
        import inspect
        source = inspect.getsource(build_statusline_data)

        # duration 설정 코드가 없어야 함
        self.assertNotIn("duration=", source)

        # safe_collect_duration 호출이 없어야 함
        self.assertNotIn("safe_collect_duration", source)


class TestStatuslineCleanupEssentialFunctionality(unittest.TestCase):
    """Test that essential functionality is preserved after cleanup"""

    def setUp(self):
        """테스트 환경 설정"""
        self.renderer = StatuslineRenderer()
        self.test_data = StatuslineData(
            model="claude-sonnet",
            claude_version="0.26.0",
            version="0.1.0",
            memory_usage="256MB",
            branch="main",
            git_status="+1 M2 ?1",
            directory="project",
            output_style="symbols",
            update_available=False,
            latest_version=None
        )

    def test_essential_information_preserved(self):
        """📊 필수 정보가 청소 후에도 유지되는지 확인"""
        # Powerline 렌더링
        rendered = self.renderer._render_powerline(self.test_data)

        # 필수 정보는 여전히 표시되어야 함
        self.assertIn("🤖", rendered)  # 모델 정보
        self.assertIn("📁", rendered)  # 디렉토리 정보
        self.assertIn("🔀", rendered)  # Git 정보

        # 모델 이름 확인
        self.assertIn("sonnet", rendered.lower())

        # 디렉토리 이름 확인
        self.assertIn("project", rendered.lower())

    def test_rendering_modes_still_work(self):
        """🎨 모든 렌더링 모드가 여전히 작동하는지 확인"""
        modes = ["powerline", "extended", "minimal", "simple"]

        for mode in modes:
            with self.subTest(mode=mode):
                if mode == "powerline":
                    rendered = self.renderer._render_powerline(self.test_data)
                elif mode == "extended":
                    rendered = self.renderer._render_extended(self.test_data)
                elif mode == "minimal":
                    rendered = self.renderer._render_minimal(self.test_data)
                elif mode == "simple":
                    rendered = self.renderer._render_simple_powerline(self.test_data)

                # 각 모드에서 유효한 문자열 반환
                self.assertIsInstance(rendered, str)
                self.assertGreater(len(rendered), 0)

    def test_windows_korean_emoji_support(self):
        """🌐 Windows 한국어 이모지 지원이 유지되는지 확인"""
        # Windows 환경에서 이모지 지원 확인
        with patch('sys.platform', 'win32'):
            with patch('os.environ.get', side_effect=lambda key, default=None: {
                'WT_SESSION': '1',  # Windows Terminal 지시
                'TERM_PROGRAM': None,
                'MOAI_STATUSLINE_FORCE_UNICODE': '1'
            }.get(key, default)):

                # Windows에서도 이모지가 포함된 렌더링 작동
                rendered = self.renderer._render_powerline(self.test_data)

                # 이모지가 포함되어 있어야 함
                self.assertIn("🤖", rendered)
                self.assertIn("📁", rendered)
                self.assertIn("🔀", rendered)

    def test_performance_improvement_measurement(self):
        """⚡ 성능 개선 측정"""
        import time

        # 청소 전후 성능 비교를 위한 기준 측정
        start_time = time.perf_counter()

        # 여러 번 렌더링하여 성능 측정
        for _ in range(100):
            self.renderer._render_powerline(self.test_data)

        end_time = time.perf_counter()
        render_time = (end_time - start_time) * 1000  # ms로 변환

        # 100번 렌더링이 500ms 이내 완료되어야 함 (성능 개선 확인)
        self.assertLess(render_time, 500,
                        f"100 renders took {render_time:.2f}ms, expected <500ms")


if __name__ == '__main__':
    unittest.main()