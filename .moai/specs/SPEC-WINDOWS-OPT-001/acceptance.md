---
spec_id: SPEC-WINDOWS-OPT-001
title: "Windows 최적화 자동 재적용 시스템 수용 기준"
version: 1.0
status: draft
created_at: 2025-11-27
author: Claude Code (manager-spec)
---

## 수용 기준 개요

Windows 환경에서 `moai-adk update` 명령어 실행 후 최적화 설정이 자동으로 재적용되는지 검증하기 위한 상세 테스트 시나리오와 수용 기준입니다.

---

## 기능적 수용 기준 (Functional Acceptance Criteria)

### AC-1: 업데이트 후 Windows 최적화 자동 적용
**Given**: Windows 환경에서 MoAI-ADK 프로젝트가 설치되어 있고
**When**: `moai-adk update` 명령어를 실행하면
**Then**: Windows 최적화가 자동으로 적용되고 성공 메시지가 표시된다

#### 테스트 시나리오
```gherkin
Scenario: Update applies Windows optimizations automatically
  Given I have a Windows MoAI-ADK project
  And I run "moai-adk update" command
  Then I should see "🔧 Applying Windows optimizations..." message
  And I should see "✅ Windows optimizations applied successfully" message
  And Windows-specific optimizations should be applied to the project
```

#### 검증 항목
- [ ] `sys.platform == 'win32'` 조건 확인
- [ ] `apply_windows_optimizations()` 함수 호출
- [ ] 성공/실패 메시지 표시
- [ ] 로깅 기록 확인

### AC-2: statusline-runner.py 자동 생성 및 업데이트
**Given**: `.moai/scripts/` 디렉토리가 존재하고
**When**: Windows 최적화가 적용되면
**Then**: `statusline-runner.py`가 생성되거나 업데이트되고 Windows UTF-8 설정이 포함된다

#### 테스트 시나리오
```gherkin
Scenario: Statusline runner auto-generation
  Given I have a Windows project with .moai/scripts directory
  When Windows optimizations are applied
  Then .moai/scripts/statusline-runner.py should be created
  And the file should contain Windows UTF-8 encoding settings
  And the file should contain PYTHONIOENCODING environment variable
```

#### 검증 항목
- [ ] 파일 생성 확인
- [ ] UTF-8 인코딩 설정 (`# -*- coding: utf-8 -*-`)
- [ ] `PYTHONIOENCODING='utf-8'` 설정
- [ ] Windows 호환 명령어 실행 로직

### AC-3: hook 파일 UTF-8 인코딩 자동 추가
**Given**: `.claude/hooks/moai/` 디렉토리에 hook 파일들이 존재하고
**When**: Windows 최적화가 적용되면
**Then**: 각 hook 파일에 UTF-8 인코딩 설정이 자동으로 추가된다

#### 테스트 시나리오
```gherkin
Scenario: Hook files UTF-8 encoding auto-addition
  Given I have hook files in .claude/hooks/moai/ directory
  When Windows optimizations are applied
  Then each hook file should have UTF-8 encoding declaration
  And subprocess.run calls should have encoding parameters
```

#### 검증 항목
- [ ] `session_start__show_project_info.py` UTF-8 인코딩 추가
- [ ] `pre_tool__document_management.py` UTF-8 인코딩 추가
- [ ] `session_end__auto_cleanup.py` UTF-8 인코딩 추가
- [ ] `subprocess.run(encoding='utf-8', errors='replace')` 파라미터 추가
- [ ] 중복 적용 방지 확인

### AC-4: settings.json 경로 자동 수정
**Given**: `.claude/settings.json` 파일이 존재하고
**When**: Windows 최적화가 적용되면
**Then**: 모든 경로가 `%CLAUDE_PROJECT_DIR%` 환경변수를 사용하도록 수정된다

#### 테스트 시나리오
```gherkin
Scenario: Settings JSON paths auto-update
  Given I have .claude/settings.json with absolute paths
  When Windows optimizations are applied
  Then statusLine.command should use %CLAUDE_PROJECT_DIR%
  And all hooks.*.command should use %CLAUDE_PROJECT_DIR%
  And the file should remain valid JSON format
```

