---
spec_id: SPEC-WINDOWS-OPT-001
title: "Windows 최적화 자동 재적용 시스템 구현 계획"
version: 1.0
status: draft
created_at: 2025-11-27
author: Claude Code (manager-spec)
---

## 구현 계획 개요

`moai-adk update` 명령어에 Windows 최적화 자동 재적용 기능을 통합하여 업데이트 후에도 Windows 사용자가 최적화된 환경을 유지할 수 있도록 합니다.

---

## 기술 아키텍처

### 컴포넌트 구조
```
moai-adk update 명령어
    ↓
템플릿 동기화 (기존)
    ↓
사용자 설정 복원 (기존)
    ↓
Windows 최적화 자동 적용 (신규)
    ├── statusline-runner.py 생성/업데이트
    ├── hook 파일 UTF-8 인코딩 추가
    ├── settings.json 경로 수정
    └── 적용 결과 보고
    ↓
업데이트 완료
```

### 핵심 모듈
- **windows_patch.py**: Windows 최적화 패치 메인 모듈
- **update.py**: 업데이트 명령어 통합 지점
- **패치 함수들**: 각 파일별 최적화 적용 함수

---

## 구현 단계 (Phase별)

### Phase 1: Windows 최적화 모듈 구현
**우선순위**: 높음
**예상 작업량**: 4-6시간

#### 1.1 기본 모듈 구조 생성
```python
# src/moai_adk/platform/windows_patch.py
from pathlib import Path
import json
import sys
import shutil
from typing import Optional, Tuple

def apply_windows_optimizations(project_path: Path) -> bool:
    """
    Apply all Windows optimizations to the project.

    Args:
        project_path: Path to the project directory

    Returns:
        bool: True if all optimizations applied successfully
    """

def patch_statusline_runner(project_path: Path) -> bool:
    """Generate or update statusline-runner.py with Windows optimizations."""

def patch_hook_files(project_path: Path) -> bool:
    """Add UTF-8 encoding to hook files."""

def patch_settings_json(project_path: Path) -> bool:
    """Update settings.json paths for Windows compatibility."""
```

#### 1.2 statusline-runner.py 패치 함수
```python
def patch_statusline_runner(project_path: Path) -> bool:
    """
    Generate or update .moai/scripts/statusline-runner.py with Windows UTF-8 settings.

    Template source: src/moai_adk/templates/scripts/statusline-runner.py
    Target: .moai/scripts/statusline-runner.py
    """
    template_path = Path(__file__).parent.parent.parent / "templates" / "scripts" / "statusline-runner.py"
    target_path = project_path / ".moai" / "scripts" / "statusline-runner.py"

    # Create directory if not exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy template if exists
    if template_path.exists():
        shutil.copy2(template_path, target_path)
        return True

    # Generate minimal version if template not found
    content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess

def main():
    """Windows UTF-8 최적화 statusline runner"""
    # UTF-8 설정 강제
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    # 기존 statusline 로직 실행
    try:
        result = subprocess.run([
            sys.executable, "-m", "moai_adk.statusline.main"
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(f"Error: {result.stderr.strip()}", file=sys.stderr)

    except Exception as e:
        print(f"Statusline error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    target_path.write_text(content, encoding='utf-8')
    return True
```

