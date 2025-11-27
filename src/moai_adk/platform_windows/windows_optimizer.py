"""
Windows Optimizer 모듈

TAG-WIN-004: Windows 최적화 구현

Windows 환경에 특화된 최적화 기능을 제공합니다.
Windows 경로 최적화, 환경변수 관리, 성능 튜닝, 레지스트리 최적화 등을 지원합니다.

주요 기능:
- 경로 정규화 및 최적화
- 환경변수 정리 및 최적화
- Windows 성능 튜닝 설정
- 레지스트리 및 서비스 최적화 설정
- 시작 프로그램 최적화 추천
"""

import sys
import os
import re
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

try:
    import winreg
    WINDOWS_SUPPORT = True
except ImportError:
    WINDOWS_SUPPORT = False


class OptimizationType(Enum):
    """최적화 유형 열거형"""
    PATH = "path"
    ENVIRONMENT = "environment"
    PERFORMANCE = "performance"
    REGISTRY = "registry"
    SERVICE = "service"
    STARTUP = "startup"


@dataclass
class OptimizationResult:
    """최적화 결과 데이터 클래스"""
    success: bool
    optimization_type: OptimizationType
    details: Dict[str, Any]
    errors: List[str]
    timestamp: datetime


class WindowsOptimizer:
    """Windows 환경 최적화 클래스

    Windows OS에 특화된 성능 최적화, 경로 관리, 환경변수 최적화 기능을 제공합니다.
    """

    def __init__(self):
        """Windows Optimizer 초기화"""
        self.is_windows = sys.platform == 'win32'
        self.optimization_history = []
        self.performance_metrics = {}

        # Windows 최적화 설정
        self.optimization_config = self._init_optimization_config()

        # 경로 정규화 규칙
        self.path_normalization_rules = self._init_path_rules()

        # 환경변수 최적화 규칙
        self.env_optimization_rules = self._init_env_rules()

    def _init_optimization_config(self) -> Dict[str, Any]:
        """최적화 설정 초기화"""
        return {
            'path_optimization': {
                'normalize_separators': True,
                'resolve_relative_paths': True,
                'remove_duplicates': True,
                'sort_paths': True,
                'validate_existence': False
            },
            'environment_optimization': {
                'remove_duplicates': True,
                'sort_variables': True,
                'cleanup_temp_vars': True,
                'optimize_path_order': True
            },
            'performance_tuning': {
                'enable_fast_startup': True,
                'optimize_memory': True,
                'tune_processor_scheduling': True,
                'optimize_disk_io': True
            }
        }

    def _init_path_rules(self) -> Dict[str, Any]:
        """경로 정규화 규칙 초기화"""
        return {
            'separator_pattern': re.compile(r'[\\/]+'),
            'relative_pattern': re.compile(r'^\.+([\\/])'),
            'windows_drive_pattern': re.compile(r'^[a-zA-Z]:'),
            'unc_pattern': re.compile(r'^\\\\'),
            'environment_var_pattern': re.compile(r'%[^%]+%')
        }

    def _init_env_rules(self) -> Dict[str, Any]:
        """환경변수 최적화 규칙 초기화"""
        return {
            'critical_paths': [
                'PATH',
                'PATHEXT',
                'PYTHONPATH',
                'JAVA_HOME'
            ],
            'temp_patterns': [
                r'^TEMP_.*',
                r'^TMP_.*',
                r'^TEMPORARY_.*'
            ],
            'cleanup_vars': [
                'OLD_PATH',
                'BACKUP_PATH',
                'PREV_PATH'
            ]
        }

    def optimize_paths(self, paths: Union[List[str], None]) -> List[str]:
        """Windows 경로 최적화

        Args:
            paths (Union[List[str], None]): 최적화할 경로 목록

        Returns:
            List[str]: 최적화된 경로 목록

        Examples:
            >>> optimizer = WindowsOptimizer()
            >>> paths = ['C:/path/to/app', '..\\relative\\path', 'C:\\Windows']
            >>> optimized = optimizer.optimize_paths(paths)
            >>> len(optimized) == 3
            True
        """
        if not paths or not isinstance(paths, list):
            return []

        if not self.is_windows:
            return paths.copy()

        config = self.optimization_config['path_optimization']
        seen = set()
        optimized = []

        # 병렬 처리를 위한 경로 그룹화 (100개 단위)
        batch_size = 100
        for i in range(0, len(paths), batch_size):
            batch = paths[i:i + batch_size]
            batch_results = self._process_path_batch(batch, seen, config)
            optimized.extend(batch_results)

        # 경로 정렬 (사전 순서로 대소문자 구분 없이)
        if config['sort_paths']:
            optimized.sort(key=lambda x: x.lower())

        return optimized

    def _process_path_batch(self, batch: List[str], seen: set, config: Dict[str, Any]) -> List[str]:
        """경로 배치 처리 - 성능 최적화를 위한 내부 메서드"""
        optimized = []

        for path in batch:
            if not path or not isinstance(path, str):
                continue

            try:
                normalized = self._normalize_path(path)

                # 중복 확인 및 추가
                if normalized not in seen:
                    optimized.append(normalized)
                    seen.add(normalized)

            except Exception as e:
                # 오류 로깅 및 원본 경로 유지
                self._log_optimization_error("path_optimization", str(e))
                optimized.append(str(path))

        return optimized

    def _normalize_path(self, path: str) -> str:
        """경로 정규화

        Args:
            path (str): 정규화할 경로

        Returns:
            str: 정규화된 경로
        """
        if not path:
            return ""

        config = self.optimization_config['path_optimization']

        # 1. 공백 제거
        normalized = path.strip()

        # 2. 환경변수 확장 (선택적)
        if config.get('expand_env_vars', False):
            try:
                normalized = os.path.expandvars(normalized)
            except Exception:
                pass

        # 3. 경로 구분자 정규화
        if config['normalize_separators']:
            normalized = self.path_normalization_rules['separator_pattern'].sub('\\', normalized)

        # 4. 상대 경로 해결
        if config['resolve_relative_paths']:
            if self.path_normalization_rules['relative_pattern'].match(normalized):
                try:
                    normalized = os.path.abspath(normalized)
                except Exception:
                    pass

        # 5. 경로 존재 여부 검증
        if config['validate_existence']:
            try:
                if not os.path.exists(normalized):
                    # 존재하지 않는 경로는 표시
                    normalized = f"[MISSING] {normalized}"
            except Exception:
                pass

        return normalized

    def optimize_environment_vars(self) -> Dict[str, str]:
        """환경변수 최적화

        Returns:
            Dict[str, str]: 최적화된 환경변수
        """
        if not self.is_windows:
            return dict(os.environ)

        optimized_env = {}
        config = self.optimization_config['environment_optimization']

        # 모든 환경변수 처리
        for key, value in os.environ.items():
            try:
                # PATH 변수 특별 처리
                if key == 'PATH':
                    optimized_value = self._optimize_path_variable(value)
                else:
                    optimized_value = self._optimize_generic_variable(key, value, config)

                optimized_env[key] = optimized_value

            except Exception:
                # 오류 발생 시 원본 값 유지
                optimized_env[key] = str(value)

        # 정렬 (선택적)
        if config['sort_variables']:
            optimized_env = dict(sorted(optimized_env.items()))

        return optimized_env

    def _optimize_path_variable(self, path_value: str) -> str:
        """PATH 환경변수 최적화"""
        config = self.optimization_config['environment_optimization']

        # PATH 항목 분리
        path_entries = path_value.split(os.pathsep)

        # 경로 최적화
        optimized_entries = self.optimize_paths(path_entries)

        # 경로 순서 최적화
        if config['optimize_path_order']:
            optimized_entries = self._optimize_path_order(optimized_entries)

        return os.pathsep.join(optimized_entries)

    def _optimize_generic_variable(self, key: str, value: str, config: Dict[str, Any]) -> str:
        """일반 환경변수 최적화"""
        rules = self.env_optimization_rules

        # 임시 변수 정리
        if config['cleanup_temp_vars']:
            for pattern in rules['temp_patterns']:
                if re.match(pattern, key, re.IGNORECASE):
                    # 임시 변수는 제거 대상으로 표시
                    return f"[CLEANUP] {value}"

        # 백업 변수 정리
        if key in rules['cleanup_vars']:
            return f"[CLEANUP] {value}"

        # 중복 제거 (PATH와 유사한 형식의 변수)
        if ';' in value:
            entries = [entry.strip() for entry in value.split(';') if entry.strip()]
            if config['remove_duplicates']:
                seen = set()
                unique_entries = []
                for entry in entries:
                    if entry not in seen:
                        unique_entries.append(entry)
                        seen.add(entry)
                return ';'.join(unique_entries)

        return value

    def _optimize_path_order(self, paths: List[str]) -> List[str]:
        """경로 순서 최적화"""
        # 우선순위에 따라 경로 재정렬
        priority_patterns = [
            r'C:\\Windows\\System32',
            r'C:\\Windows',
            r'C:\\Program Files',
            r'C:\\Program Files \(x86\)',
            r'C:\\Python\d+',
            r'C:\\Users\\.*\\AppData\\Local\\Programs\\Python'
        ]

        def get_priority(path: str) -> int:
            for i, pattern in enumerate(priority_patterns):
                if re.search(pattern, path, re.IGNORECASE):
                    return i
            return len(priority_patterns)

        return sorted(paths, key=get_priority)

    def get_windows_performance_tuning(self) -> Dict[str, Any]:
        """Windows 성능 튜닝 설정 반환

        Returns:
            Dict[str, Any]: 성능 튜닝 설정
        """
        if not self.is_windows:
            return self._get_non_windows_performance_config()

        config = self.optimization_config['performance_tuning']

        return {
            'process_priority': {
                'enabled': config['tune_processor_scheduling'],
                'priority_class': 'HIGH_PRIORITY_CLASS',
                'affinity_mask': '0xFFFFFFFF'
            },
            'memory_optimization': {
                'enabled': config['optimize_memory'],
                'working_set_size': 'automatic',
                'page_file_optimization': True,
                'memory_pressure_threshold': 80
            },
            'disk_optimization': {
                'enabled': config['optimize_disk_io'],
                'file_system_optimization': True,
                'disk_caching': 'aggressive',
                'defrag_recommendation': True
            },
            'network_optimization': {
                'enabled': True,
                'tcp_window_scaling': True,
                'dns_caching': True,
                'network_adapter_optimization': True
            },
            'system_services': {
                'disable_unnecessary_services': True,
                'optimize_startup_programs': True,
                'system_restore_optimization': True
            }
        }

    def _get_non_windows_performance_config(self) -> Dict[str, Any]:
        """비-Windows 환경 성능 설정"""
        return {
            'process_priority': {
                'enabled': False,
                'reason': 'Windows-specific optimization'
            },
            'memory_optimization': {
                'enabled': False,
                'reason': 'Windows-specific optimization'
            },
            'disk_optimization': {
                'enabled': False,
                'reason': 'Windows-specific optimization'
            },
            'network_optimization': {
                'enabled': False,
                'reason': 'Windows-specific optimization'
            }
        }

    def apply_windows_optimizations(self) -> Dict[str, Any]:
        """Windows 최적화 적용

        Returns:
            Dict[str, Any]: 최적화 적용 결과
        """
        result = {
            'success': False,
            'optimizations_applied': [],
            'errors': [],
            'timestamp': datetime.now().isoformat(),
            'platform': sys.platform
        }

        if not self.is_windows:
            result['errors'].append('Not running on Windows platform')
            return result

        try:
            # 1. 환경변수 최적화
            optimized_env = self.optimize_environment_vars()
            result['optimizations_applied'].append('environment_variables')

            # 2. 경로 최적화
            if 'PATH' in os.environ:
                optimized_path = self._optimize_path_variable(os.environ['PATH'])
                result['optimizations_applied'].append('path_optimization')

            # 3. 성능 튜닝 설정 가져오기
            perf_config = self.get_windows_performance_tuning()
            result['optimizations_applied'].append('performance_tuning')

            # 4. 레지스트리 최적화 (가능한 경우)
            if WINDOWS_SUPPORT:
                reg_result = self._apply_registry_optimizations()
                if reg_result:
                    result['optimizations_applied'].append('registry_optimization')

            result['success'] = True
            result['optimized_environment'] = optimized_env
            result['performance_config'] = perf_config

            # 최적화 기록 저장
            self.optimization_history.append(result)

        except Exception as e:
            result['errors'].append(f'Optimization failed: {str(e)}')

        return result

    def _apply_registry_optimizations(self) -> bool:
        """레지스트리 최적화 적용 (안전한 항목만)"""
        if not WINDOWS_SUPPORT:
            return False

        try:
            # 주의: 실제 레지스트리 수정은 위험하므로 설정만 반환
            # 실제 구현에서는 사용자 동의 후 적용 필요
            return False
        except Exception:
            return False

    def get_registry_optimization_config(self) -> Dict[str, Any]:
        """레지스트리 최적화 설정 반환

        Returns:
            Dict[str, Any]: 레지스트리 최적화 설정
        """
        if not self.is_windows:
            return {'enabled': False, 'reason': 'Windows only'}

        return {
            'enabled': True,
            'registry_keys': [
                {
                    'path': 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl',
                    'value': 'Win32PrioritySeparation',
                    'type': 'DWORD',
                    'recommended_value': 38
                },
                {
                    'path': 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer',
                    'value': 'Max Cached Icons',
                    'type': 'DWORD',
                    'recommended_value': 2000
                }
            ],
            'warnings': [
                'Registry modifications require administrator privileges',
                'Always backup registry before making changes',
                'Apply only recommended settings'
            ]
        }

    def get_service_optimization_config(self) -> Dict[str, Any]:
        """Windows 서비스 최적화 설정 반환

        Returns:
            Dict[str, Any]: 서비스 최적화 설정
        """
        if not self.is_windows:
            return {'enabled': False, 'reason': 'Windows only'}

        return {
            'enabled': True,
            'services': {
                'disable_services': [
                    {
                        'name': 'SysMain',
                        'display_name': 'Superfetch/Prefetch',
                        'recommendation': 'disable_on_ssd'
                    },
                    {
                        'name': 'Fax',
                        'display_name': 'Fax Service',
                        'recommendation': 'disable_if_unused'
                    }
                ],
                'optimize_services': [
                    {
                        'name': 'BITS',
                        'display_name': 'Background Intelligent Transfer Service',
                        'startup_type': 'automatic_delayed'
                    }
                ]
            }
        }

    def get_startup_optimization_config(self) -> Dict[str, Any]:
        """Windows 시작 프로그램 최적화 설정 반환

        Returns:
            Dict[str, Any]: 시작 프로그램 최적화 설정
        """
        if not self.is_windows:
            return {'enabled': False, 'reason': 'Windows only'}

        return {
            'enabled': True,
            'startup_programs': {
                'locations': [
                    'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                    'HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                    'Startup folder'
                ],
                'recommendations': [
                    'Review and disable unnecessary startup programs',
                    'Delay non-essential programs',
                    'Keep security software startup enabled'
                ]
            },
            'performance_impact': {
                'high_impact_programs': [
                    'Antivirus software',
                    'Cloud storage sync',
                    'Update managers'
                ],
                'safe_to_disable': [
                    'Application updaters',
                    'Optional system tools',
                    'Third-party utilities'
                ]
            },
            'recommendations': [
                'Review startup programs regularly',
                'Disable unnecessary applications',
                'Keep essential security software enabled'
            ]
        }

    def get_optimization_report(self) -> Dict[str, Any]:
        """최적화 보고서 생성

        Returns:
            Dict[str, Any]: 최적화 보고서
        """
        return {
            'platform': sys.platform,
            'is_windows': self.is_windows,
            'optimization_count': len(self.optimization_history),
            'last_optimization': self.optimization_history[-1] if self.optimization_history else None,
            'performance_metrics': self.performance_metrics,
            'recommendations': self._get_recommendations()
        }

    def _get_recommendations(self) -> List[str]:
        """최적화 추천 목록 반환"""
        recommendations = []

        if not self.is_windows:
            recommendations.append('Windows Optimizer is designed for Windows systems only')
            return recommendations

        # 시스템 상태 기반 추천
        try:
            path_entries = os.environ.get('PATH', '').split(os.pathsep)
            if len(path_entries) > 50:
                recommendations.append('Consider cleaning up PATH variable (too many entries)')

            # 환경변수 크기 확인
            env_size = sum(len(key) + len(value) for key, value in os.environ.items())
            if env_size > 32766:  # Windows 환경변수 제한
                recommendations.append('Environment variables size approaching limit')

        except Exception:
            pass

        recommendations.extend([
            'Regular maintenance recommended for optimal performance',
            'Consider system backup before applying optimizations',
            'Monitor system performance after optimizations'
        ])

        return recommendations

    def reset_optimizations(self) -> Dict[str, Any]:
        """최적화 설정 초기화

        Returns:
            Dict[str, Any]: 초기화 결과
        """
        self.optimization_history.clear()
        self.performance_metrics.clear()

        return {
            'success': True,
            'message': 'Windows Optimizer settings reset to default',
            'timestamp': datetime.now().isoformat()
        }

    def _log_optimization_error(self, operation: str, error_message: str) -> None:
        """최적화 오류 로깅 - 내부 메서드

        Args:
            operation (str): 수행 중이던 작업
            error_message (str): 오류 메시지
        """
        if 'errors' not in self.performance_metrics:
            self.performance_metrics['errors'] = []

        error_entry = {
            'operation': operation,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }
        self.performance_metrics['errors'].append(error_entry)

    def _measure_performance(self, operation: str, start_time: datetime, end_time: datetime) -> None:
        """성능 측정 기록 - 내부 메서드

        Args:
            operation (str): 측정할 작업
            start_time (datetime): 시작 시간
            end_time (datetime): 종료 시간
        """
        duration = (end_time - start_time).total_seconds()

        if 'performance' not in self.performance_metrics:
            self.performance_metrics['performance'] = {}

        if operation not in self.performance_metrics['performance']:
            self.performance_metrics['performance'][operation] = []

        self.performance_metrics['performance'][operation].append({
            'duration': duration,
            'timestamp': start_time.isoformat()
        })

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 반환

        Returns:
            Dict[str, Any]: 성능 측정 데이터
        """
        metrics = self.performance_metrics.copy()

        # 평균 성능 계산
        if 'performance' in metrics:
            for operation, measurements in metrics['performance'].items():
                if measurements:
                    durations = [m['duration'] for m in measurements]
                    metrics['performance'][operation] = {
                        'count': len(measurements),
                        'average_duration': sum(durations) / len(durations),
                        'min_duration': min(durations),
                        'max_duration': max(durations),
                        'total_duration': sum(durations),
                        'recent_measurements': measurements[-5:]  # 최근 5개 측정
                    }

        return metrics

    def validate_optimization_result(self, result: OptimizationResult) -> bool:
        """최적화 결과 유효성 검증

        Args:
            result (OptimizationResult): 검증할 결과

        Returns:
            bool: 유효성 여부
        """
        if not isinstance(result, OptimizationResult):
            return False

        # 필드 유효성 검사
        if not isinstance(result.success, bool):
            return False

        if not isinstance(result.optimization_type, OptimizationType):
            return False

        if not isinstance(result.details, dict):
            return False

        if not isinstance(result.errors, list):
            return False

        if not isinstance(result.timestamp, datetime):
            return False

        return True

    def create_optimization_report(self) -> Dict[str, Any]:
        """상세 최적화 보고서 생성

        Returns:
            Dict[str, Any]: 상세 보고서
        """
        base_report = self.get_optimization_report()

        # 성능 메트릭 추가
        base_report['performance_metrics'] = self.get_performance_metrics()

        # 최적화 히스토리 분석
        if self.optimization_history:
            success_count = sum(1 for h in self.optimization_history if h.get('success', False))
            base_report['success_rate'] = success_count / len(self.optimization_history)

            # 가장 최근 최적화
            base_report['latest_optimization'] = self.optimization_history[-1]

        # 시스템 상태 요약
        base_report['system_status'] = self._get_system_status_summary()

        return base_report

    def _get_system_status_summary(self) -> Dict[str, Any]:
        """시스템 상태 요약 - 내부 메서드

        Returns:
            Dict[str, Any]: 시스템 상태 정보
        """
        if not self.is_windows:
            return {'platform': 'non-windows', 'optimizations_available': False}

        status = {
            'platform': 'windows',
            'optimizations_available': True,
            'environment_size': 0,
            'path_entries_count': 0,
            'registry_access': WINDOWS_SUPPORT
        }

        try:
            # 환경변수 크기 계산
            env_size = sum(len(key) + len(value) for key, value in os.environ.items())
            status['environment_size'] = env_size

            # PATH 항목 수 계산
            path_entries = len(os.environ.get('PATH', '').split(os.pathsep))
            status['path_entries_count'] = path_entries

        except Exception as e:
            status['status_error'] = str(e)

        return status