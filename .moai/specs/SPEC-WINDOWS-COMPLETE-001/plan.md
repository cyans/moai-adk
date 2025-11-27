---
spec_id: SPEC-WINDOWS-COMPLETE-001
title: "Windows 환경 최적화 및 자동 설정 적용"
version: 1.0
status: in_progress
created_at: 2025-11-25
author: Claude Code (spec-builder)
---

## 구현 계획 (Implementation Plan)

### 개요
Windows 환경에서 MoAI-ADK의 호환성 문제를 해결하기 위한 종합적인 구현 계획입니다. OS 자동 감지, 동적 설정 생성, Windows statusline 문제 해결을 단계적으로 구현합니다.

---

## 🎯 우선순위별 마일스톤

### Primary Goal (1순위)
- **Windows Statusline 표시 문제 해결**: 현재 가장 시급한 사용자 경험 문제 해결
- **OS 자동 감지 기반 MCP 설정**: 핵심 기능 안정화

### Secondary Goal (2순위)
- **동적 설정 생성 스크립트**: 자동화 구현
- **Windows 특정 최적화**: 성능 및 안정성 개선

### Final Goal (3순위)
- **역호환성 및 마이그레이션**: 기존 사용자 보호
- **선택적 적용 기능**: 고급 사용자 지원

---

## 🏗️ 기술 아키텍처 설계

### 시스템 구조

```
MoAI-ADK 초기화
    ↓
OS 감지 모듈 (platform_detector.py)
    ↓
설정 템플릿 선택
    ↓
동적 설정 생성 (config_generator.py)
    ↓
설정 파일 적용
    ↓
기능 실행 (statusline, MCP 서버)
```

### 핵심 컴포넌트

#### 1. PlatformDetector
```python
class PlatformDetector:
    def detect_os() -> str
    def get_platform_config() -> dict
    def validate_platform() -> bool
```

#### 2. ConfigGenerator
```python
class ConfigGenerator:
    def generate_mcp_config(platform: str) -> dict
    def generate_statusline_config(platform: str) -> dict
    def apply_config(config: dict, filepath: str) -> bool
```

#### 3. WindowsOptimizer
```python
class WindowsOptimizer:
    def fix_windows_statusline() -> bool
    def optimize_windows_paths() -> dict
    def handle_windows_permissions() -> bool
```

---

## 📋 상세 구현 단계

### Phase 1: 기반 구조 구현 (Priority: High)

#### 1.1 OS 감지 모듈 개발
- **담당**: backend-expert
- **파일**: `src/moai_adk/platform/detector.py`
- **기능**:
  - `process.platform`을 통한 OS 감지
  - Windows, macOS, Linux 식별
  - 버전 및 아키텍처 정보 수집
- **테스트**: `tests/test_platform_detector.py`

#### 1.2 설정 템플릿 설계
- **담당**: backend-expert
- **파일**: `src/moai_adk/templates/config/`
- **템플릿 구조**:
  ```
  templates/
  ├── mcp/
  │   ├── mcp_windows.json
  │   ├── mcp_macos.json
  │   └── mcp_linux.json
  └── claude/
      ├── settings_windows.json
      ├── settings_macos.json
      └── settings_linux.json
  ```

#### 1.3 단위 테스트 환경 구축
- **담당**: test-engineer
- **테스트 범위**:
  - OS 감지 정확성
  - 설정 파일 생성 유효성
  - Windows 특정 기능 동작

### Phase 2: 핵심 기능 구현 (Priority: High)

#### 2.1 동적 설정 생성기
- **담당**: backend-expert
- **파일**: `src/moai_adk/platform/config_generator.py`
- **기능**:
  - OS별 설정 템플릿 로딩
  - 동적 설정 파일 생성
  - 백업 및 복원 기능
- **API 설계**:
  ```python
  def generate_optimized_config(platform: str) -> ConfigResult:
      """OS에 최적화된 설정 생성"""
      pass

  def apply_config_with_backup(config: dict, target_path: str) -> bool:
      """백업 후 설정 적용"""
      pass
  ```

#### 2.2 Windows Statusline 해결
- **담당**: backend-expert
- **문제 분석**:
  - 현재: `uv run moai-adk statusline` → Windows에서 실패
  - 원인: Windows PATH 환경변수, uv 설치 문제
- **해결方案**:
  1. 직접 Python 모듈 호출: `python -m moai_adk.statusline.main`
  2. Windows 경로 처리 개선
  3. 환경변수 자동 설정
- **구현**:
  ```python
  def fix_windows_statusline_command() -> str:
      """Windows에서 동작하는 statusline 명령어 반환"""
      if platform.system() == "Windows":
          return "python -m moai_adk.statusline.main"
      return "uv run moai-adk statusline"
  ```

### Phase 3: 최적화 및 안정화 (Priority: Medium)

#### 3.1 Windows 특정 최적화
- **담당**: performance-engineer
- **최적화 영역**:
  - 프로세스 생성 오버헤드 최소화
  - 파일 I/O 최적화
  - 메모리 사용량 개선
- **구현 전략**:
  - 비동기 설정 적용
  - 캐시 메커니즘 도입
  - Windows API 활용

#### 3.2 MCP 서버 Windows 호환성
- **담당**: devops-expert
- **현재 문제**:
  - context7: `cmd /c npx` 명령어
  - playwright: Windows 경로 문제