#### 1.3 hook 파일 UTF-8 패치 함수
```python
def patch_hook_files(project_path: Path) -> bool:
    """
    Add UTF-8 encoding to hook files.

    Target files:
    - .claude/hooks/moai/session_start__show_project_info.py
    - .claude/hooks/moai/pre_tool__document_management.py
    - .claude/hooks/moai/session_end__auto_cleanup.py
    """
    hook_files = [
        "session_start__show_project_info.py",
        "pre_tool__document_management.py",
        "session_end__auto_cleanup.py"
    ]

    success_count = 0

    for hook_file in hook_files:
        hook_path = project_path / ".claude" / "hooks" / "moai" / hook_file

        if not hook_path.exists():
            continue

        try:
            content = hook_path.read_text(encoding='utf-8')

            # Check if already has UTF-8 encoding
            if '# -*- coding: utf-8 -*-' in content or '# coding=utf-8' in content:
                success_count += 1
                continue

            # Add UTF-8 encoding at the top
            lines = content.split('\n')

            # Find first import or main line
            insert_index = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                    insert_index = i
                    break

            lines.insert(insert_index, '# -*- coding: utf-8 -*-')
            lines.insert(insert_index + 1, '')

            new_content = '\n'.join(lines)
            hook_path.write_text(new_content, encoding='utf-8')

            # Update subprocess.run calls
            content = hook_path.read_text(encoding='utf-8')
            content = content.replace(
                'subprocess.run(',
                'subprocess.run(encoding=\'utf-8\', errors=\'replace\', '
            )
            hook_path.write_text(content, encoding='utf-8')

            success_count += 1

        except Exception as e:
            print(f"Failed to patch {hook_file}: {e}")
            continue

    return success_count == len(hook_files)
```

#### 1.4 settings.json 경로 패치 함수
```python
def patch_settings_json(project_path: Path) -> bool:
    """
    Update .claude/settings.json paths for Windows compatibility.

    Changes:
    - statusLine.command: use %CLAUDE_PROJECT_DIR%
    - hooks.*.command: use %CLAUDE_PROJECT_DIR%
    """
    settings_path = project_path / ".claude" / "settings.json"

    if not settings_path.exists():
        return True  # File not exists, nothing to patch

    try:
        settings = json.loads(settings_path.read_text(encoding='utf-8'))

        # Update statusLine command
        if 'statusLine' in settings and 'command' in settings['statusLine']:
            cmd = settings['statusLine']['command']
            if isinstance(cmd, str):
                # Replace absolute path with %CLAUDE_PROJECT_DIR%
                if '.moai/scripts/statusline-runner.py' in cmd:
                    settings['statusLine']['command'] = (
                        'uv run "%CLAUDE_PROJECT_DIR%/.moai/scripts/statusline-runner.py"'
                    )

        # Update hooks commands
        if 'hooks' in settings:
            for hook_name, hook_config in settings['hooks'].items():
                if isinstance(hook_config, dict) and 'command' in hook_config:
                    cmd = hook_config['command']
                    if isinstance(cmd, str):
                        # Replace absolute paths with %CLAUDE_PROJECT_DIR%
                        if '.claude/hooks/' in cmd:
                            cmd = cmd.replace(str(project_path), '%CLAUDE_PROJECT_DIR%')
                            hook_config['command'] = cmd

        # Write updated settings
        settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')
        return True

    except Exception as e:
        print(f"Failed to patch settings.json: {e}")
        return False
```

---

### Phase 2: 업데이트 명령어 통합
**우선순위**: 높음
**예상 작업량**: 2-3시간

#### 2.1 update.py 수정
```python
# src/moai_adk/cli/commands/update.py
import sys
from pathlib import Path

def _restore_user_settings(project_path: Path, preserved_settings: dict):
    # 기존 코드...
    pass

def update_command():
    # 기존 업데이트 로직...

    # Restore user-specific settings after sync
    _restore_user_settings(project_path, preserved_settings)

    # Apply Windows optimizations (NEW)
    if sys.platform == 'win32':
        try:
            from moai_adk.platform.windows_patch import apply_windows_optimizations

            console.print("   [blue]🔧 Applying Windows optimizations...[/blue]")

            if apply_windows_optimizations(project_path):
                console.print("   [green]✅ Windows optimizations applied successfully[/green]")
            else:
                console.print("   [yellow]⚠️  Windows optimizations partially applied[/yellow]")

        except Exception as e:
            console.print(f"   [yellow]⚠️  Windows optimization failed: {e}[/yellow]")
            logger.warning(f"Windows optimization failed: {e}")

    console.print("\n   [green]✅ Project update completed successfully![/green]")
```

