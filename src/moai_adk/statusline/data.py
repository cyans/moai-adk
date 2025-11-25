# type: ignore
"""
Statusline data structures and models

TAG-WIN-005: Statusline Solution 구현
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StatuslineData:
    """Statusline data container

    모든 statusline 표시 정보를 담는 데이터 클래스
    """
    model: str
    claude_version: str
    version: str
    memory_usage: str
    branch: str
    git_status: str
    duration: str
    directory: str
    active_task: str
    output_style: str
    update_available: bool
    latest_version: Optional[str] = None

    def __post_init__(self):
        """데이터 초기화 후 후처리"""
        if not self.model:
            self.model = "unknown"
        if not self.version:
            self.version = "0.0.0"
        if not self.branch:
            self.branch = "unknown"
        if not self.duration:
            self.duration = "0m"
        if not self.directory:
            self.directory = "project"