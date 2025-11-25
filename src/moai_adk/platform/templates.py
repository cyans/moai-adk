"""
ConfigTemplates 모듈

TAG-WIN-002: OS별 설정 템플릿 구조 설계

OS별 최적화된 설정 템플릿을 제공합니다.
Windows, macOS, Linux 환경에 맞는 MCP 서버, statusline, Claude 설정을 제공합니다.

이 클래스는 각 OS별로 최적화된 실행 환경 설정을 미리 정의된 템플릿에서 제공합니다.
"""

import json
from typing import Dict, Any
import os


class ConfigTemplates:
    """OS별 설정 템플릿 클래스

    Attributes:
        _mcp_templates (Dict): MCP 서버 설정 템플릿
        _statusline_templates (Dict): Statusline 실행 설정 템플릿
        _claude_settings_templates (Dict): Claude 설정 템플릿
    """

    def __init__(self):
        """ConfigTemplates 초기화

        OS별 설정 템플릿을 초기화합니다.
        Windows, macOS, Linux에 최적화된 MCP 서버, statusline, Claude 설정을 정의합니다.
        """
        self._mcp_templates = self._init_mcp_templates()
        self._statusline_templates = self._init_statusline_templates()
        self._claude_settings_templates = self._init_claude_settings_templates()

    def _init_mcp_templates(self) -> Dict[str, Any]:
        """MCP 서버 설정 템플릿 초기화"""
        return {
            'windows': {
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
            },
            'macos': {
                'mcpServers': {
                    'context7': {
                        'command': 'bash',
                        'args': ['-c', 'npx', '-y', '@upstash/context7-mcp@latest']
                    },
                    'playwright': {
                        'command': 'bash',
                        'args': ['-c', 'npx', '-y', 'playwright-bdd@latest']
                    },
                    'figma-dev-mode-mcp-server': {
                        'command': 'bash',
                        'args': ['-c', 'npx', '-y', 'figma-dev-mode-mcp-server@latest']
                    }
                }
            },
            'linux': {
                'mcpServers': {
                    'context7': {
                        'command': 'bash',
                        'args': ['-c', 'npx', '-y', '@upstash/context7-mcp@latest']
                    },
                    'playwright': {
                        'command': 'bash',
                        'args': ['-c', 'npx', '-y', 'playwright-bdd@latest']
                    },
                    'figma-dev-mode-mcp-server': {
                        'command': 'bash',
                        'args': ['-c', 'npx', '-y', 'figma-dev-mode-mcp-server@latest']
                    }
                }
            }
        }

    def _init_statusline_templates(self) -> Dict[str, Any]:
        """Statusline 실행 설정 템플릿 초기화"""
        return {
            'windows': {
                'enabled': True,
                'mode': 'extended',
                'update_check': True,
                'performance': {
                    'cache_enabled': True,
                    'startup_timeout': 100,
                    'fast_startup': True
                },
                'command': 'python',
                'args': ['-m', 'moai_adk.statusline.main']
            },
            'macos': {
                'enabled': True,
                'mode': 'extended',
                'update_check': True,
                'performance': {
                    'cache_enabled': True,
                    'startup_timeout': 100,
                    'fast_startup': False
                },
                'command': 'uv',
                'args': ['run', 'moai-adk', 'statusline']
            },
            'linux': {
                'enabled': True,
                'mode': 'extended',
                'update_check': True,
                'performance': {
                    'cache_enabled': True,
                    'startup_timeout': 100,
                    'fast_startup': False
                },
                'command': 'uv',
                'args': ['run', 'moai-adk', 'statusline']
            }
        }

    def _init_claude_settings_templates(self) -> Dict[str, Any]:
        """Claude 설정 템플릿 초기화"""
        return {
            'windows': {
                'claude': {
                    'statusline': {
                        'command': 'python',
                        'args': ['-m', 'moai_adk.statusline.main']
                    }
                }
            },
            'macos': {
                'claude': {
                    'statusline': {
                        'command': 'uv',
                        'args': ['run', 'moai-adk', 'statusline']
                    }
                }
            },
            'linux': {
                'claude': {
                    'statusline': {
                        'command': 'uv',
                        'args': ['run', 'moai-adk', 'statusline']
                    }
                }
            }
        }

    def get_mcp_template(self, os_type: str) -> Dict[str, Any]:
        """
        OS별 MCP 설정 템플릿 반환

        Args:
            os_type (str): OS 종류 ('windows', 'macos', 'linux')

        Returns:
            Dict[str, Any]: MCP 설정 템플릿
        """
        return self._mcp_templates.get(os_type, self._mcp_templates['linux'])

    def get_statusline_template(self, os_type: str) -> Dict[str, Any]:
        """
        OS별 statusline 설정 템플릿 반환

        Args:
            os_type (str): OS 종류 ('windows', 'macos', 'linux')

        Returns:
            Dict[str, Any]: Statusline 설정 템플릿
        """
        return self._statusline_templates.get(os_type, self._statusline_templates['linux'])

    def get_claude_settings_template(self, os_type: str) -> Dict[str, Any]:
        """
        OS별 Claude 설정 템플릿 반환

        Args:
            os_type (str): OS 종류 ('windows', 'macos', 'linux')

        Returns:
            Dict[str, Any]: Claude 설정 템플릿
        """
        return self._claude_settings_templates.get(os_type, self._claude_settings_templates['linux'])

    def get_template(self, os_type: str) -> Dict[str, Any]:
        """
        OS별 전체 설정 템플릿 반환 (호환성을 위한 메서드)

        Args:
            os_type (str): OS 종류 ('windows', 'macos', 'linux')

        Returns:
            Dict[str, Any]: OS별 전체 설정 템플릿
        """
        return self.get_all_templates(os_type)

    def get_all_templates(self, os_type: str) -> Dict[str, Any]:
        """
        모든 설정 템플릿을 OS별로 반환

        Args:
            os_type (str): OS 종류 ('windows', 'macos', 'linux')

        Returns:
            Dict[str, Any]: 모든 설정 템플릿
        """
        return {
            'mcp': self.get_mcp_template(os_type),
            'statusline': self.get_statusline_template(os_type),
            'claude_settings': self.get_claude_settings_template(os_type)
        }

    def validate_template(self, template: Dict[str, Any], template_type: str) -> bool:
        """
        템플릿 유효성 검사

        Args:
            template (Dict[str, Any]): 검증할 템플릿
            template_type (str): 템플릿 종류 ('mcp', 'statusline', 'claude_settings')

        Returns:
            bool: 유효한 템플릿이면 True
        """
        try:
            if template_type == 'mcp':
                return self._validate_mcp_template(template)
            elif template_type == 'statusline':
                return self._validate_statusline_template(template)
            elif template_type == 'claude_settings':
                return self._validate_claude_settings_template(template)
            return False
        except Exception:
            return False

    def _validate_mcp_template(self, template: Dict[str, Any]) -> bool:
        """MCP 템플릿 유효성 검사"""
        if not isinstance(template, dict) or 'mcpServers' not in template:
            return False

        servers = template['mcpServers']
        if not isinstance(servers, dict):
            return False

        required_servers = ['context7', 'playwright', 'figma-dev-mode-mcp-server']
        for server in required_servers:
            if server not in servers:
                return False
            server_config = servers[server]
            if not isinstance(server_config, dict):
                return False
            if 'command' not in server_config or 'args' not in server_config:
                return False

        return True

    def _validate_statusline_template(self, template: Dict[str, Any]) -> bool:
        """Statusline 템플릿 유효성 검사"""
        if not isinstance(template, dict):
            return False
        if 'command' not in template or 'args' not in template:
            return False
        if not isinstance(template['args'], list):
            return False
        return True

    def _validate_claude_settings_template(self, template: Dict[str, Any]) -> bool:
        """Claude 설정 템플릿 유효성 검사"""
        if not isinstance(template, dict) or 'claude' not in template:
            return False

        claude_config = template['claude']
        if not isinstance(claude_config, dict) or 'statusline' not in claude_config:
            return False

        statusline_config = claude_config['statusline']
        if not isinstance(statusline_config, dict):
            return False
        if 'command' not in statusline_config or 'args' not in statusline_config:
            return False
        if not isinstance(statusline_config['args'], list):
            return False

        return True