"""
Setup Command 모듈

TAG-WIN-004: 자동 설정 명령 구현

MoAI-ADK의 자동 설정을 담당하는 중앙 제어 모듈입니다.
OS 감지, 설정 생성, 백업/복원, 상태 확인 기능을 통합하여 제공합니다.
"""

import json
import os
import sys
import shutil
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from moai_adk.platform.detector import PlatformDetector
from moai_adk.platform.config_generator import ConfigGenerator
from moai_adk.platform.templates import ConfigTemplates


class SetupCommand:
    """자동 설정 명령 클래스"""

    def __init__(self, backup_enabled: bool = True, backup_dir: str = '.moai/backup'):
        """
        SetupCommand 초기화

        Args:
            backup_enabled (bool): 백업 기능 활성화 여부
            backup_dir (str): 백업 디렉토리 경로
        """
        self.detector = PlatformDetector()
        self.config_generator = ConfigGenerator()
        self.backup_enabled = backup_enabled
        self.backup_dir = backup_dir
        self.templates = ConfigTemplates()

    def get_detected_os(self) -> str:
        """
        감지된 OS 반환

        Returns:
            str: 'windows', 'macos', 'linux', 또는 'unknown'
        """
        return self.detector.detect_os()

    def is_platform_supported(self) -> bool:
        """
        플랫폼 지원 여부 확인

        Returns:
            bool: 지원되는 플랫폼이면 True, 그렇지 않으면 False
        """
        return self.detector.validate_platform()

    def setup_project(self, project_dir: str = '.',
                    mcp_only: bool = False,
                    statusline_only: bool = False,
                    claude_only: bool = False) -> Dict[str, Any]:
        """
        프로젝트 설정 수행

        Args:
            project_dir (str): 프로젝트 디렉토리 경로
            mcp_only (bool): MCP 설정만 적용 여부
            statusline_only (bool): Statusline 설정만 적용 여부
            claude_only (bool): Claude 설정만 적용 여부

        Returns:
            Dict[str, Any]: 설정 결과
        """
        try:
            # 플랫폼 감지
            detected_os = self.get_detected_os()
            is_supported = self.is_platform_supported()

            # 플랫폼 지원 여부 확인
            if not is_supported:
                return {
                    'success': False,
                    'error': f'Unsupported platform: {detected_os}',
                    'platform_detected': detected_os,
                    'backup_created': False
                }

            # 유효한 프로젝트 디렉토리 확인
            if not project_dir or not os.path.isabs(project_dir):
                # 상대 경로인 경우 현재 작업 디렉토리 기준으로 변환
                if not os.path.isabs(project_dir):
                    project_dir = os.path.abspath(project_dir)

                # 유효하지 않은 디렉토리인 경우
                if not os.path.exists(project_dir) and not project_dir.endswith('.json'):
                    return {
                        'success': False,
                        'error': f'Invalid project directory: {project_dir}',
                        'platform_detected': detected_os,
                        'backup_created': False
                    }

            # 결과 초기화
            result = {
                'success': True,
                'details': {},
                'platform_detected': detected_os,
                'backup_created': False
            }

            # 백업 활성화 시 기존 설정 백업
            if self.backup_enabled:
                backup_success = self._backup_existing_configs(project_dir)
                result['backup_created'] = backup_success

            # 설정 파일 경로
            mcp_path = os.path.join(project_dir, '.mcp.json')
            statusline_path = os.path.join(project_dir, '.claude', 'statusline.json')
            claude_settings_path = os.path.join(project_dir, '.claude', 'settings.json')

            # 설정 적용
            if mcp_only or not (statusline_only or claude_only):
                # MCP 설정 적용
                mcp_config = self.config_generator.generate_mcp_config()
                mcp_result = self.config_generator.apply_config(mcp_config, mcp_path)
                result['details']['mcp'] = mcp_result

            if statusline_only or not (mcp_only or claude_only):
                # Statusline 설정 적용
                statusline_config = self.config_generator.generate_statusline_config()
                statusline_result = self.config_generator.apply_config(statusline_config, statusline_path)
                result['details']['statusline'] = statusline_result

            if claude_only or not (mcp_only or statusline_only):
                # Claude 설정 적용
                claude_config = self.config_generator.generate_claude_settings()
                claude_result = self.config_generator.apply_config(claude_config, claude_settings_path)
                result['details']['claude_settings'] = claude_result

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform_detected': self.get_detected_os(),
                'backup_created': False
            }

    def setup_mcp_config(self, project_dir: str = '.') -> Dict[str, Any]:
        """
        MCP 설정만 적용

        Args:
            project_dir (str): 프로젝트 디렉토리 경로

        Returns:
            Dict[str, Any]: 설정 결과
        """
        return self.setup_project(project_dir, mcp_only=True)

    def setup_statusline_config(self, project_dir: str = '.') -> Dict[str, Any]:
        """
        Statusline 설정만 적용

        Args:
            project_dir (str): 프로젝트 디렉토리 경로

        Returns:
            Dict[str, Any]: 설정 결과
        """
        return self.setup_project(project_dir, statusline_only=True)

    def setup_claude_config(self, project_dir: str = '.') -> Dict[str, Any]:
        """
        Claude 설정만 적용

        Args:
            project_dir (str): 프로젝트 디렉토리 경로

        Returns:
            Dict[str, Any]: 설정 결과
        """
        return self.setup_project(project_dir, claude_only=True)

    def rollback_config(self, filepath: str) -> bool:
        """
        설정 파일 롤백

        Args:
            filepath (str): 롤백할 파일 경로

        Returns:
            bool: 롤백 성공 여부
        """
        try:
            if not self.backup_enabled:
                return False

            return self.config_generator.rollback_config(filepath)
        except Exception:
            return False

    def _backup_existing_configs(self, project_dir: str) -> bool:
        """
        기존 설정 파일 백업

        Args:
            project_dir (str): 프로젝트 디렉토리 경로

        Returns:
            bool: 백업 성공 여부
        """
        try:
            backup_success = False

            # MCP 설정 백업
            mcp_path = os.path.join(project_dir, '.mcp.json')
            if os.path.exists(mcp_path):
                backup_success = self.config_generator.create_backup(mcp_path)

            # Claude 설정 백업
            claude_settings_path = os.path.join(project_dir, '.claude', 'settings.json')
            if os.path.exists(claude_settings_path):
                backup_success = self.config_generator.create_backup(claude_settings_path)

            # Statusline 설정 백업
            statusline_path = os.path.join(project_dir, '.claude', 'statusline.json')
            if os.path.exists(statusline_path):
                backup_success = self.config_generator.create_backup(statusline_path)

            return backup_success

        except Exception:
            return False

    def get_setup_status(self, project_dir: str = '.') -> Dict[str, Any]:
        """
        프로젝트 설정 상태 확인

        Args:
            project_dir (str): 프로젝트 디렉토리 경로

        Returns:
            Dict[str, Any]: 설정 상태 정보
        """
        try:
            detected_os = self.get_detected_os()
            is_supported = self.is_platform_supported()

            # 설정 파일 존재 확인
            mcp_path = os.path.join(project_dir, '.mcp.json')
            claude_settings_path = os.path.join(project_dir, '.claude', 'settings.json')
            statusline_path = os.path.join(project_dir, '.claude', 'statusline.json')

            configs_applied = {
                'mcp': os.path.exists(mcp_path),
                'claude_settings': os.path.exists(claude_settings_path),
                'statusline': os.path.exists(statusline_path)
            }

            # 백업 파일 확인
            backup_exists = False
            if self.backup_enabled and os.path.exists(self.backup_dir):
                backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.backup')]
                backup_exists = len(backup_files) > 0

            return {
                'platform_detected': detected_os,
                'is_supported': is_supported,
                'configs_applied': configs_applied,
                'backup_exists': backup_exists,
                'platform_details': self.detector.get_detailed_info(),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'platform_detected': self.get_detected_os(),
                'is_supported': self.is_platform_supported(),
                'configs_applied': {},
                'backup_exists': False,
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }

    def validate_config(self, config: Dict[str, Any], config_type: str) -> bool:
        """
        설정 유효성 검사

        Args:
            config (Dict[str, Any]): 검증할 설정
            config_type (str): 설정 종류 ('mcp', 'statusline', 'claude_settings')

        Returns:
            bool: 유효성 검사 결과
        """
        try:
            return self.config_generator.validate_config(config, config_type)
        except Exception:
            return False

    def get_setup_summary(self) -> Dict[str, Any]:
        """
        설정 요약 정보 반환

        Returns:
            Dict[str, Any]: 설정 요약
        """
        try:
            detected_os = self.get_detected_os()
            is_supported = self.is_platform_supported()

            # 현재 설정 정보 가져오기
            config_summary = self.config_generator.get_config_summary()

            # 설정 생성 예시
            mcp_config = self.config_generator.generate_mcp_config()
            statusline_config = self.config_generator.generate_statusline_config()
            claude_config = self.config_generator.generate_claude_settings()

            # 권장사항 생성
            recommendations = []
            if not is_supported:
                recommendations.append(f"Unsupported platform: {detected_os}")
            else:
                # 플랫폼별 권장사항
                if detected_os == 'windows':
                    recommendations.append("Windows 환경에서는 cmd /c 명령어를 사용합니다")
                    recommendations.append("인코딩 문제 발생 시 UTF-8 확인이 필요할 수 있습니다")
                elif detected_os in ['macos', 'linux']:
                    recommendations.append(f"{detected_os} 환경에서는 bash -c 명령어를 사용합니다")

                if not config_summary.get('is_supported', False):
                    recommendations.append("일부 설정이 지원되지 않을 수 있습니다")

            return {
                'platform': detected_os,
                'status': 'supported' if is_supported else 'unsupported',
                'configs': {
                    'mcp_servers': list(mcp_config.get('mcpServers', {}).keys()),
                    'statusline_command': statusline_config.get('command', 'unknown'),
                    'claude_statusline_command': claude_config.get('claude', {}).get('statusline', {}).get('command', 'unknown')
                },
                'recommendations': recommendations,
                'platform_details': self.detector.get_detailed_info()
            }

        except Exception as e:
            return {
                'platform': self.get_detected_os(),
                'status': 'error',
                'error': str(e),
                'configs': {},
                'recommendations': ['Setup error occurred'],
                'platform_details': {}
            }

    def get_help(self) -> str:
        """
        도움말 정보 반환

        Returns:
            str: 도움말 텍스트
        """
        help_text = """
MoAI-ADK 자동 설정 명령 사용법

기본 기능:
- 프로젝트 설정: setup_project(project_dir)
- MCP 설정만 적용: setup_mcp_config(project_dir)
- Statusline 설정만 적용: setup_statusline_config(project_dir)
- Claude 설정만 적용: setup_claude_config(project_dir)
- 설정 롤백: rollback_config(filepath)
- 설정 상태 확인: get_setup_status(project_dir)

사용 예시:
```python
# 프로젝트 루트 디렉토리에서 전체 설정
setup_cmd = SetupCommand()
result = setup_cmd.setup_project('.')

# 특정 설정만 적용
mcp_result = setup_cmd.setup_mcp_config('./my-project')

# 설정 상태 확인
status = setup_cmd.get_setup_status('.')
```

주의사항:
- 백업 기능이 활성화된 경우 기존 설정이 자동으로 백업됩니다
- 지원되는 플랫폼: Windows, macOS, Linux
- 설정 파일: .mcp.json, .claude/settings.json, .claude/statusline.json
        """
        return help_text

    def dry_run_setup(self, project_dir: str = '.') -> Dict[str, Any]:
        """
        드라이 럴 실행 (실제 설정 적용 없이 예상 결과 확인)

        Args:
            project_dir (str): 프로젝트 디렉토리 경로

        Returns:
            Dict[str, Any]: 드라이 럴 결과
        """
        try:
            detected_os = self.get_detected_os()
            is_supported = self.is_platform_supported()

            # 설정 파일 경로
            mcp_path = os.path.join(project_dir, '.mcp.json')
            claude_settings_path = os.path.join(project_dir, '.claude', 'settings.json')
            statusline_path = os.path.join(project_dir, '.claude', 'statusline.json')

            # 현재 파일 상태 확인
            existing_files = {
                'mcp': os.path.exists(mcp_path),
                'claude_settings': os.path.exists(claude_settings_path),
                'statusline': os.path.exists(statusline_path)
            }

            # 생성될 설정 예시
            mcp_config = self.config_generator.generate_mcp_config()
            claude_config = self.config_generator.generate_claude_settings()
            statusline_config = self.config_generator.generate_statusline_config()

            # 영향 평가
            impact = 'low'
            if any(existing_files.values()):
                impact = 'medium'
            if detected_os == 'windows':
                impact = 'medium'  # Windows 인코딩 영향

            return {
                'platform_detected': detected_os,
                'is_supported': is_supported,
                'would_create': {
                    'mcp.json': not existing_files['mcp'],
                    'claude/settings.json': not existing_files['claude_settings'],
                    'claude/statusline.json': not existing_files['statusline']
                },
                'would_modify': existing_files,
                'estimated_impact': impact,
                'preview_configs': {
                    'mcp_servers': list(mcp_config.get('mcpServers', {}).keys()),
                    'platform_specific': detected_os,
                    'backup_enabled': self.backup_enabled
                }
            }

        except Exception as e:
            return {
                'platform_detected': self.get_detected_os(),
                'is_supported': self.is_platform_supported(),
                'error': str(e),
                'would_create': {},
                'would_modify': {},
                'estimated_impact': 'unknown'
            }

    def validate_setup(self, project_dir: str = '.') -> Dict[str, Any]:
        """
        설정 유효성 검사

        Args:
            project_dir (str): 프로젝트 디렉토리 경로

        Returns:
            Dict[str, Any]: 유효성 검사 결과
        """
        try:
            status = self.get_setup_status(project_dir)
            result = {
                'is_valid': True,
                'config_validations': {},
                'overall_status': 'valid',
                'issues': []
            }

            # MCP 설정 유효성 검사
            mcp_path = os.path.join(project_dir, '.mcp.json')
            if os.path.exists(mcp_path):
                try:
                    with open(mcp_path, 'r', encoding='utf-8') as f:
                        mcp_config = json.load(f)
                    mcp_valid = self.validate_config(mcp_config, 'mcp')
                    result['config_validations']['mcp'] = mcp_valid
                    if not mcp_valid:
                        result['issues'].append('MCP 설정 유효성 검사 실패')
                        result['is_valid'] = False
                except Exception:
                    result['config_validations']['mcp'] = False
                    result['issues'].append('MCP 설정 파일 읽기 오류')
                    result['is_valid'] = False

            # Claude 설정 유효성 검사
            claude_settings_path = os.path.join(project_dir, '.claude', 'settings.json')
            if os.path.exists(claude_settings_path):
                try:
                    with open(claude_settings_path, 'r', encoding='utf-8') as f:
                        claude_config = json.load(f)
                    claude_valid = self.validate_config(claude_config, 'claude_settings')
                    result['config_validations']['claude_settings'] = claude_valid
                    if not claude_valid:
                        result['issues'].append('Claude 설정 유효성 검사 실패')
                        result['is_valid'] = False
                except Exception:
                    result['config_validations']['claude_settings'] = False
                    result['issues'].append('Claude 설정 파일 읽기 오류')
                    result['is_valid'] = False

            # 전체 상태 업데이트
            if not result['is_valid']:
                result['overall_status'] = 'invalid'
            elif not result['config_validations']:
                result['overall_status'] = 'no_configs'
            else:
                result['overall_status'] = 'valid'

            return result

        except Exception as e:
            return {
                'is_valid': False,
                'overall_status': 'error',
                'error': str(e),
                'config_validations': {},
                'issues': ['Validation error occurred']
            }