#### 검증 항목
- [ ] `statusLine.command` 경로 수정
- [ ] 모든 `hooks.*.command` 경로 수정
- [ ] `%CLAUDE_PROJECT_DIR%` 환경변수 사용
- [ ] JSON 유효성 유지

### AC-5: 안전한 실패 처리
**Given**: Windows 최적화 적용 중 일부 단계가 실패하고
**When**: 패치 실패가 발생하면
**Then**: 실패한 부분에 대해서만 경고 메시지를 표시하고 업데이트는 계속 진행된다

#### 테스트 시나리오
```gherkin
Scenario: Safe failure handling
  Given Windows optimization patch partially fails
  When update command continues execution
  Then I should see warning messages for failed steps
  And I should see success messages for completed steps
  And the update process should not be interrupted
```

#### 검증 항목
- [ ] 개별 단계별 예외 처리
- [ ] 실패 시 경고 메시지 표시
- [ ] 업데이트 프로세스 계속 진행
- [ ] 상세한 로깅 기록

---

## 비기능적 수용 기준 (Non-Functional Acceptance Criteria)

### NF-AC-1: 성능 기준
**Given**: Windows 최적화 적용 프로세스가 실행되고
**When**: 모든 패치 단계가 완료되면
**Then**: 전체 적용 시간이 10초를 초과하지 않는다

#### 테스트 시나리오
```gherkin
Scenario: Performance criteria
  Given I run moai-adk update on Windows
  When Windows optimizations are applied
  Then the optimization process should complete within 10 seconds
  And the update time should not increase by more than 20%
```

#### 검증 항목
- [ ] 전체 적용 시간 ≤ 10초
- [ ] 업데이트 시간 증가율 ≤ 20%
- [ ] 각 단계별 실행 시간 측정

### NF-AC-2: 호환성 기준
**Given**: 다양한 Windows 버전 환경에서
**When**: Windows 최적화가 적용되면
**Then**: 모든 최적화 기능이 정상적으로 동작한다

#### 테스트 시나리오
```gherkin
Scenario: Windows version compatibility
  Given I have Windows 10/11 different versions
  When Windows optimizations are applied
  Then all optimization features should work correctly
  And there should be no version-specific errors
```

#### 검증 항목
- [ ] Windows 10 호환성
- [ ] Windows 11 호환성
- [ ] 다양한 Python 버전 호환성
- [ ] 경로 구분자 처리 정확성

### NF-AC-3: 신뢰성 기준
**Given**: 반복적인 업데이트 실행 시나리오에서
**When**: Windows 최적화가 여러 번 적용되면
**Then**: 중복 적용이 방지되고 일관된 결과가 유지된다

#### 테스트 시나리오
```gherkin
Scenario: Reliability and idempotency
  Given I run moai-adk update multiple times
  When Windows optimizations are applied each time
  Then the results should be consistent
  And there should be no duplicate modifications
  And existing optimizations should not be broken
```

#### 검증 항목
- [ ] 중복 적용 방지 로직
- [ ] 기존 최적화 유지
- [ ] 일관된 결과 보장
- [ ] 멱등성(idempotency) 확인

---

## 통합 테스트 시나리오

### IT-1: 완전한 업데이트 워크플로우 테스트
```gherkin
Feature: Complete update workflow with Windows optimizations

  Background:
    Given I have a clean Windows machine
    And I have installed MoAI-ADK
    And I have initialized a project with "moai-adk init test-project"

  Scenario: Complete update with all Windows optimizations
    Given I navigate to the project directory
    And I simulate a template update scenario
    When I run "moai-adk update"
    Then the update should complete successfully
    And I should see Windows optimization messages
    And .moai/scripts/statusline-runner.py should be created with UTF-8
    And hook files should have UTF-8 encoding added
    And settings.json should use %CLAUDE_PROJECT_DIR% paths
    And the project should be fully functional on Windows

  Scenario: Update with existing customizations
    Given I have customized some project files
    And I have modified .claude/settings.json with custom settings
    When I run "moai-adk update"
    Then my custom settings should be preserved
    And Windows optimizations should be applied alongside my settings
    And there should be no conflicts or data loss
```

