"""
ConfigGenerator 테스트 파일

TAG-WIN-003: 동적 설정 생성기 검증
"""

import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open

# 테스트 대상 모듈 경로 설정
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from moai_adk.platform.config_generator import ConfigGenerator
from moai_adk.platform.detector import PlatformDetector
from moai_adk.platform.templates import ConfigTemplates


class TestConfigGenerator(unittest.TestCase):
    """ConfigGenerator 클래스 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = ConfigGenerator()
        self.detector = PlatformDetector()
        self.templates = ConfigTemplates()

    def tearDown(self):
        """테스트 환경 정리"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_generator_initialization(self):
        """ConfigGenerator 초기화 테스트"""
        self.assertIsNotNone(self.generator)
        self.assertTrue(hasattr(self.generator, 'generate_mcp_config'))
        self.assertTrue(hasattr(self.generator, 'generate_statusline_config'))
        self.assertTrue(hasattr(self.generator, 'apply_config'))

    def test_generate_mcp_config_windows(self):
        """Windows MCP 설정 생성 테스트"""
        with patch('config_generator.sys.platform', 'win32'):
            mcp_config = self.generator.generate_mcp_config()

            # 기본 구조 확인
            self.assertIn('mcpServers', mcp_config)
            self.assertIn('context7', mcp_config['mcpServers'])
            self.assertIn('playwright', mcp_config['mcpServers'])
            self.assertIn('figma-dev-mode-mcp-server', mcp_config['mcpServers'])

            # Windows 명령어 확인
            context7_config = mcp_config['mcpServers']['context7']
            self.assertEqual(context7_config['command'], 'cmd')
            self.assertEqual(context7_config['args'][0], '/c')

    def test_generate_mcp_config_macos(self):
        """macOS MCP 설정 생성 테스트"""
        with patch('config_generator.sys.platform', 'darwin'):
            mcp_config = self.generator.generate_mcp_config()

            # 기본 구조 확인
            self.assertIn('mcpServers', mcp_config)

            # macOS 명령어 확인
            context7_config = mcp_config['mcpServers']['context7']
            self.assertEqual(context7_config['command'], 'bash')
            self.assertEqual(context7_config['args'][0], '-c')

    def test_generate_mcp_config_linux(self):
        """Linux MCP 설정 생성 테스트"""
        with patch('config_generator.sys.platform', 'linux'):
            mcp_config = self.generator.generate_mcp_config()

            # 기본 구조 확인
            self.assertIn('mcpServers', mcp_config)

            # Linux 명령어 확인
            context7_config = mcp_config['mcpServers']['context7']
            self.assertEqual(context7_config['command'], 'bash')
            self.assertEqual(context7_config['args'][0], '-c')

    def test_generate_statusline_config_windows(self):
        """Windows statusline 설정 생성 테스트"""
        with patch('config_generator.sys.platform', 'win32'):
            statusline_config = self.generator.generate_statusline_config()

            # Windows는 Python 모듈 직접 호출
            self.assertEqual(statusline_config['command'], 'python')
            self.assertIn('moai_adk.statusline.main', statusline_config['args'])

    def test_generate_statusline_config_unix(self):
        """Unix 계열 statusline 설정 생성 테스트"""
        for os_type in ['darwin', 'linux']:
            with self.subTest(os_type=os_type):
                with patch('config_generator.sys.platform', os_type):
                    statusline_config = self.generator.generate_statusline_config()

                    # Unix는 uv 명령어 사용
                    self.assertEqual(statusline_config['command'], 'uv')
                    self.assertIn('moai-adk', statusline_config['args'])

    def test_generate_claude_settings_windows(self):
        """Windows Claude 설정 생성 테스트"""
        with patch('config_generator.sys.platform', 'win32'):
            claude_settings = self.generator.generate_claude_settings()

            # 기본 구조 확인
            self.assertIn('claude', claude_settings)
            self.assertIn('statusline', claude_settings['claude'])

            # Windows statusline 설정 확인
            statusline_config = claude_settings['claude']['statusline']
            self.assertEqual(statusline_config['command'], 'python')
            self.assertIn('moai_adk.statusline.main', statusline_config['args'])

    def test_generate_claude_settings_unix(self):
        """Unix 계열 Claude 설정 생성 테스트"""
        for os_type in ['darwin', 'linux']:
            with self.subTest(os_type=os_type):
                with patch('config_generator.sys.platform', os_type):
                    claude_settings = self.generator.generate_claude_settings()

                    # 기본 구조 확인
                    self.assertIn('claude', claude_settings)
                    statusline_config = claude_settings['claude']['statusline']

                    # Unix는 uv 명령어 사용
                    self.assertEqual(statusline_config['command'], 'uv')
                    self.assertIn('moai-adk', statusline_config['args'])

    def test_apply_config_success(self):
        """설정 적용 성공 테스트"""
        test_config = {'test': 'data'}
        test_path = os.path.join(self.temp_dir, 'test_config.json')

        with patch('builtins.open', mock_open()), \
             patch('json.dump') as mock_dump:

            result = self.generator.apply_config(test_config, test_path)

            # 성공 확인
            self.assertTrue(result)
            mock_dump.assert_called_once()

    def test_apply_config_failure(self):
        """설정 적용 실패 테스트"""
        test_config = {'test': 'data'}
        invalid_path = os.path.join(self.temp_dir, 'nonexistent', 'config.json')

        with patch('builtins.open', side_effect=OSError("Permission denied")):
            result = self.generator.apply_config(test_config, invalid_path)
            self.assertFalse(result)

    def test_generate_optimized_config(self):
        """최적화된 설정 생성 테스트"""
        with patch('config_generator.sys.platform', 'win32'):
            config_result = self.generator.generate_optimized_config()

            # 결과 구조 확인
            self.assertIn('mcp', config_result)
            self.assertIn('statusline', config_result)
            self.assertIn('claude_settings', config_result)
            self.assertIn('detected_os', config_result)
            self.assertIn('is_valid', config_result)

            # Windows 설정 확인
            self.assertEqual(config_result['detected_os'], 'windows')
            self.assertTrue(config_result['is_valid'])

            # 개별 설정 확인
            mcp_config = config_result['mcp']
            self.assertIn('mcpServers', mcp_config)

            statusline_config = config_result['statusline']
            self.assertEqual(statusline_config['command'], 'python')

            claude_settings = config_result['claude_settings']
            self.assertIn('claude', claude_settings)

    def test_config_validation(self):
        """설정 유효성 검사 테스트"""
        # 유효한 설정 (모든 필수 서버 포함)
        valid_mcp = {
            'mcpServers': {
                'context7': {
                    'command': 'cmd',
                    'args': ['/c', 'npx', '-y', '@upstash/context7-mcp@latest']
                },
                'playwright': {
                    'command': 'cmd',
                    'args': ['/c', 'npx', '-y', 'playwright-bdd@latest']
                },
                'figma-dev-mode-mcp-server': {
                    'command': 'cmd',
                    'args': ['/c', 'npx', '-y', 'figma-dev-mode-mcp-server@latest']
                }
            }
        }
        self.assertTrue(self.generator.validate_config(valid_mcp, 'mcp'))

        # 무효한 설정
        invalid_mcp = {
            'invalid_structure': 'test'
        }
        self.assertFalse(self.generator.validate_config(invalid_mcp, 'mcp'))

    def test_backup_and_restore(self):
        """백업 및 복원 테스트"""
        test_config = {'test': 'data'}
        test_path = os.path.join(self.temp_dir, 'config.json')

        # 백업 생성
        backup_result = self.generator.create_backup(test_path)
        self.assertTrue(backup_result)

        # 복원
        if os.path.exists(test_path + '.backup'):
            restore_result = self.generator.restore_backup(test_path)
            self.assertTrue(restore_result)

    def test_file_operations_error_handling(self):
        """파일 작업 오류 처리 테스트"""
        # 존재하지 않는 디렉토리 테스트
        invalid_path = os.path.join('nonexistent', 'config.json')
        test_config = {'test': 'data'}

        with patch('builtins.open', side_effect=OSError("Permission denied")):
            result = self.generator.apply_config(test_config, invalid_path)
            self.assertFalse(result)

        # JSON 쓰기 오류 테스트
        test_path = os.path.join(self.temp_dir, 'config.json')
        with patch('builtins.open', mock_open()), \
             patch('json.dump', side_effect=TypeError('Invalid data')):
            result = self.generator.apply_config(test_config, test_path)
            self.assertFalse(result)

    def test_config_consistency(self):
        """설정 일관성 검증 테스트"""
        with patch('config_generator.sys.platform', 'win32'):
            mcp_config = self.generator.generate_mcp_config()
            statusline_config = self.generator.generate_statusline_config()
            claude_settings = self.generator.generate_claude_settings()

            # 설정 간 일관성 확인
            # (예: statusline command는 Claude 설정과 일치해야 함)
            statusline_command = statusline_config['command']
            claude_statusline_command = claude_settings['claude']['statusline']['command']
            self.assertEqual(statusline_command, claude_statusline_command)

    def test_detect_os_changes(self):
        """OS 변화 감지 테스트"""
        # 현재 Windows로 설정
        with patch('config_generator.sys.platform', 'win32'):
            windows_config = self.generator.generate_mcp_config()
            self.assertEqual(windows_config['mcpServers']['context7']['command'], 'cmd')

        # OS를 macOS로 변경
        with patch('config_generator.sys.platform', 'darwin'):
            macos_config = self.generator.generate_mcp_config()
            self.assertEqual(macos_config['mcpServers']['context7']['command'], 'bash')

    def test_edge_cases(self):
        """엣지 케이스 테스트"""
        # 알 수 없는 OS 테스트
        with patch('config_generator.sys.platform', 'unknown_os'):
            config = self.generator.generate_mcp_config()
            # 알 수 없는 OS의 경우 기본으로 Linux 설정 사용
            self.assertEqual(config['mcpServers']['context7']['command'], 'bash')

        # 빈 설정 테스트
        result = self.generator.validate_config({}, 'mcp')
        self.assertFalse(result)

        # None 테스트
        result = self.generator.validate_config(None, 'mcp')
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()