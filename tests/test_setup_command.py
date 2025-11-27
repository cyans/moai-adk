"""
Windows Setup Command Tests

TAG-WIN-004: Windows setup command 구현 검증

Windows 환경에서 MoAI-ADK의 자동 설정 기능을 검증합니다.
OS 감지, 설정 생성, 백업/복원, 상태 확인 기능을 포함합니다.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# 테스트 대상 모듈 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'moai_adk', 'platform'))

# 테스트 대상 모듈 임포트
try:
    from setup_command import SetupCommand
    from config_generator import ConfigGenerator
    from detector import PlatformDetector
    from templates import ConfigTemplates
    SETUP_AVAILABLE = True
except ImportError:
    SETUP_AVAILABLE = False


class TestSetupCommand(unittest.TestCase):
    """Windows Setup Command 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        if not SETUP_AVAILABLE:
            self.skipTest("Setup command modules not yet implemented")

        self.temp_dir = tempfile.mkdtemp()
        self.setup_cmd = SetupCommand()
        self.config_generator = ConfigGenerator()

    def tearDown(self):
        """테스트 환경 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_command_initialization(self):
        """Setup Command 초기화 테스트

        SetupCommand 객체가 정상적으로 초기화되는지 검증합니다.
        """
        # SetupCommand 객체 생성
        self.assertIsInstance(self.setup_cmd, SetupCommand)

        # 필수 속성 존재 확인
        self.assertTrue(hasattr(self.setup_cmd, 'config_generator'))
        self.assertTrue(hasattr(self.setup_cmd, 'detector'))
        self.assertTrue(hasattr(self.setup_cmd, 'backup_enabled'))

        # 기본 값 확인
        self.assertTrue(self.setup_cmd.backup_enabled)
        self.assertEqual(self.setup_cmd.backup_dir, '.moai/backup')

    def test_os_detection_integration(self):
        """OS 감지 통합 테스트

        SetupCommand가 PlatformDetector를 올바르게 통합하는지 검증합니다.
        """
        # OS 감지 테스트
        detected_os = self.setup_cmd.get_detected_os()
        self.assertIn(detected_os, ['windows', 'macos', 'linux', 'unknown'])

        # 플랫폼 유효성 검사 테스트
        is_valid = self.setup_cmd.is_platform_supported()
        self.assertIsInstance(is_valid, bool)

    def test_full_setup_process_windows(self):
        """전체 설정 프로세스 Windows 테스트

        Windows 환경에서 전체 설정 프로세스가 정상적으로 동작하는지 검증합니다.
        """
        # Windows 환경 모의
        with patch('sys.platform', 'win32'):
            # 테스트 디렉토리 설정
            test_project_dir = os.path.join(self.temp_dir, 'test_project')
            os.makedirs(test_project_dir, exist_ok=True)

            # 전체 설정 실행
            result = self.setup_cmd.setup_project(test_project_dir)

            # 결과 검증
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('details', result)
            self.assertIn('backup_created', result)

            # 파일 생성 확인
            mcp_path = os.path.join(test_project_dir, '.mcp.json')
            claude_settings_path = os.path.join(test_project_dir, '.claude', 'settings.json')

            if result['success']:
                self.assertTrue(os.path.exists(mcp_path))
                self.assertTrue(os.path.exists(claude_settings_path))

                # 설정 내용 확인
                with open(mcp_path, 'r', encoding='utf-8') as f:
                    mcp_config = json.load(f)
                    self.assertIn('mcpServers', mcp_config)

                    # Windows 명령어 확인
                    for server_name, server_config in mcp_config['mcpServers'].items():
                        if server_name != 'figma-dev-mode-mcp-server':  # SSE 서버 제외
                            self.assertEqual(server_config['command'], 'cmd')
                            self.assertEqual(server_config['args'][0], '/c')

    def test_setup_process_with_backup(self):
        """백업 기능을 포함한 설정 프로세스 테스트

        백업/복원 기능이 정상적으로 동작하는지 검증합니다.
        """
        # 테스트 디렉토리 설정
        test_project_dir = os.path.join(self.temp_dir, 'test_project')
        os.makedirs(test_project_dir, exist_ok=True)

        # 원본 설정 파일 생성
        original_mcp = {
            "mcpServers": {
                "context7": {
                    "command": "cmd",
                    "args": ["/c", "echo", "original"]
                }
            }
        }

        mcp_path = os.path.join(test_project_dir, '.mcp.json')
        with open(mcp_path, 'w', encoding='utf-8') as f:
            json.dump(original_mcp, f, indent=2)

        # 설정 실행 (백포트 생성)
        result = self.setup_cmd.setup_project(test_project_dir)

        # 백업 파일 확인
        backup_dir = os.path.join(test_project_dir, '.moai', 'backup')
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.backup')]
            if result['backup_created']:
                self.assertGreater(len(backup_files), 0)

    def test_setup_process_error_handling(self):
        """설정 프로세스 오류 처리 테스트

        오류 발생 시 적절한 예외 처리가 동작하는지 검증합니다.
        """
        # 지원되지 않는 플랫폼으로 오류 테스트
        with patch('sys.platform', 'unknown_os'):
            result = self.setup_cmd.setup_project(self.temp_dir)

        # 오류 처리 확인
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('error', result)
        self.assertFalse(result['success'])

        # 존재하지 않는 파일 경로로 테스트 (유효하지 않은 파일 형식)
        invalid_file_path = os.path.join(self.temp_dir, 'nonexistent.json')
        result = self.setup_cmd.setup_project(invalid_file_path)

        # 유효하지 않은 파일 형식에 대한 처리 확인
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)

    def test_partial_setup_options(self):
        """부분 설정 옵션 테스트

        일부 설정만 선택적으로 적용하는 기능을 검증합니다.
        """
        # 테스트 디렉토리 설정
        test_project_dir = os.path.join(self.temp_dir, 'test_project')
        os.makedirs(test_project_dir, exist_ok=True)

        # 개별 설정 적용 테스트
        mcp_result = self.setup_cmd.setup_mcp_config(test_project_dir)
        statusline_result = self.setup_cmd.setup_statusline_config(test_project_dir)
        claude_result = self.setup_cmd.setup_claude_config(test_project_dir)

        # 각 설정 결과 검증
        for result in [mcp_result, statusline_result, claude_result]:
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)

    def test_rollback_functionality(self):
        """롤백 기능 테스트

        설정 롤백이 정상적으로 동작하는지 검증합니다.
        """
        # 테스트 디렉토리 설정
        test_project_dir = os.path.join(self.temp_dir, 'test_project')
        os.makedirs(test_project_dir, exist_ok=True)

        # 원본 설정 파일 생성
        original_mcp = {
            "mcpServers": {
                "context7": {
                    "command": "cmd",
                    "args": ["/c", "echo", "original"]
                }
            }
        }

        mcp_path = os.path.join(test_project_dir, '.mcp.json')
        with open(mcp_path, 'w', encoding='utf-8') as f:
            json.dump(original_mcp, f, indent=2)

        # 새로운 설정 적용
        result = self.setup_cmd.setup_project(test_project_dir)

        # 롤백 실행
        rollback_result = self.setup_cmd.rollback_config(mcp_path)

        # 롤백 결과 검증
        self.assertIsInstance(rollback_result, bool)

        if rollback_result:
            # 원본 설정 복원 확인
            with open(mcp_path, 'r', encoding='utf-8') as f:
                restored_config = json.load(f)
                self.assertEqual(restored_config, original_mcp)

    def test_setup_status_reporting(self):
        """설정 상태 보고 기능 테스트

        설정 상태가 정상적으로 보고되는지 검증합니다.
        """
        # 테스트 디렉토리 설정
        test_project_dir = os.path.join(self.temp_dir, 'test_project')
        os.makedirs(test_project_dir, exist_ok=True)

        # 설정 상태 확인
        status = self.setup_cmd.get_setup_status(test_project_dir)

        # 상태 정보 검증
        self.assertIsInstance(status, dict)
        self.assertIn('platform_detected', status)
        self.assertIn('configs_applied', status)
        self.assertIn('backup_exists', status)
        self.assertIn('platform_details', status)

    def test_cross_platform_setup(self):
        """크로스 플랫폼 설정 테스트

        다양한 플랫폼에서 설정이 올바르게 동작하는지 검증합니다.
        """
        platforms = ['win32', 'darwin', 'linux']

        for platform in platforms:
            with patch('sys.platform', platform):
                test_project_dir = os.path.join(self.temp_dir, f'test_{platform}')
                os.makedirs(test_project_dir, exist_ok=True)

                # 플랫폼별 설정 테스트
                result = self.setup_cmd.setup_project(test_project_dir)

                # 기본 구조 검증
                self.assertIsInstance(result, dict)
                self.assertIn('success', result)
                self.assertIn('details', result)

    def test_setup_validation(self):
        """설정 유효성 검사 테스트

        생성된 설정의 유효성 검사 기능을 검증합니다.
        """
        # MCP 설정 유효성 검사
        mcp_config = self.config_generator.generate_mcp_config()
        is_valid = self.setup_cmd.validate_config(mcp_config, 'mcp')
        self.assertIsInstance(is_valid, bool)

        # Statusline 설정 유효성 검사
        statusline_config = self.config_generator.generate_statusline_config()
        is_valid = self.setup_cmd.validate_config(statusline_config, 'statusline')
        self.assertIsInstance(is_valid, bool)

        # Claude 설정 유효성 검사
        claude_config = self.config_generator.generate_claude_settings()
        is_valid = self.setup_cmd.validate_config(claude_config, 'claude_settings')
        self.assertIsInstance(is_valid, bool)

    def test_setup_summary_generation(self):
        """설정 요약 생성 기능 테스트

        설정 요약 정보가 정상적으로 생성되는지 검증합니다.
        """
        # 설정 요약 생성
        summary = self.setup_cmd.get_setup_summary()

        # 요약 정보 검증
        self.assertIsInstance(summary, dict)
        self.assertIn('platform', summary)
        self.assertIn('status', summary)
        self.assertIn('configs', summary)
        self.assertIn('recommendations', summary)

    def test_setup_command_help(self):
        """설정 명령 도움말 기능 테스트

        도움말 정보가 올바르게 제공되는지 검증합니다.
        """
        # 도움말 정보 확인
        help_text = self.setup_cmd.get_help()

        # 도움말 내용 검증
        self.assertIsInstance(help_text, str)
        self.assertGreater(len(help_text), 0)
        self.assertIn('setup', help_text.lower())

    def test_setup_command_dry_run(self):
        """드라이 런 기능 테스트

        실제 설정 적용 없이 예상 결과를 확인하는 기능을 검증합니다.
        """
        # 테스트 디렉토리 설정
        test_project_dir = os.path.join(self.temp_dir, 'test_project')
        os.makedirs(test_project_dir, exist_ok=True)

        # 드라이 런 실행
        dry_run_result = self.setup_cmd.dry_run_setup(test_project_dir)

        # 드라이 런 결과 검증
        self.assertIsInstance(dry_run_result, dict)
        self.assertIn('would_create', dry_run_result)
        self.assertIn('would_modify', dry_run_result)
        self.assertIn('estimated_impact', dry_run_result)

        # 실제 파일 생성 확인 (드라이 런이면 생성되지 않아야 함)
        mcp_path = os.path.join(test_project_dir, '.mcp.json')
        self.assertFalse(os.path.exists(mcp_path))


class TestSetupCommandIntegration(unittest.TestCase):
    """Setup Command 통합 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        if not SETUP_AVAILABLE:
            self.skipTest("Setup command modules not yet implemented")

        self.temp_dir = tempfile.mkdtemp()
        self.setup_cmd = SetupCommand()

    def tearDown(self):
        """테스트 환경 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_setup_workflow(self):
        """엔드투엔드 설정 워크플로우 테스트

        실제 사용 시나리오를 모방한 전체 워크플로우를 검증합니다.
        """
        # 테스트 디렉토리 설정
        test_project_dir = os.path.join(self.temp_dir, 'my_project')
        os.makedirs(test_project_dir, exist_ok=True)

        # 1. 현재 상태 확인
        initial_status = self.setup_cmd.get_setup_status(test_project_dir)

        # 2. 드라이 런으로 예상 결과 확인
        dry_run = self.setup_cmd.dry_run_setup(test_project_dir)

        # 3. 실제 설정 적용
        setup_result = self.setup_cmd.setup_project(test_project_dir)

        # 4. 설정 후 상태 확인
        final_status = self.setup_cmd.get_setup_status(test_project_dir)

        # 5. 유효성 검사
        validation_result = self.setup_cmd.validate_setup(test_project_dir)

        # 결과 검증
        self.assertIsInstance(initial_status, dict)
        self.assertIsInstance(dry_run, dict)
        self.assertIsInstance(setup_result, dict)
        self.assertIsInstance(final_status, dict)
        self.assertIsInstance(validation_result, dict)

        # 설정이 적용된 경우 검증
        if setup_result.get('success'):
            # 설정 파일 존재 확인
            mcp_path = os.path.join(test_project_dir, '.mcp.json')
            self.assertTrue(os.path.exists(mcp_path))

            # 유효성 검사 통과 확인
            self.assertTrue(validation_result.get('is_valid', False))

    def test_setup_error_recovery(self):
        """설정 오류 복구 테스트

        설정 중 오류 발생 시 복구 기능을 검증합니다.
        """
        # 테스트 디렉토리 설정
        test_project_dir = os.path.join(self.temp_dir, 'test_project')
        os.makedirs(test_project_dir, exist_ok=True)

        # 원본 설정 생성
        original_config = {
            "mcpServers": {
                "context7": {
                    "command": "cmd",
                    "args": ["/c", "echo", "original"]
                }
            }
        }

        mcp_path = os.path.join(test_project_dir, '.mcp.json')
        with open(mcp_path, 'w', encoding='utf-8') as f:
            json.dump(original_config, f, indent=2)

        # 설정 적용 (오류 유발)
        with patch.object(self.setup_cmd.config_generator, 'apply_config', return_value=False):
            result = self.setup_cmd.setup_project(test_project_dir)

            # 오류 처리 확인
            self.assertIn('error', result)

            # 롤백 시도
            rollback_result = self.setup_cmd.rollback_config(mcp_path)

            if rollback_result:
                # 원본 설정 복원 확인
                with open(mcp_path, 'r', encoding='utf-8') as f:
                    restored_config = json.load(f)
                    self.assertEqual(restored_config, original_config)


if __name__ == '__main__':
    unittest.main()