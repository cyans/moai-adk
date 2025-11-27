"""
PlatformDetector 모듈

TAG-WIN-001: OS 자동 감지 기구 구현

OS 플랫폼을 감지하고 해당 플랫폼에 최적화된 설정을 제공합니다.
Windows, macOS, Linux 환경에서 MoAI-ADK의 호환성을 보장합니다.
"""

import sys
from typing import Dict, Any


class PlatformDetector:
    """OS 플랫폼 감지 및 설정 제공 클래스"""

    def __init__(self):
        """PlatformDetector 초기화

        플랫폼 매핑 테이블을 설정하고 감지 엔진을 초기화합니다.
        """
        self._platform_mapping = {
            'win32': 'windows',
            'darwin': 'macos',
            'linux': 'linux'
        }
        self._config_templates = {
            'windows': {
                'command': 'cmd',
                'args': ['/c'],
                'shell': True,
                'encoding': 'utf-8',
                'path_separator': '\\',
                'env_var_format': '%{}%',
                'fast_startup': True
            },
            'macos': {
                'command': 'bash',
                'args': ['-c'],
                'shell': False,
                'encoding': 'utf-8',
                'path_separator': '/',
                'env_var_format': '${{}',
                'fast_startup': False
            },
            'linux': {
                'command': 'bash',
                'args': ['-c'],
                'shell': False,
                'encoding': 'utf-8',
                'path_separator': '/',
                'env_var_format': '${{}',
                'fast_startup': False
            }
        }

    @property
    def platform(self) -> str:
        """현재 플랫폼 반환 (매번 새로 읽음)"""
        return sys.platform

    def detect_os(self) -> str:
        """
        현재 OS 감지

        Returns:
            str: 'windows', 'macos', 'linux', 또는 'unknown'
        """
        return self._platform_mapping.get(self.platform, 'unknown')

    def get_platform_config(self) -> Dict[str, Any]:
        """
        플랫폼별 기본 설정 반환

        감지된 OS에 따라 적절한 실행 환경 설정을 반환합니다.

        Returns:
            Dict[str, Any]: 플랫폼별 설정 정보

        Examples:
            >>> detector = PlatformDetector()
            >>> config = detector.get_platform_config()
            >>> print(config['command'])  # 'cmd' (Windows) 또는 'bash' (Unix)
        """
        os_type = self.detect_os()
        template = self._config_templates.get(os_type)

        if template:
            return template.copy()

        # 알 수 없는 OS의 경우 기본 Unix 설정 사용
        return self._config_templates['linux'].copy()

    def validate_platform(self) -> bool:
        """
        플랫폼 유효성 검사

        지원되는 플랫폼인지 확인합니다.

        Returns:
            bool: 유효한 플랫폼이면 True, 그렇지 않으면 False
        """
        detected_os = self.detect_os()
        return detected_os in ['windows', 'macos', 'linux']

    def get_detailed_info(self) -> Dict[str, Any]:
        """
        상세한 플랫폼 정보 반환 (확장 기능)

        시스템 정보와 함께 플랫폼 관련 상세 정보를 제공합니다.

        Returns:
            Dict[str, Any]: 상세 플랫폼 정보
        """
        return {
            'platform': self.platform,
            'detected_os': self.detect_os(),
            'is_valid': self.validate_platform(),
            'version': sys.version,
            'version_info': sys.version_info,
            'supported_platforms': list(self._platform_mapping.values())
        }

    def get_environment_format(self) -> Dict[str, Any]:
        """
        플랫폼별 환경변수 형식 반환

        Returns:
            Dict[str, Any]: 환경변수 처리에 필요한 형식 정보
        """
        os_type = self.detect_os()
        template = self._config_templates.get(os_type)

        if template:
            return {
                'path_separator': template['path_separator'],
                'env_var_format': template['env_var_format']
            }

        return {
            'path_separator': '/',
            'env_var_format': '${}'
        }