- **해결方案**:
  - OS별 명령어 분기 처리
  - Windows 인코딩 문제 해결
  - 권한 문제 예방

### Phase 4: 사용자 경험 개선 (Priority: Medium)

#### 4.1 자동 설정 적용 스크립트
- **담당**: backend-expert
- **진입점**: `moai-adk setup` 명령어 추가
- **기능**:
  - OS 감지 및 설정 최적화
  - 사용자 확인 프롬프트
  - 진행 상황 표시
- **CLI 인터페이스**:
  ```bash
  moai-adk setup                    # 대화형 설정
  moai-adk setup --auto            # 자동 설정
  moai-adk setup --backup-only     # 백업만 생성
  moai-adk setup --restore         # 백업 복원
  ```

#### 4.2 마이그레이션 도구
- **담당**: backend-expert
- **기능**:
  - 기존 설정 자동 백업
  - 문제 감지 및 해결 제안
  - 롤백 기능
- **안전장치**:
  - 설정 파일 유효성 검사
  - 백업 강제 생성
  - 롤백 명령어 제공

### Phase 5: 테스트 및 검증 (Priority: High)

#### 5.1 멀티 OS 테스트 환경
- **담당**: test-engineer
- **테스트 대상**:
  - Windows 10/11 (다양한 빌드)
  - macOS 12+ (Intel/Apple Silicon)
  - Linux (Ubuntu, CentOS, Arch)

#### 5.2 통합 테스트 시나리오
- **시나리오 1**: 신규 설치 사용자
  - OS 감지 → 자동 설정 → 기능 확인
- **시나리오 2**: 기존 사용자 마이그레이션
  - 백업 → 설정 업그레이드 → 기능 확인
- **시나리오 3**: 커스텀 설정 사용자
  - 설정 감지 → 선택적 적용 → 호환성 확인

---

## 🚧 위험 관리 및 완화 전략

### 기술적 위험

#### 위험 1: OS 감지 오류
- **확률**: 낮음 (안정적인 API)
- **영향**: 높음 (설정 실패)
- **완화**:
  - 다중 감지 방식 (process.platform + os.release())
  - 기본 설정 폴백
  - 상세 로깅

#### 위험 2: Windows 호환성 문제
- **확률**: 중간 (Windows 복잡성)
- **영향**: 중간 (일부 기능 오작동)
- **완화**:
  - 다양한 Windows 버전 테스트
  - Windows 전용 테스트 스위트
  - 점진적 롤아웃

### 사용자 경험 위험

#### 위험 3: 설정 손실
- **확률**: 중간 (자동 설정 위험)
- **영향**: 높음 (사용자 데이터)
- **완화**:
  - 강제 백업 정책
  - 명시적 사용자 동의
  - 원클릭 롤백

#### 위험 4: 성능 저하
- **확률**: 낮음 (설정은 일회성)
- **영향**: 낮음 (초기 로딩만)
- **완화**:
  - 비동기 처리
  - 캐싱 전략
  - 진행 상황 표시

---

## 📊 성공 지표 및 측정

### 기술적 성공 지표
- **OS 감지 정확률**: 100%
- **설정 생성 성공률**: 95% 이상
- **Windows statusline 표시율**: 100%
- **MCP 서버 연결 성공률**: 98% 이상

### 사용자 경험 지표
- **초기 설정 시간**: 30초 이내
- **설정 실패 복구 시간**: 1분 이내
- **Windows 사용자 만족도**: 90% 이상
- **지원 요청 감소율**: 50% 이상

---

## 🔗 의존성 관리

### 내부 의존성
- `PlatformDetector` → `ConfigGenerator`
- `ConfigGenerator` → `WindowsOptimizer`
- `WindowsOptimizer` → `ConfigTemplates`

### 외부 의존성
- **Python**: 3.11+ (pathlib, subprocess 최적화)
- **Node.js**: 18+ (process.platform 안정성)
- **uv**: 0.4.0+ (statusline 실행)

### 선택적 의존성
- **Windows API**: `pywin32` (고급 Windows 기능)
- **감지 라이브러리**: `psutil` (시스템 정보)

---

## 📝 릴리스 및 배포 계획

### Version 1.0.0 (MVP)
- OS 감지 기능
- Windows statusline 해결
- 기본 MCP 설정 최적화

### Version 1.1.0 (Enhancement)
- 고급 최적화 기능
- 사용자 커스터마이징
- 성능 개선

### Version 1.2.0 (Stabilization)
- 안정성 향상
- 추가 OS 지원
- 모니터링 기능

---

## 🧪 테스트 전략

### 단위 테스트
- 각 컴포넌트별 기능 검증
- OS별 동작 확인
- 에러 핸들링 검증

### 통합 테스트
- 전체 플로우 테스트
- 실제 환경 시뮬레이션
- 사용자 시나리오 검증

### 수동 테스트
- 다양한 Windows 환경
- 엣지 케이스 검증
- 사용자 피드백 수집

---

## 📚 문서화 계획

### 기술 문서
- API 문서
- 아키텍처 설명
- 트러블슈팅 가이드

### 사용자 문서
- 설정 가이드
- FAQ
- 마이그레이션 가이드

### 개발자 문서
- 기여 가이드
- 테스트 방법
- 릴리스 절차