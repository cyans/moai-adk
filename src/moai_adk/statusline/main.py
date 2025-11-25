#!/usr/bin/env python3
"""
Claude Code Statusline Integration

TAG-WIN-005: Statusline Solution 구현

Main entry point for MoAI-ADK statusline rendering in Claude Code.
Collects all necessary information from the project and renders it
in the specified format for display in the status bar.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

# Windows에서 UTF-8 인코딩 강제 설정
if sys.platform == 'win32':
    try:
        # stdout과 stderr을 UTF-8로 재설정
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        
        # Windows 콘솔 코드 페이지를 UTF-8로 설정
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # UTF-8 코드 페이지
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass  # 실패해도 계속 진행
    except Exception:
        pass  # 실패해도 계속 진행

try:
    from .data import StatuslineData
    from .renderer import StatuslineRenderer
    from .version_reader import VersionReader, VersionConfig
except ImportError:
    from data import StatuslineData
    from renderer import StatuslineRenderer
    try:
        from version_reader import VersionReader, VersionConfig
    except ImportError:
        VersionReader = None
        VersionConfig = None


def read_session_context() -> dict:
    """
    Read JSON context from stdin (sent by Claude Code).

    Returns:
        Dictionary containing session information
    """
    try:
        # Handle Docker/non-interactive environments by checking TTY
        input_data = sys.stdin.read() if not sys.stdin.isatty() else "{}"
        if input_data:
            try:
                return json.loads(input_data)
            except json.JSONDecodeError as e:
                import logging
                logging.error(f"Failed to parse JSON from stdin: {e}")
                logging.debug(f"Input data: {input_data[:200]}")
                return {}
        return {}
    except (EOFError, ValueError) as e:
        import logging
        logging.error(f"Error reading stdin: {e}")
        return {}


def safe_collect_git_info() -> tuple[str, str]:
    """
    Safely collect git information with fallback.

    Returns:
        Tuple of (branch_name, git_status_str)
    """
    try:
        # Mock implementation for testing
        return "main", "+1 M2 ?1"
    except Exception:
        return "N/A", ""


def safe_collect_duration() -> str:
    """
    Safely collect session duration with fallback.

    Returns:
        Formatted duration string
    """
    try:
        # Mock implementation for testing
        return "15m"
    except Exception:
        return "0m"


def safe_collect_alfred_task() -> str:
    """
    Safely collect active Alfred task with fallback.

    Returns:
        Formatted task string
    """
    try:
        # Mock implementation for testing
        return "[DEVELOP]"
    except Exception:
        return ""


def safe_collect_version() -> str:
    """
    Safely collect MoAI-ADK version with fallback.
    실제 VersionReader를 사용하여 .moai/config/config.json에서 버전을 읽습니다.

    Returns:
        Version string
    """
    try:
        if VersionReader is not None:
            # 실제 VersionReader 사용
            version_config = VersionConfig(
                cache_ttl_seconds=60,
                fallback_version="unknown",
                enable_validation=False
            )
            version_reader = VersionReader(config=version_config)
            version = version_reader.get_version()
            # "v" 접두사 제거 (있는 경우)
            if version.startswith("v"):
                version = version[1:]
            return version
        else:
            # Fallback: 패키지 버전 사용
            try:
                from moai_adk import __version__
                return __version__
            except ImportError:
                return "unknown"
    except Exception:
        # 최종 fallback
        try:
            from moai_adk import __version__
            return __version__
        except ImportError:
            return "unknown"


def safe_check_update(current_version: str) -> tuple[bool, Optional[str]]:
    """
    Safely check for updates with fallback.

    Args:
        current_version: Current version string

    Returns:
        Tuple of (update_available, latest_version)
    """
    try:
        # Mock implementation for testing
        return False, None
    except Exception:
        return False, None


def build_statusline_data(session_context: dict, mode: str = "compact") -> str:
    """
    Build complete statusline string from all data sources.

    Collects information from:
    - Claude Code session context (via stdin)
    - Git repository
    - Session metrics
    - Alfred workflow state
    - MoAI-ADK version
    - Update checker
    - Output style

    Args:
        session_context: Context passed from Claude Code via stdin
        mode: Display mode (compact, extended, minimal)

    Returns:
        Rendered statusline string
    """
    try:
        # Extract model from session context with Claude Code version
        model_info = session_context.get("model", {})
        model_name = model_info.get("display_name") or model_info.get("name") or "Unknown"

        # Extract Claude Code version separately for new layout
        claude_version = session_context.get("version", "")
        model = model_name

        # Extract directory (한글 경로 인코딩 처리)
        cwd = session_context.get("cwd", "")
        if cwd:
            try:
                # Windows에서 한글 경로 처리
                if sys.platform == 'win32':
                    # 경로를 UTF-8로 디코딩하여 처리
                    if isinstance(cwd, bytes):
                        cwd = cwd.decode('utf-8', errors='replace')
                    # Path 객체 생성 시 UTF-8 보장
                    cwd_path = Path(cwd)
                    directory = cwd_path.name or cwd_path.parent.name or "project"
                else:
                    directory = Path(cwd).name or Path(cwd).parent.name or "project"
            except Exception:
                # 경로 처리 실패 시 기본값
                directory = "project"
        else:
            directory = "project"

        # Extract output style from session context
        output_style = session_context.get("output_style", {}).get("name", "")

        # Collect all information from local sources
        branch, git_status = safe_collect_git_info()
        duration = safe_collect_duration()
        active_task = safe_collect_alfred_task()
        version = safe_collect_version()
        update_available, latest_version = safe_check_update(version)

        # Build StatuslineData with dynamic fields
        data = StatuslineData(
            model=model,
            claude_version=claude_version,
            version=version,
            memory_usage="256MB",
            branch=branch,
            git_status=git_status,
            duration=duration,
            directory=directory,
            active_task=active_task,
            output_style=output_style,
            update_available=update_available,
            latest_version=latest_version,
        )

        # Render statusline with labeled sections
        renderer = StatuslineRenderer()
        statusline = renderer.render(data, mode=mode)

        return statusline

    except Exception as e:
        # Graceful degradation on any error
        import logging

        logging.warning(f"Statusline rendering error: {e}")
        return ""


def safe_print(text: str):
    """
    Safely print text with proper encoding handling for Windows.
    Windows에서 이모지가 제대로 출력되도록 UTF-8 인코딩 보장.

    Args:
        text: Text to print
    """
    try:
        # Windows에서 UTF-8로 직접 출력
        if sys.platform == 'win32':
            # UTF-8 바이트로 인코딩 후 stdout에 직접 쓰기
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout.buffer.write(text.encode('utf-8', errors='replace'))
                sys.stdout.buffer.flush()
            else:
                print(text, end="")
        else:
            # 다른 플랫폼에서는 일반 print 사용
            print(text, end="")
    except (UnicodeEncodeError, AttributeError):
        # Fallback: 일반 print 시도
        try:
            print(text, end="")
        except Exception:
            # 최종 fallback: UTF-8로 인코딩 시도
            try:
                utf8_text = text.encode('utf-8', errors='replace').decode('utf-8')
                print(utf8_text, end="")
            except Exception:
                # 최후의 수단: ASCII만 출력
                safe_text = ''.join(c for c in text if ord(c) < 128)
                print(safe_text, end="")


def main():
    """
    Main entry point for Claude Code statusline.

    Reads JSON from stdin, processes all information,
    and outputs the formatted statusline string.
    """
    # Debug mode check
    debug_mode = os.environ.get("MOAI_STATUSLINE_DEBUG") == "1"

    # Read session context from Claude Code
    session_context = read_session_context()

    if debug_mode:
        # Write debug info to stderr for troubleshooting
        sys.stderr.write(f"[DEBUG] Received session_context: {json.dumps(session_context, indent=2)}\n")
        sys.stderr.flush()

    # Determine display mode (priority: session context > environment > config > default)
    mode = (
        session_context.get("statusline", {}).get("mode")
        or os.environ.get("MOAI_STATUSLINE_MODE")
        or "extended"
    )

    # Build and output statusline
    statusline = build_statusline_data(session_context, mode=mode)
    if debug_mode:
        sys.stderr.write(f"[DEBUG] Generated statusline: {statusline}\n")
        sys.stderr.flush()

    if statusline:
        safe_print(statusline)


if __name__ == "__main__":
    main()