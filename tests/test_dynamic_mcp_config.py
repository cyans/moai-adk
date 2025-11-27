"""
Dynamic MCP Configuration Tests

TAG-WIN-003: 동적 MCP 설정 생성 검증

OS 감지를 통한 동적 MCP 설정 생성 및 적용 기능을 검증합니다.
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
try:
    from moai_adk.platform.config_generator import ConfigGenerator
    from moai_adk.platform.templates import ConfigTemplates
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


class TestDynamicMCPConfig(unittest.TestCase):
    """동적 MCP 설정 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        if not CONFIG_AVAILABLE:
            self.skipTest("Config modules not yet implemented")

        self.temp_dir = tempfile.mkdtemp()
        self.generator = ConfigGenerator()

    def tearDown(self):
        """테스트 환경 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_mcp_config_generation_windows(self):
        """Windows 환경에서 MCP 설정 생성 테스트

        Windows 환경에서 cmd /c 명령어를 사용하는 MCP 설정이 생성되는지 검증합니다.
        """
        # Windows 환경 모의
        with patch('sys.platform', 'win32'):
            mcp_config = self.generator.generate_mcp_config()

            # MCP 서버 설정 검증
            self.assertIsInstance(mcp_config, dict)
            self.assertIn('mcpServers', mcp_config)

            # Windows 설정 검증
            servers = mcp_config['mcpServers']
            for server_name, server_config in servers.items():
                self.assertIn('command', server_config)
                self.assertIn('args', server_config)

                # Windows에서는 cmd 명령어 사용
                self.assertEqual(server_config['command'], 'cmd')
                self.assertEqual(server_config['args'][0], '/c')

    def test_mcp_config_generation_unix(self):
        """Unix 환경에서 MCP 설정 생성 테스트

        Unix 환경에서 bash -c 명령어를 사용하는 MCP 설정이 생성되는지 검증합니다.
        """
        # macOS 환경 모의
        with patch('sys.platform', 'darwin'):
            mcp_config = self.generator.generate_mcp_config()

            # Unix 설정 검증
            servers = mcp_config['mcpServers']
            for server_name, server_config in servers.items():
                self.assertEqual(server_config['command'], 'bash')
                self.assertEqual(server_config['args'][0], '-c')

        # Linux 환경 모의
        with patch('sys.platform', 'linux'):
            mcp_config = self.generator.generate_mcp_config()

            # Unix 설정 검증
            servers = mcp_config['mcpServers']
            for server_name, server_config in servers.items():
                self.assertEqual(server_config['command'], 'bash')
                self.assertEqual(server_config['args'][0], '-c')

    def test_mcp_config_application(self):
        """MCP 설정 적용 테스트

        생성된 MCP 설정이 실제 파일로 정상적으로 적용되는지 검증합니다.
        """
        # 테스트용 MCP 설정 생성
        mcp_config = self.generator.generate_mcp_config()

        # 테스트 파일 경로
        test_mcp_path = os.path.join(self.temp_dir, '.mcp.json')

        # 설정 적용
        result = self.generator.apply_config(mcp_config, test_mcp_path)
        self.assertTrue(result)

        # 파일 생성 확인
        self.assertTrue(os.path.exists(test_mcp_path))

        # 설정 내용 확인
        with open(test_mcp_path, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
            self.assertEqual(loaded_config, mcp_config)

    def test_mcp_config_backup_and_restore(self):
        """MCP 설정 백업 및 복원 테스트

        설정 변경 시 백업이 정상적으로 생성되고 복원되는지 검증합니다.
        """
        # 원본 설정
        original_config = {
            'mcpServers': {
                'context7': {
                    'command': 'cmd',
                    'args': ['/c', 'npx', '-y', '@upstash/context7-mcp@original@latest']
                }
            }
        }

        # 테스트 파일 경로
        test_mcp_path = os.path.join(self.temp_dir, '.mcp.json')

        # 원본 설정 생성
        with open(test_mcp_path, 'w', encoding='utf-8') as f:
            json.dump(original_config, f, indent=2)

        # 새로운 설정 적용 (백업 자동 생성)
        new_config = self.generator.generate_mcp_config()
        result = self.generator.apply_config(new_config, test_mcp_path)
        self.assertTrue(result)

        # 백업 파일 확인
        backup_files = [f for f in os.listdir(self.temp_dir) if f.startswith('.mcp.json.backup.')]
        self.assertGreater(len(backup_files), 0)

        # 롤백 테스트
        rollback_result = self.generator.rollback_config(test_mcp_path)
        self.assertTrue(rollback_result)

        # 원본 설정 복원 확인
        with open(test_mcp_path, 'r', encoding='utf-8') as f:
            restored_config = json.load(f)
            self.assertEqual(restored_config, original_config)

    def test_cross_platform_mcp_consistency(self):
        """크로스 플랫폼 MCP 설정 일관성 테스트

        모든 플랫폼에서 동일한 MCP 서버가 제공되는지 검증합니다.
        """
        platforms = ['win32', 'darwin', 'linux']
        expected_servers = ['context7', 'playwright', 'figma-dev-mode-mcp-server']

        for platform in platforms:
            with patch('sys.platform', platform):
                mcp_config = self.generator.generate_mcp_config()
                servers = mcp_config['mcpServers']

                # 모든 예상 서버가 존재하는지 확인
                for server in expected_servers:
                    self.assertIn(server, servers)

                # 각 서버가 유효한 설정을 가지고 있는지 확인
                for server_name, server_config in servers.items():
                    self.assertIn('command', server_config)
                    self.assertIn('args', server_config)
                    self.assertIsInstance(server_config['args'], list)

    def test_mcp_config_validation(self):
        """MCP 설정 유효성 검사 테스트

        생성된 MCP 설정의 유효성을 검증하는 기능이 정상적으로 동작하는지 확인합니다.
        """
        # 유효한 MCP 설정 생성
        mcp_config = self.generator.generate_mcp_config()
        is_valid = self.generator.validate_config(mcp_config, 'mcp')
        self.assertTrue(is_valid)

        # 유효하지 않은 설정 검증
        invalid_config = {'invalid': 'config'}
        is_valid = self.generator.validate_config(invalid_config, 'mcp')
        self.assertFalse(is_valid)

    def test_optimized_config_generation(self):
        """최적화된 설정 생성 통합 테스트

        모든 설정(MCP, statusline, Claude settings)을 한 번에 생성하는 기능을 검증합니다.
        """
        optimized_config = self.generator.generate_optimized_config()

        # 필드 존재 확인
        self.assertIn('mcp', optimized_config)
        self.assertIn('statusline', optimized_config)
        self.assertIn('claude_settings', optimized_config)
        self.assertIn('detected_os', optimized_config)
        self.assertIn('is_valid', optimized_config)
        self.assertIn('generated_at', optimized_config)
        self.assertIn('platform_info', optimized_config)

        # 각 설정 내용 확인
        self.assertIn('mcpServers', optimized_config['mcp'])
        self.assertIn('enabled', optimized_config['statusline'])
        self.assertIn('claude', optimized_config['claude_settings'])

    def test_config_summary_generation(self):
        """설정 요약 정보 생성 테스트

        설정 요약 정보가 정상적으로 생성되는지 검증합니다.
        """
        summary = self.generator.get_config_summary()

        # 필드 존재 확인
        self.assertIn('current_os', summary)
        self.assertIn('is_supported', summary)
        self.assertIn('mcp_servers', summary)
        self.assertIn('statusline_command', summary)
        self.assertIn('claude_statusline_command', summary)
        self.assertIn('platform_details', summary)

        # 데이터 타입 확인
        self.assertIsInstance(summary['current_os'], str)
        self.assertIsInstance(summary['is_supported'], bool)
        self.assertIsInstance(summary['mcp_servers'], list)

    def test_batch_config_application(self):
        """일괄 설정 적용 테스트

        여러 설정 파일을 한 번에 적용하는 기능을 검증합니다.
        """
        # 테스트 디렉토리 생성
        test_base_dir = os.path.join(self.temp_dir, 'test_project')
        os.makedirs(test_base_dir, exist_ok=True)

        # 일괄 설정 적용
        results = self.generator.apply_all_configs(test_base_dir)

        # 모든 설정이 성공적으로 적용되었는지 확인
        self.assertIn('mcp', results)
        self.assertIn('claude_settings', results)
        self.assertTrue(results['mcp'])
        self.assertTrue(results['claude_settings'])

        # 파일 생성 확인
        mcp_path = os.path.join(test_base_dir, '.mcp.json')
        claude_settings_path = os.path.join(test_base_dir, '.claude', 'settings.json')

        self.assertTrue(os.path.exists(mcp_path))
        self.assertTrue(os.path.exists(claude_settings_path))

    def test_mcp_config_diff(self):
        """MCP 설정 차이 비교 테스트

        두 설정 간의 차이를 비교하는 기능을 검증합니다.
        """
        # 원본 설정
        old_config = {
            'mcpServers': {
                'context7': {
                    'command': 'cmd',
                    'args': ['/c', 'npx', '-y', '@upstash/context7-mcp@v1@latest']
                }
            }
        }

        # 수정된 설정
        new_config = {
            'mcpServers': {
                'context7': {
                    'command': 'cmd',
                    'args': ['/c', 'npx', '-y', '@upstash/context7-mcp@v2@latest']
                },
                'new_server': {
                    'command': 'cmd',
                    'args': ['/c', 'npx', '-y', '@new/server@latest']
                }
            }
        }

        # 차이 비교
        diff = self.generator.get_config_diff(old_config, new_config)

        # 변경된 내용 확인
        self.assertIn('mcpServers.context7.args', diff)
        self.assertIn('mcpServers.new_server', diff)
        self.assertEqual(diff['mcpServers.new_server']['added'], new_config['mcpServers']['new_server'])

    def test_mcp_config_error_handling(self):
        """MCP 설정 오류 처리 테스트

        오류 발생 시 적절한 예외 처리가 동작하는지 검증합니다.
        """
        # 잘못된 파일 경로로 설정 적용 시도
        invalid_path = os.path.join(self.temp_dir, 'nonexistent', '.mcp.json')
        result = self.generator.apply_config({}, invalid_path)
        self.assertFalse(result)

        # 존재하지 않는 파일 롤백 시도
        result = self.generator.rollback_config(invalid_path)
        self.assertFalse(result)

        # 유효하지 않은 설정으로 검증 시도
        result = self.generator.validate_config({}, 'invalid_type')
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()