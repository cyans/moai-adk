---
spec_id: SPEC-WINDOWS-OPT-001
title: "Windows 최적화 자동 재적용 시스템"
version: 1.0
status: draft
created_at: 2025-11-27
author: Claude Code (manager-spec)
priority: high
impact_area:
  - Update System Integration
  - Windows Optimization
  - Automated Configuration
  - Cross-Platform Compatibility
---

## HISTORY

| 버전 | 날짜 | 변경사항 | 작성자 |
|------|------|---------|--------|
| 1.0 | 2025-11-27 | Windows 최적화 자동 재적용 시스템 SPEC 초기 작성 | Claude Code (manager-spec) |

---

## 개요

`moai-adk update` 명령어 실행 시 원본 템플릿 동기화 후 Windows 환경 최적화 설정이 자동으로 재적용되는 시스템을 구축합니다. 이를 통해 업데이트 후에도 Windows 사용자가 최적화된 환경을 유지할 수 있습니다.

### 핵심 목표
- `moai-adk update` 실행 후 Windows 최적화 자동 재적용
- statusline-runner.py 자동 생성/업데이트
- hook 파일 UTF-8 인코딩 자동 추가
- settings.json 경로 자동 수정
- 실패 시 경고만 출력하고 계속 진행하는 안전장치

---

## 환경 (Environment)

### 시스템 요구사항
- Windows 10+ (주요 대상)
- Python 3.11+
- uv ≥ 0.4.0
- 기존 MoAI-ADK 프로젝트
- 인터넷 연결 (update 명령어 실행)

### 현재 상태
- `moai-adk update`: 템플릿 동기화 후 사용자 설정만 복원
- Windows 최적화: 업데이트 시 사라지는 문제
- 수동 재적용: 사용자가 직접 Windows 최적화 재적용 필요

### 배포 환경
- 개발 환경: Windows 개발자 워크스테이션
- 자동화: 업데이트 프로세스에 통합
- 안전성: 실패해도 기존 업데이트에 영향 없음

---

## 가정 (Assumptions)

### 기술적 가정
1. **OS 감지**: `sys.platform == 'win32'`로 Windows 환경 확인
2. **업데이트 통합**: 기존 update.py 코드에 기능 추가
3. **파일 백업**: 패치 실패 시 원본 파일 유지
4. **안전장치**: 부분 실패 시에도 업데이트 계속 진행

### 운영 가정
1. Windows 사용자는 70% 이상
2. 업데이트는 정기적으로 실행
3. 사용자는 최적화 과정을 인지할 필요 없음
4. 업데이트 실패 시 명확한 오류 메시지 필요

---

## 요구사항 (Requirements)

### 기능 요구사항

#### R1.1: 업데이트 후 Windows 최적화 자동 적용
- `moai-adk update` 실행 후 Windows 최적화 자동 재적용
- Windows 환경에서만 실행
- 성공/실패 여부 명확히 표시
- 실패 시에도 업데이트 계속 진행

#### R1.2: statusline-runner.py 자동 생성/업데이트
- `.moai/scripts/statusline-runner.py` 자동 생성
- 최신 버전 template에서 복사
- 기존 파일 백업 후 업데이트
- Windows UTF-8 인코딩 설정 포함

#### R1.3: hook 파일 UTF-8 인코딩 자동 추가
- 대상 파일:
  - `.claude/hooks/moai/session_start__show_project_info.py`
  - `.claude/hooks/moai/pre_tool__document_management.py`
  - `.claude/hooks/moai/session_end__auto_cleanup.py`
- 파일 시작 부분에 UTF-8 인코딩 설정 추가
- subprocess.run 호출에 인코딩 파라미터 추가

#### R1.4: settings.json 경로 자동 수정
- `statusLine.command` 경로 수정
- `hooks.*.command` 모든 경로 수정
- `%CLAUDE_PROJECT_DIR%` 환경변수 사용
- Windows 경로 구분자 호환

#### R1.5: 안전한 패치 적용
- 패치 전 파일 존재 확인
- 패치 실패 시 원본 유지
- 부분 성공 시 계속 진행
- 상세한 로깅 제공

### 제약사항

#### C1: Windows 환경 제약
- Windows에서만 실행되어야 함
- Windows 경로 및 인코딩 처리 필요
- Windows 권한 문제 고려

#### C2: 업데이트 호환성 제약
- 기존 update.py 코드 변경 최소화
- 기존 업데이트 기능에 영향 없음
- 실패 시 롤백 필요 없음

#### C3: 성능 제약
- 패치 적용은 빠르게 완료되어야 함
- 업데이트 시간 크게 증가하지 않음
- 불필요한 파일 작업 최소화

---

## 명세 (Specifications)

### ubiquitous (항상 참)
- **SPEC**: Windows 환경에서 `moai-adk update` 실행 시 항상 최적화 재적용 시도
- **구현**: `sys.platform == 'win32'` 조건 확인

### event-driven (이벤트 기반)
- **SPEC**: 업데이트 완료 이벤트 후 Windows 최적화 적용 이벤트 발생
- **동작**: 템플릿 동기화 → 사용자 설정 복원 → Windows 최적화 재적용
- **구현**:
  ```python
  # Restore user-specific settings after sync
  _restore_user_settings(project_path, preserved_settings)

  # Apply Windows optimizations (NEW)
  if sys.platform == 'win32':
      apply_windows_optimizations(project_path)
  ```

### unwanted (원치 않는 동작)
- **문제**: 패치 실패로 업데이트 전체 실패
- **방지**: try-catch 블록으로 예외 처리
- **구현 방식**:
  - 각 패치 단계별 예외 처리
  - 실패 시 경고만 출력
  - 업데이트 계속 진행

