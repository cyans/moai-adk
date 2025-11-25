# type: ignore
"""
Statusline renderer

TAG-WIN-005: Statusline Solution 구현
"""

from typing import Dict, Any
try:
    from .data import StatuslineData
except ImportError:
    from data import StatuslineData


class StatuslineRenderer:
    """Statusline 렌더러 클래스"""

    def __init__(self):
        """StatuslineRenderer 초기화"""
        self.default_colors = {
            'model': '->',
            'directory': 'dir',
            'branch': 'git',
            'task': 'task',
            'style': 'style'
        }
        # Windows 호환 가능한 이모지 매핑
        self.win_safe_emojis = {
            '🚀': '->',
            '📂': '[D]',
            '🌿': '[G]',
            '💭': '[T]',
            '✨': '[S]',
            '🔷': '[V]',
            '📊': '[S]',
            '⏱️': '[T]',
            '💡': '[T]',
            '🔄': '[U]'
        }

    def render(self, data: StatuslineData, mode: str = "compact") -> str:
        """
        Statusline 데이터를 문자열로 렌더링

        Args:
            data: StatuslineData 객체
            mode: 표시 모드 (compact, extended, minimal)

        Returns:
            str: 렌더링된 statusline 문자열
        """
        if mode == "minimal":
            return self._render_minimal(data)
        elif mode == "extended":
            return self._render_extended(data)
        else:  # compact
            return self._render_compact(data)

    def _render_compact(self, data: StatuslineData) -> str:
        """Compact 모드 렌더링"""
        parts = []

        # 모델 정보
        if data.model:
            model_icon = self.win_safe_emojis['🚀']
            parts.append(f"{model_icon}{data.model.replace('Claude', 'GOOS')}")  # Windows 최적화

        # 디렉토리
        if data.directory:
            dir_icon = self.win_safe_emojis['📂']
            parts.append(f"{dir_icon}{data.directory}")

        # 브랜치 정보
        if data.branch and data.branch != "unknown":
            branch_icon = self.win_safe_emojis['🌿']
            parts.append(f"{branch_icon}{data.branch}")

        # 활성 작업
        if data.active_task:
            parts.append(data.active_task)

        # 스타일 정보
        if data.output_style:
            style_icon = self.win_safe_emojis['✨']
            parts.append(f"{style_icon}{data.output_style}")

        return "│".join(parts)

    def _render_extended(self, data: StatuslineData) -> str:
        """Extended 모드 렌더링"""
        parts = []

        # 상세 정보 구성
        if data.model:
            model_icon = self.win_safe_emojis['🚀']
            parts.append(f"{model_icon} {data.model}")
        if data.claude_version:
            version_icon = self.win_safe_emojis['🔷']
            parts.append(f"{version_icon} {data.claude_version}")
        if data.directory:
            dir_icon = self.win_safe_emojis['📂']
            parts.append(f"{dir_icon} {data.directory}")
        if data.branch and data.branch != "unknown":
            branch_icon = self.win_safe_emojis['🌿']
            parts.append(f"{branch_icon} {data.branch}")
        if data.git_status:
            status_icon = self.win_safe_emojis['📊']
            parts.append(f"{status_icon} {data.git_status}")
        if data.duration:
            time_icon = self.win_safe_emojis['⏱️']
            parts.append(f"{time_icon} {data.duration}")
        if data.active_task:
            task_icon = self.win_safe_emojis['💭']
            parts.append(f"{task_icon} {data.active_task}")
        if data.output_style:
            style_icon = self.win_safe_emojis['✨']
            parts.append(f"{style_icon} {data.output_style}")
        if data.update_available and data.latest_version:
            update_icon = self.win_safe_emojis['🔄']
            parts.append(f"{update_icon} {data.latest_version}")

        return " │ ".join(parts)

    def _render_minimal(self, data: StatuslineData) -> str:
        """Minimal 모드 렌더링"""
        return f"{data.directory}│{data.branch}"