### IT-2: 에러 시나리오 테스트
```gherkin
Feature: Error handling scenarios

  Scenario: Missing directory structure
    Given I have a project with incomplete directory structure
    When I run "moai-adk update"
    Then missing directories should be created automatically
    And optimizations should be applied where possible
    And I should see appropriate warning messages

  Scenario: Permission denied errors
    Given I have restricted file permissions on some files
    When I run "moai-adk update"
    Then the process should continue with other optimizations
    And I should see clear permission error messages
    And the update should not fail completely

  Scenario: Corrupted settings.json
    Given I have a corrupted .claude/settings.json file
    When I run "moai-adk update"
    Then the corrupted file should be backed up
    And a new settings.json with optimizations should be created
    And I should see a recovery message
```

---

## 자동화된 테스트 구현

### 단위 테스트
```python
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from moai_adk.platform.windows_patch import (
    apply_windows_optimizations,
    patch_statusline_runner,
    patch_hook_files,
    patch_settings_json
)

class TestWindowsPatchAutomated:

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create directory structure
            (project_path / ".moai" / "scripts").mkdir(parents=True)
            (project_path / ".claude" / "hooks" / "moai").mkdir(parents=True)

            # Create test hook files
            hook_content = """import subprocess
import sys

def main():
    result = subprocess.run(['echo', 'test'])
    print(result.stdout)

if __name__ == "__main__":
    main()
"""

            (project_path / ".claude" / "hooks" / "moai" / "session_start__show_project_info.py").write_text(hook_content)
            (project_path / ".claude" / "hooks" / "moai" / "pre_tool__document_management.py").write_text(hook_content)
            (project_path / ".claude" / "hooks" / "moai" / "session_end__auto_cleanup.py").write_text(hook_content)

            # Create test settings.json
            settings = {
                "statusLine": {
                    "command": "python C:/Users/test/project/.moai/scripts/statusline-runner.py"
                },
                "hooks": {
                    "test_hook": {
                        "command": "python C:/Users/test/project/.claude/hooks/test.py"
                    }
                }
            }

            (project_path / ".claude" / "settings.json").write_text(json.dumps(settings))

            yield project_path

    def test_apply_windows_optimizations_success(self, temp_project):
        """Test successful application of all Windows optimizations."""
        with patch('sys.platform', 'win32'):
            result = apply_windows_optimizations(temp_project)

            assert result is True

            # Verify statusline runner
            statusline_file = temp_project / ".moai" / "scripts" / "statusline-runner.py"
            assert statusline_file.exists()

            content = statusline_file.read_text(encoding='utf-8')
            assert '# -*- coding: utf-8 -*-' in content
            assert 'PYTHONIOENCODING' in content

    def test_apply_windows_optimizations_non_windows(self, temp_project):
        """Test that optimizations are not applied on non-Windows platforms."""
        with patch('sys.platform', 'darwin'):
            result = apply_windows_optimizations(temp_project)

            # Should return True (no-op) but not apply changes
            assert result is True

    def test_patch_statusline_runner_with_template(self, temp_project):
        """Test statusline runner patching when template exists."""
        # Create template
        template_dir = Path(__file__).parent.parent.parent / "templates" / "scripts"
        template_dir.mkdir(parents=True, exist_ok=True)

        template_content = """#!/usr/bin/env python3
# Template statusline runner
def main():
    print("Statusline running")
"""
        (template_dir / "statusline-runner.py").write_text(template_content)

        result = patch_statusline_runner(temp_project)

        assert result is True

        statusline_file = temp_project / ".moai" / "scripts" / "statusline-runner.py"
        content = statusline_file.read_text(encoding='utf-8')
        assert "Template statusline runner" in content

    def test_patch_hook_files_encoding(self, temp_project):
        """Test hook files UTF-8 encoding patching."""
        result = patch_hook_files(temp_project)

        assert result is True

        # Check each hook file
        hook_files = [
            "session_start__show_project_info.py",
            "pre_tool__document_management.py",
            "session_end__auto_cleanup.py"
        ]

        for hook_file in hook_files:
            hook_path = temp_project / ".claude" / "hooks" / "moai" / hook_file
            content = hook_path.read_text(encoding='utf-8')

            # Should have UTF-8 encoding declaration
            assert '# -*- coding: utf-8 -*-' in content

            # Should have encoding parameters in subprocess.run
            assert "encoding='utf-8', errors='replace'" in content

    def test_patch_settings_json_paths(self, temp_project):
        """Test settings.json path patching."""
        result = patch_settings_json(temp_project)

        assert result is True

        settings_file = temp_project / ".claude" / "settings.json"
        settings = json.loads(settings_file.read_text(encoding='utf-8'))

        # Check statusLine command
        assert "%CLAUDE_PROJECT_DIR%" in settings["statusLine"]["command"]

        # Check hooks commands
        assert "%CLAUDE_PROJECT_DIR%" in settings["hooks"]["test_hook"]["command"]

    def test_error_handling_missing_file(self, temp_project):
        """Test error handling when required files are missing."""
        # Remove settings.json
        (temp_project / ".claude" / "settings.json").unlink()

        # Should not fail
        result = patch_settings_json(temp_project)
        assert result is True

    def test_error_handling_corrupted_file(self, temp_project):
        """Test error handling when files are corrupted."""
        # Create corrupted settings.json
        (temp_project / ".claude" / "settings.json").write_text("invalid json content")

        # Should handle gracefully
        result = patch_settings_json(temp_project)
        assert result is False  # Expected failure
```