#### 2.2 에러 처리 및 로깅 강화
```python
import logging
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

def apply_windows_optimizations_with_logging(project_path: Path) -> Tuple[bool, dict]:
    """
    Apply Windows optimizations with detailed logging.

    Returns:
        Tuple[bool, dict]: (overall_success, step_results)
    """
    step_results = {
        'statusline_runner': False,
        'hook_files': False,
        'settings_json': False
    }

    overall_success = True

    # Step 1: Statusline runner
    try:
        step_results['statusline_runner'] = patch_statusline_runner(project_path)
        if step_results['statusline_runner']:
            console.print("   [green]✅ Statusline runner updated[/green]")
        else:
            console.print("   [yellow]⚠️  Statusline runner update failed[/yellow]")
            overall_success = False
    except Exception as e:
        step_results['statusline_runner'] = False
        console.print(f"   [red]❌ Statusline runner error: {e}[/red]")
        logger.error(f"Statusline runner patch failed: {e}")
        overall_success = False

    # Step 2: Hook files
    try:
        step_results['hook_files'] = patch_hook_files(project_path)
        if step_results['hook_files']:
            console.print("   [green]✅ Hook files optimized[/green]")
        else:
            console.print("   [yellow]⚠️  Hook files optimization failed[/yellow]")
            overall_success = False
    except Exception as e:
        step_results['hook_files'] = False
        console.print(f"   [red]❌ Hook files error: {e}[/red]")
        logger.error(f"Hook files patch failed: {e}")
        overall_success = False

    # Step 3: Settings JSON
    try:
        step_results['settings_json'] = patch_settings_json(project_path)
        if step_results['settings_json']:
            console.print("   [green]✅ Settings paths updated[/green]")
        else:
            console.print("   [yellow]⚠️  Settings paths update failed[/yellow]")
            overall_success = False
    except Exception as e:
        step_results['settings_json'] = False
        console.print(f"   [red]❌ Settings paths error: {e}[/red]")
        logger.error(f"Settings JSON patch failed: {e}")
        overall_success = False

    return overall_success, step_results
```

---

### Phase 3: 테스트 및 검증
**우선순위**: 중간
**예상 작업량**: 3-4시간

#### 3.1 단위 테스트 작성
```python
# tests/test_windows_patch.py
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from moai_adk.platform.windows_patch import (
    apply_windows_optimizations,
    patch_statusline_runner,
    patch_hook_files,
    patch_settings_json
)

class TestWindowsPatch:

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create directory structure
            (project_path / ".moai" / "scripts").mkdir(parents=True)
            (project_path / ".claude" / "hooks" / "moai").mkdir(parents=True)

            yield project_path

    def test_patch_statusline_runner_new_file(self, temp_project):
        result = patch_statusline_runner(temp_project)
        assert result is True

        runner_file = temp_project / ".moai" / "scripts" / "statusline-runner.py"
        assert runner_file.exists()

        content = runner_file.read_text(encoding='utf-8')
        assert '# -*- coding: utf-8 -*-' in content
        assert 'PYTHONIOENCODING' in content

    def test_patch_hook_files_encoding(self, temp_project):
        # Create test hook file
        hook_file = temp_project / ".claude" / "hooks" / "moai" / "test_hook.py"
        hook_file.write_text("import subprocess\nsubprocess.run(['ls'])", encoding='utf-8')

        result = patch_hook_files(temp_project)
        assert result is True

        content = hook_file.read_text(encoding='utf-8')
        assert '# -*- coding: utf-8 -*-' in content
        assert "encoding='utf-8', errors='replace'" in content

    def test_patch_settings_json_paths(self, temp_project):
        # Create test settings file
        settings_file = temp_project / ".claude" / "settings.json"
        settings = {
            "statusLine": {
                "command": f"python {temp_project}/.moai/scripts/statusline-runner.py"
            },
            "hooks": {
                "test": {
                    "command": f"python {temp_project}/.claude/hooks/test.py"
                }
            }
        }
        settings_file.write_text(json.dumps(settings), encoding='utf-8')

        result = patch_settings_json(temp_project)
        assert result is True

        updated_settings = json.loads(settings_file.read_text(encoding='utf-8'))
        assert "%CLAUDE_PROJECT_DIR%" in updated_settings["statusLine"]["command"]
        assert "%CLAUDE_PROJECT_DIR%" in updated_settings["hooks"]["test"]["command"]
```

