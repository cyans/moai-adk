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
            parts.append(f"🤖 {data.model}")

        # 디렉토리
        if data.directory:
            parts.append(f"📁 {data.directory}")

        # 브랜치 정보
        if data.branch and data.branch != "unknown":
            parts.append(f"🔀 {data.branch}")

        # 활성 작업
        if data.active_task:
            parts.append(data.active_task)

        # 스타일 정보
        if data.output_style:
            parts.append(f"💬 {data.output_style}")

        return " │ ".join(parts)

    def _render_extended(self, data: StatuslineData) -> str:
        """Extended 모드 렌더링"""
        parts = []

        # 상세 정보 구성
        if data.model:
            parts.append(f"🤖 {data.model}")
        if data.claude_version:
            parts.append(f"v{data.claude_version}")
        if data.version:
            parts.append(f"🗿 {data.version}")
        if data.directory:
            parts.append(f"📁 {data.directory}")
        if data.branch and data.branch != "unknown":
            parts.append(f"🔀 {data.branch}")
        if data.git_status:
            parts.append(f"📊 {data.git_status}")
        if data.duration:
            parts.append(f"⏱️ {data.duration}")
        if data.active_task:
            parts.append(f"💭 {data.active_task}")
        if data.output_style:
            parts.append(f"💬 {data.output_style}")
        if data.update_available and data.latest_version:
            parts.append(f"🔄 {data.latest_version}")

        return " │ ".join(parts)

    def _render_minimal(self, data: StatuslineData) -> str:
        """Minimal 모드 렌더링"""
        return f"{data.directory}│{data.branch}"