### 통합 테스트
```python
import subprocess
import sys
import time
from pathlib import Path

class TestUpdateIntegration:

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows integration test")
    def test_update_command_integration(self):
        """Test the complete update command integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Initialize project
            init_result = subprocess.run([
                sys.executable, "-m", "moai_adk.cli.main", "init", "test-project"
            ], cwd=temp_dir, capture_output=True, text=True, timeout=300)

            assert init_result.returncode == 0

            # Measure update time
            start_time = time.time()

            # Run update
            update_result = subprocess.run([
                sys.executable, "-m", "moai_adk.cli.main", "update"
            ], cwd=temp_dir, capture_output=True, text=True, timeout=300)

            end_time = time.time()
            update_duration = end_time - start_time

            # Assertions
            assert update_result.returncode == 0
            assert update_duration <= 30  # Should complete within 30 seconds
            assert "Windows optimizations" in update_result.stdout

            # Verify optimizations
            statusline_file = project_path / ".moai" / "scripts" / "statusline-runner.py"
            assert statusline_file.exists()
```

---

## 수용 테스트 실행 가이드

### 사전 요구사항
1. Windows 10 또는 11 환경
2. Python 3.11+ 설치
3. MoAI-ADK 개발 버전 설치
4. 테스트용 깨끗한 프로젝트

### 실행 단계
1. **단위 테스트 실행**:
   ```bash
   pytest tests/test_windows_patch.py -v
   ```

2. **통합 테스트 실행**:
   ```bash
   pytest tests/test_update_windows_integration.py -v
   ```

3. **수동 테스트 실행**:
   - 새 프로젝트 생성
   - `moai-adk update` 실행
   - 결과 검증

### 성공 기준
- 모든 단위 테스트 통과 (100%)
- 통합 테스트 통과 (95% 이상)
- 수동 테스트 시나리오 통과
- 성능 기준 만족
- 호환성 기준 만족

---

## 완료 정의 (Definition of Done)

**기능적 완료**:
- [ ] 모든 Windows 최적화 기능 구현 완료
- [ ] 업데이트 명령어 통합 완료
- [ ] 에러 처리 및 로깅 완료

**품질적 완료**:
- [ ] 단위 테스트覆盖率 90% 이상
- [ ] 통합 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 성능 테스트 통과

**운영적 완료**:
- [ ] 사용자 문서 업데이트
- [ ] 릴리스 노트 작성
- [ ] 배포 준비 완료
- [ ] 고객 지원 가이드 준비

이 수용 기준을 모두 만족해야 SPEC-WINDOWS-OPT-001이 완료된 것으로 간주됩니다.