### state-driven (상태 기반)
- **SPEC**: 패치 적용 상태를 로깅하여 추적
- **구현**: 각 패치 단계별 성공/실패 상태 기록
- **추적**: 적용된 최적화 목록과 실패原因 기록

### optional (선택적)
- **기능**: 비활성화 옵션 제공
- **사용**: `--no-windows-optimization` 플래그 또는 설정 파일 옵션
- **목적**: 고급 사용자의 수동 제어 지원

---

## 추적 (Traceability)

### 태그 매핑
- `@TAG(R1.1)`: 업데이트 후 자동 적용 → `test_update_windows_optimization()`
- `@TAG(R1.2)`: statusline-runner.py → `test_statusline_runner_generation()`
- `@TAG(R1.3)`: hook 파일 인코딩 → `test_hook_files_encoding()`
- `@TAG(R1.4)`: settings.json 경로 → `test_settings_json_paths()`
- `@TAG(R1.5)`: 안전한 패치 → `test_safe_patch_application()`

### 의존성
- `SPEC-WINDOWS-OPT-001` → `src/moai_adk/platform/windows_patch.py` (최적화 모듈)
- `SPEC-WINDOWS-OPT-001` → `src/moai_adk/cli/commands/update.py` (업데이트 통합)
- `SPEC-WINDOWS-OPT-001` → `.moai/scripts/statusline-runner.py` (생성 대상)
- `SPEC-WINDOWS-OPT-001` → `.claude/hooks/moai/*.py` (수정 대상)
- `SPEC-WINDOWS-OPT-001` → `.claude/settings.json` (수정 대상)

---

## 기술 고려사항

### 패치 적용 순서
1. **statusline-runner.py**: 새로 생성 또는 업데이트
2. **hook 파일**: UTF-8 인코딩 추가
3. **settings.json**: 경로 수정
4. **검증**: 적용 결과 확인

### 에러 처리 전략
```python
def apply_windows_optimizations(project_path: Path) -> bool:
    success_count = 0
    total_steps = 3

    # Step 1: statusline-runner.py
    try:
        patch_statusline_runner(project_path)
        success_count += 1
        console.print("   [green]✅ Statusline runner updated[/green]")
    except Exception as e:
        console.print(f"   [yellow]⚠️  Statusline runner failed: {e}[/yellow]")

    # Step 2: hook files
    try:
        patch_hook_files(project_path)
        success_count += 1
        console.print("   [green]✅ Hook files optimized[/green]")
    except Exception as e:
        console.print(f"   [yellow]⚠️  Hook files failed: {e}[/yellow]")

    # Step 3: settings.json
    try:
        patch_settings_json(project_path)
        success_count += 1
        console.print("   [green]✅ Settings paths updated[/green]")
    except Exception as e:
        console.print(f"   [yellow]⚠️  Settings paths failed: {e}[/yellow]")

    return success_count == total_steps
```

### 파일 백업 전략
- 패치 전 원본 파일 백업 (선택적)
- 백업 위치: `.moai/backups/windows-optimization/`
- 백업 보관 기간: 7일
- 복원 기능 제공 (선택적)

---

## 성능 영향 분석

### 업데이트 시간 증가
- **현재**: 업데이트 약 30초
- **개선 후**: +3-5초 (Windows 최적화 적용)
- **영향**: 미미한 증가, 사용자 경험 저하 최소화

### 패치 적용 비용
- **파일 읽기/쓰기**: 약 1-2초
- **경로 처리**: 약 0.5초
- **검증**: 약 0.5초
- **총계**: 약 3초

---

## 마이그레이션 전략

### 단계별 적용

#### Phase 1: Windows 최적화 모듈 구현 (영향도: 낮음)
1. `src/moai_adk/platform/windows_patch.py` 생성
2. 각 패치 함수 구현
3. 단위 테스트 작성

#### Phase 2: 업데이트 통합 (영향도: 중간)
1. `update.py`에 Windows 최적화 통합
2. 에러 처리 및 로깅 추가
3. 업데이트 프로세스 테스트

#### Phase 3: 검증 및 테스트 (영향도: 중간)
1. Windows 환경에서 통합 테스트
2. 다양한 프로젝트에서 테스트
3. 롤백 시나리오 테스트

#### Phase 4: 배포 및 문서화 (영향도: 낮음)
1. 사용자 문서 업데이트
2. 릴리스 노트 작성
3. 고객 지원 가이드 작성

---

## 위험 및 완화 방안

### 위험 R1: 패치 실패로 업데이트 실패
- **가능성**: 중간 (파일 시스템 오류 가능성)
- **영향도**: 높음 (업데이트 전체 실패)
- **완화**: 각 패치 단계별 예외 처리, 실패 시 계속 진행

### 위험 R2: 기존 파일 호환성 문제
- **가능성**: 중간 (사용자 커스텀 설정)
- **영향도**: 중간 (사용자 설정 변경)
- **완화**: 패치 전 파일 백업, 스마트 병합 로직

### 위험 R3: Windows 특정 오류
- **가능성**: 높음 (Windows 경로, 인코딩 문제)
- **영향도**: 중간 (일부 기능 오작동)
- **완화**: 철저한 Windows 테스트, 다양한 환경 검증

### 위험 R4: 성능 저하
- **가능성**: 낮음 (간단한 파일 작업)
- **영향도**: 낮음 (업데이트 시간 약간 증가)
- **완화**: 비동기 처리, 캐싱 전략

---