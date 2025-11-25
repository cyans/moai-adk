"""
ConfigGenerator 모듈

TAG-WIN-003: 동적 설정 생성기 개발

OS 감지 결과를 바탕으로 동적으로 설정 파일을 생성하고 적용합니다.
PlatformDetector와 ConfigTemplates를 조합하여 최적화된 설정을 생성합니다.
"""

import json
import os
import shutil
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from moai_adk.platform.detector import PlatformDetector
from moai_adk.platform.templates import ConfigTemplates

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


class ConfigGenerator:
    """동적 설정 생성기 클래스"""

    def __init__(self):
        """ConfigGenerator 초기화"""
        self.detector = PlatformDetector()
        self.templates = ConfigTemplates()
        self.backup_dir = '.moai/backup'

    def generate_config(self, os_type: str = None) -> Dict[str, Any]:
        """
        설정 동적 생성 (호환성을 위한 메서드)

        Args:
            os_type (str): OS 종류 (None이면 자동 감지)

        Returns:
            Dict[str, Any]: 설정
        """
        if os_type is None:
            os_type = self.detector.detect_os()

        return {
            'statusline': self.templates.get_statusline_template(os_type),
            'platform': os_type,
            'detected_os': os_type,
            'generated_at': datetime.now().isoformat()
        }

    def generate_mcp_config(self) -> Dict[str, Any]:
        """
        MCP 설정 동적 생성
        .mcp.json 파일을 읽어서 플랫폼에 맞게 자동 변환합니다.

        Returns:
            Dict[str, Any]: MCP 설정 (플랫폼에 맞게 변환됨)
        """
        # 먼저 .mcp.json 파일이 있는지 확인
        mcp_file_path = '.mcp.json'
        if os.path.exists(mcp_file_path):
            try:
                with open(mcp_file_path, 'r', encoding='utf-8') as f:
                    mcp_config = json.load(f)
                
                # Windows에서 npx 명령을 cmd로 변환
                os_type = self.detector.detect_os()
                if os_type == 'windows' and 'mcpServers' in mcp_config:
                    for server_name, server_config in mcp_config['mcpServers'].items():
                        # SSE 타입은 변환하지 않음
                        if server_config.get('type') == 'sse':
                            continue
                        
                        # command가 npx인 경우 Windows에서 cmd로 변환
                        if server_config.get('command') == 'npx':
                            server_config['command'] = 'cmd'
                            original_args = server_config.get('args', [])
                            server_config['args'] = ['/c', 'npx'] + original_args
                
                return mcp_config
            except (JSONDecodeError, OSError, Exception):
                # 파일 읽기 실패 시 템플릿 사용
                pass
        
        # 파일이 없거나 읽기 실패 시 템플릿 사용
        os_type = self.detector.detect_os()
        return self.templates.get_mcp_template(os_type)

    def generate_statusline_config(self) -> Dict[str, Any]:
        """
        Statusline 설정 동적 생성

        Returns:
            Dict[str, Any]: Statusline 설정
        """
        os_type = self.detector.detect_os()
        return self.templates.get_statusline_template(os_type)

    def generate_claude_settings(self) -> Dict[str, Any]:
        """
        Claude 설정 동적 생성

        Returns:
            Dict[str, Any]: Claude 설정
        """
        os_type = self.detector.detect_os()
        return self.templates.get_claude_settings_template(os_type)

    def apply_config(self, config: Dict[str, Any], filepath: str) -> bool:
        """
        설정 파일 적용

        Args:
            config (Dict[str, Any]): 적용할 설정
            filepath (str): 설정 파일 경로

        Returns:
            bool: 적용 성공 여부
        """
        try:
            # 백업 생성
            self.create_backup(filepath)

            # 디렉토리 생성
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # 설정 파일 쓰기
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True

        except (OSError, JSONDecodeError, Exception):
            return False

    def generate_optimized_config(self) -> Dict[str, Any]:
        """
        최적화된 설정 전체 생성

        Returns:
            Dict[str, Any]: 최적화된 설정
        """
        os_type = self.detector.detect_os()
        is_valid = self.detector.validate_platform()

        return {
            'mcp': self.generate_mcp_config(),
            'statusline': self.generate_statusline_config(),
            'claude_settings': self.generate_claude_settings(),
            'detected_os': os_type,
            'is_valid': is_valid,
            'generated_at': datetime.now().isoformat(),
            'platform_info': self.detector.get_detailed_info()
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
            return self.templates.validate_template(config, config_type)
        except Exception:
            return False

    def create_backup(self, filepath: str) -> bool:
        """
        설정 파일 백업

        Args:
            filepath (str): 백업할 파일 경로

        Returns:
            bool: 백업 성공 여부
        """
        try:
            # 백업 디렉토리 생성
            os.makedirs(self.backup_dir, exist_ok=True)

            # 파일이 존재할 경우에만 백업
            if os.path.exists(filepath):
                # 백업 파일 경로 생성
                backup_path = f"{filepath}.backup.{int(datetime.now().timestamp())}"
                # 파일 복사
                shutil.copy2(filepath, backup_path)

            return True

        except Exception:
            return False

    def restore_backup(self, filepath: str) -> bool:
        """
        설정 파일 복원

        Args:
            filepath (str): 복원할 파일 경로

        Returns:
            bool: 복원 성공 여부
        """
        try:
            # 가장 최신 백업 파일 찾기
            backup_pattern = f"{filepath}.backup.*"
            backup_files = []

            for file in os.listdir(self.backup_dir):
                if file.startswith(f"{os.path.basename(filepath)}.backup."):
                    backup_files.append(os.path.join(self.backup_dir, file))

            if not backup_files:
                return False

            # 가장 최신 백업 파일 선택
            latest_backup = max(backup_files, key=os.path.getctime)

            # 백업 파일 복원
            shutil.copy2(latest_backup, filepath)

            return True

        except Exception:
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """
        설정 요약 정보 반환

        Returns:
            Dict[str, Any]: 설정 요약
        """
        os_type = self.detector.detect_os()
        is_valid = self.detector.validate_platform()

        return {
            'current_os': os_type,
            'is_supported': is_valid,
            'mcp_servers': list(self.generate_mcp_config().get('mcpServers', {}).keys()),
            'statusline_command': self.generate_statusline_config()['command'],
            'claude_statusline_command': self.generate_claude_settings()['claude']['statusline']['command'],
            'platform_details': self.detector.get_detailed_info()
        }

    def apply_all_configs(self, base_dir: str = '.') -> Dict[str, bool]:
        """
        모든 설정 파일 일괄 적용

        Args:
            base_dir (str): 기본 디렉토리

        Returns:
            Dict[str, bool]: 각 설정 파일 적용 결과
        """
        results = {}

        # .mcp.json 경로
        mcp_path = os.path.join(base_dir, '.mcp.json')
        # Windows에서 실제 파일에 저장할 때는 변환된 형식으로 저장
        mcp_config = self.generate_mcp_config()
        # Windows인 경우 변환된 형식으로 딕셔너리 복사본 생성 (원본 수정 방지)
        os_type = self.detector.detect_os()
        if os_type == 'windows':
            import copy
            mcp_config = copy.deepcopy(mcp_config)
            if 'mcpServers' in mcp_config:
                for server_name, server_config in mcp_config['mcpServers'].items():
                    # SSE 타입은 변환하지 않음
                    if server_config.get('type') == 'sse':
                        continue
                    # command가 npx인 경우 Windows에서 cmd로 변환
                    if server_config.get('command') == 'npx':
                        server_config['command'] = 'cmd'
                        original_args = server_config.get('args', [])
                        server_config['args'] = ['/c', 'npx'] + original_args
        results['mcp'] = self.apply_config(mcp_config, mcp_path)

        # .claude/settings.json 경로
        claude_settings_path = os.path.join(base_dir, '.claude', 'settings.json')
        claude_settings = self.generate_claude_settings()
        results['claude_settings'] = self.apply_config(claude_settings, claude_settings_path)

        return results

    def rollback_config(self, filepath: str) -> bool:
        """
        설정 롤백

        Args:
            filepath (str): 롤백할 파일 경로

        Returns:
            bool: 롤백 성공 여부
        """
        return self.restore_backup(filepath)

    def get_config_diff(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        설정 차이 비교

        Args:
            old_config (Dict[str, Any]): 이전 설정
            new_config (Dict[str, Any]): 새 설정

        Returns:
            Dict[str, Any]: 설정 차이
        """
        diff = {}

        def compare_dicts(old: Any, new: Any, path: str = ''):
            if isinstance(old, dict) and isinstance(new, dict):
                for key in set(old.keys()) | set(new.keys()):
                    current_path = f"{path}.{key}" if path else key
                    if key not in old:
                        diff[current_path] = {'added': new[key]}
                    elif key not in new:
                        diff[current_path] = {'removed': old[key]}
                    elif old[key] != new[key]:
                        if isinstance(old[key], dict) and isinstance(new[key], dict):
                            compare_dicts(old[key], new[key], current_path)
                        else:
                            diff[current_path] = {
                                'old': old[key],
                                'new': new[key]
                            }
            elif old != new:
                diff[path] = {
                    'old': old,
                    'new': new
                }

        compare_dicts(old_config, new_config)
        return diff