#### 3.2 통합 테스트 작성
```python
# tests/test_update_windows_integration.py
import pytest
import subprocess
import tempfile
from pathlib import Path

class TestUpdateWindowsIntegration:

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only test")
    def test_update_with_windows_optimizations(self):
        """Test that update command applies Windows optimizations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Initialize project
            result = subprocess.run([
                'moai-adk', 'init', 'test-project'
            ], cwd=project_path, capture_output=True, text=True)

            assert result.returncode == 0

            # Run update
            result = subprocess.run([
                'moai-adk', 'update'
            ], cwd=project_path, capture_output=True, text=True)

            assert result.returncode == 0
            assert 'Windows optimizations applied' in result.stdout

            # Verify optimizations
            statusline_runner = project_path / ".moai" / "scripts" / "statusline-runner.py"
            assert statusline_runner.exists()

            settings_file = project_path / ".claude" / "settings.json"
            if settings_file.exists():
                settings = json.loads(settings_file.read_text(encoding='utf-8'))
                # Check for Windows path optimizations
```

---

### Phase 4: 배포 및 문서화
**우선순위**: 낮음
**예상 작업량**: 2-3시간

#### 4.1 사용자 문서 업데이트
- README.md 업데이트
- Windows 특정 설치 가이드 추가
- 트러블슈팅 가이드 추가

#### 4.2 릴리스 노트 작성
- 새로운 Windows 최적화 기능 설명
- 자동 적용 프로세스 설명
- 향후 개선 계획

---

## 위험 관리 및 완화 전략

### 기술적 위험

#### 위험: 파일 패치 실패
- **확률**: 중간
- **영향**: 중간
- **완화**: 각 패치 단계별 예외 처리, 롤백 기능

#### 위험: Windows 환경 호환성
- **확률**: 높음
- **영향**: 높음
- **완화**: 다양한 Windows 버전 테스트, CI/CD 자동화

#### 위험: 성능 저하
- **확률**: 낮음
- **영향**: 낮음
- **완화**: 비동기 처리, 캐싱 전략

### 운영적 위험

#### 위험: 사용자 설정 손실
- **확률**: 낮음
- **영향**: 높음
- **완화**: 백업 및 복원 기능, 스마트 병합

#### 위험: 업데이트 프로세스 중단
- **확률**: 중간
- **영향**: 높음
- **완화**: 안전한 실패 처리, 계속 진행 로직

---

## 성공 기준

### 기능적 기준
- [ ] Windows 환경에서 update 실행 시 최적화 자동 적용
- [ ] statusline-runner.py 성공적으로 생성/업데이트
- [ ] hook 파일 UTF-8 인코딩 성공적으로 추가
- [ ] settings.json 경로 성공적으로 수정
- [ ] 실패 시에도 업데이트 계속 진행

### 비기능적 기준
- [ ] 업데이트 시간 10% 이내 증가
- [ ] 95% 이상의 Windows 환경에서 정상 동작
- [ ] 명확한 성공/실패 메시지 제공
- [ ] 상세한 로깅 및 오류 보고

### 품질 기준
- [ ] 단위 테스트覆盖率 90% 이상
- [ ] 통합 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 문서화 완료

---

## 다음 단계

1. **즉시**: Phase 1 Windows 최적화 모듈 구현 시작
2. **1주일 내**: Phase 2 업데이트 통합 완료
3. **2주일 내**: Phase 3 테스트 및 검증 완료
4. **3주일 내**: Phase 4 배포 및 문서화 완료

이 계획에 따라 Windows 최적화 자동 재적용 시스템을 안정적으로 구현할 수 있습니다.