"""
ConfigTemplates 테스트 파일

TAG-WIN-002: OS별 설정 템플릿 구조 검증
"""

import sys
import unittest
import json
import os
import tempfile

from unittest.mock import patch, mock_open

# 테스트 대상 모듈 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'moai_adk', 'platform'))

from templates import ConfigTemplates


class TestConfigTemplates(unittest.TestCase):
    """ConfigTemplates 클래스 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.templates = ConfigTemplates()

    def test_template_initialization(self):
        """템플릿 초기화 테스트"""
        self.assertIsNotNone(self.templates)
        self.assertTrue(hasattr(self.templates, 'get_mcp_template'))
        self.assertTrue(hasattr(self.templates, 'get_statusline_template'))
        self.assertTrue(hasattr(self.templates, 'get_claude_settings_template'))

    def test_mcp_template_windows(self):
        """Windows MCP 템플릿 테스트"""
        template = self.templates.get_mcp_template('windows')

        # 필수 키 확인
        self.assertIn('mcpServers', template)
        self.assertIn('context7', template['mcpServers'])
        self.assertIn('playwright', template['mcpServers'])
        self.assertIn('figma-dev-mode-mcp-server', template['mcpServers'])

        # Windows 명령어 확인
        context7_config = template['mcpServers']['context7']
        self.assertEqual(context7_config['command'], 'cmd')
        self.assertEqual(context7_config['args'][0], '/c')

    def test_mcp_template_macos(self):
        """macOS MCP 템플릿 테스트"""
        template = self.templates.get_mcp_template('macos')

        self.assertIn('mcpServers', template)
        context7_config = template['mcpServers']['context7']
        self.assertEqual(context7_config['command'], 'bash')
        self.assertEqual(context7_config['args'][0], '-c')

    def test_mcp_template_linux(self):
        """Linux MCP 템플릿 테스트"""
        template = self.templates.get_mcp_template('linux')

        self.assertIn('mcpServers', template)
        context7_config = template['mcpServers']['context7']
        self.assertEqual(context7_config['command'], 'bash')
        self.assertEqual(context7_config['args'][0], '-c')

    def test_mcp_template_unknown_os(self):
        """알 수 없는 OS MCP 템플릿 테스트 - 기본으로 Linux 설정 사용"""
        template = self.templates.get_mcp_template('unknown_os')

        self.assertIn('mcpServers', template)
        context7_config = template['mcpServers']['context7']
        self.assertEqual(context7_config['command'], 'bash')
        self.assertEqual(context7_config['args'][0], '-c')

    def test_statusline_template_windows(self):
        """Windows statusline 템플릿 테스트"""
        template = self.templates.get_statusline_template('windows')

        # Windows는 Python 모듈 직접 호출
        self.assertEqual(template['command'], 'python')
        self.assertIn('moai_adk.statusline.main', template['args'])

    def test_statusline_template_unix(self):
        """Unix 계열 statusline 템플릿 테스트"""
        for os_type in ['macos', 'linux']:
            with self.subTest(os_type=os_type):
                template = self.templates.get_statusline_template(os_type)

                # Unix는 uv 명령어 사용
                self.assertEqual(template['command'], 'uv')
                self.assertIn('moai-adk', template['args'])

    def test_claude_settings_template_windows(self):
        """Windows Claude 설정 템플릿 테스트"""
        template = self.templates.get_claude_settings_template('windows')

        self.assertIn('claude', template)
        self.assertIn('statusline', template['claude'])

        # Windows의 statusline 설정 확인
        statusline_config = template['claude']['statusline']
        self.assertEqual(statusline_config['command'], 'python')
        self.assertIn('moai_adk.statusline.main', statusline_config['args'])

    def test_claude_settings_template_unix(self):
        """Unix 계열 Claude 설정 템플릿 테스트"""
        for os_type in ['macos', 'linux']:
            with self.subTest(os_type=os_type):
                template = self.templates.get_claude_settings_template(os_type)

                self.assertIn('claude', template)
                statusline_config = template['claude']['statusline']
                self.assertEqual(statusline_config['command'], 'uv')

    def test_validate_template_structure(self):
        """템플릿 구조 유효성 검사 테스트"""
        for os_type in ['windows', 'macos', 'linux']:
            with self.subTest(os_type=os_type):
                # MCP 템플릿 검증
                mcp_template = self.templates.get_mcp_template(os_type)
                self._validate_mcp_structure(mcp_template)

                # Statusline 템플릿 검증
                statusline_template = self.templates.get_statusline_template(os_type)
                self._validate_statusline_structure(statusline_template)

                # Claude 설정 템플릿 검증
                claude_template = self.templates.get_claude_settings_template(os_type)
                self._validate_claude_settings_structure(claude_template)

    def _validate_mcp_structure(self, template):
        """MCP 템플릿 구조 검증"""
        self.assertIsInstance(template, dict)
        self.assertIn('mcpServers', template)
        self.assertIsInstance(template['mcpServers'], dict)

        # 필수 서버 확인
        required_servers = ['context7', 'playwright', 'figma-dev-mode-mcp-server']
        for server in required_servers:
            self.assertIn(server, template['mcpServers'])
            server_config = template['mcpServers'][server]
            self.assertIsInstance(server_config, dict)
            self.assertIn('command', server_config)
            self.assertIn('args', server_config)

    def _validate_statusline_structure(self, template):
        """Statusline 템플릿 구조 검증"""
        self.assertIsInstance(template, dict)
        self.assertIn('command', template)
        self.assertIn('args', template)
        self.assertIsInstance(template['args'], list)

    def _validate_claude_settings_structure(self, template):
        """Claude 설정 템플릿 구조 검증"""
        self.assertIsInstance(template, dict)
        self.assertIn('claude', template)
        claude_config = template['claude']
        self.assertIn('statusline', claude_config)

    def test_all_templates_consistency(self):
        """모든 템플릿 간의 일관성 검증"""
        os_types = ['windows', 'macos', 'linux']

        for os_type in os_types:
            mcp_template = self.templates.get_mcp_template(os_type)
            statusline_template = self.templates.get_statusline_template(os_type)
            claude_template = self.templates.get_claude_settings_template(os_type)

            # 같은 OS의 템플릿들 간에 호환성 확인
            # (예: statusline command는 Claude 설정과 일치해야 함)
            statusline_command = statusline_template['command']
            claude_statusline_command = claude_template['claude']['statusline']['command']
            self.assertEqual(statusline_command, claude_statusline_command)

    def test_mcp_server_configurations(self):
        """MCP 서별별 구성 검증"""
        # context7 서버 검증
        for os_type in ['windows', 'macos', 'linux']:
            with self.subTest(os_type=os_type):
                template = self.templates.get_mcp_template(os_type)
                context7_config = template['mcpServers']['context7']

                # context7은 항상 npx 실행
                self.assertIn('npx', context7_config['args'])
                self.assertIn('context7-mcp', ' '.join(context7_config['args']))

        # playwright 서버 검증
        for os_type in ['windows', 'macos', 'linux']:
            with self.subTest(os_type=os_type):
                template = self.templates.get_mcp_template(os_type)
                playwright_config = template['mcpServers']['playwright']

                # playwright는 항상 npx 실행
                self.assertIn('npx', playwright_config['args'])
                self.assertIn('playwright-bdd', ' '.join(playwright_config['args']))

    def test_figma_server_configuration(self):
        """Figma 서버 구성 검증"""
        for os_type in ['windows', 'macos', 'linux']:
            with self.subTest(os_type=os_type):
                template = self.templates.get_mcp_template(os_type)
                figma_config = template['mcpServers']['figma-dev-mode-mcp-server']

                # Figma 서버는 항상 npx 실행
                self.assertIn('npx', figma_config['args'])
                self.assertIn('figma-dev-mode-mcp-server', ' '.join(figma_config['args']))


if __name__ == '__main__':
    unittest.main()