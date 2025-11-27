# SPEC-STATUSLINE-CLEANUP-001: 상태선 불필요 요소 제거 및 최적화

**생성일**: 2025-11-26
**상태**: draft
**우선순위**: medium
**소유자**: cyans
**버전**: 1.0.0

---

## 📋 요약

MoAI-ADK 상태선에서 불필요한 요소(시간 표시 및 [Develop] 표시기)를 제거하고, 필수 정보(프로젝트 정보, 모델 정보, 배지 상태)를 보존하여 시각적 명확성을 향상시키는 사양입니다. Windows 환경에서 한글 이모지 지원을 보장하면서 성능을 최적화하는 것을 목표로 합니다.

---

## 🎯 목표

### 주요 목표
- [ ] 상태선에서 시간 표시(⏰ HH:MM:SS) 제거
- [ ] 상태선에서 [Develop] 표시기 제거
- [ ] 필수 정보 보존: 프로젝트 이름, 모델 정보, Git 상태, 배지 상태
- [ ] Windows 한글 이모지 정상 표시 유지
- [ ] 상태선 렌더링 성능 최적화

### 성과 지표
- 상태선 표시 길이 30% 감소
- 렌더링 성능 15% 향상
- Windows 한글 이모지 표시 정확도 100%
- 사용자 만족도 90% 이상

---

## 🌍 환경 (Environment)

### 시스템 환경
- **플랫폼**: Windows 10/11 (주요 대상)
- **터미널**: Windows Terminal, VSCode Terminal, 기본 Windows Console
- **Python**: 3.8 이상
- **인코딩**: UTF-8 (한글 이모지 지원)

### 제약 조건
- Windows 환경에서의 한글 이모지 깨짐 방지
- 기존 Powerline 스타일 유지
- Unicode/ANSI 색상 코드 호환성
- 다양한 터미널 환경 지원

---

## 🤖 가정 (Assumptions)

### 기술적 가정
- 사용자는 현재 상태선 구조에 익숙함
- 시간 표시는 다른 시스템(시스템 트레이 등)으로 확인 가능
- [Develop] 표시기는 개발 모드 표시보다 깔끔한 UI 선호
- Git 상태와 모델 정보가 가장 중요한 정보임

### 사용자 가정
- 사용자는 단순하고 깔끔한 상태선 선호
- Windows 환경에서 안정적인 이모지 표시 기대
- 성능 저하 없는 UI 변경 원함

---

## 📋 요구사항 (Requirements)

### 기능적 요구사항 (Functional Requirements)

#### FR-001: 시간 표시 제거
- **이벤트**: 상태선 렌더링 시
- **액션**: 시간 정보(⏰ HH:MM:SS)를 상태선에서 제외
- **응답**: 상태선 길이 감소 및 시각적 단순화
- **상태**: 시간 정보가 없는 깔끔한 상태선 표시

#### FR-002: [Develop] 표시기 제거
- **이벤트**: 상태선 렌더링 시
- **액션**: 활성 작업 표시기([DEVELOP]) 제거
- **응답**: 불필요한 텍스트 정보 제거
- **상태**: 필수 정보만 포함된 상태선

#### FR-003: 필수 정보 보존
- **이벤트**: 상태선 렌더링 시
- **액션**: 프로젝트 정보, 모델 정보, Git 상태, 배지 상태 유지
- **응답**: 모든 필수 정보 정상 표시
- **상태**: 필수 정보가 완전히 포함된 상태선

#### FR-004: 렌더링 모드 호환성
- **이벤트**: 다양한 렌더링 모드 요청 시
- **액션**: Powerline, Simple, Minimal 모드에서 일관적으로 요소 제거
- **응답**: 모든 모드에서 동일한 정책 적용
- **상태**: 모드별 일관된 상태선 표시

### 비기능적 요구사항 (Non-Functional Requirements)

#### NFR-001: 성능 (Performance)
- 상태선 렌더링 시간 15% 이상 향상
- 메모리 사용량 10% 이상 감소
- CPU 사용량 최소화

#### NFR-002: 호환성 (Compatibility)
- Windows Terminal에서 한글 이모지 정상 표시
- VSCode Terminal 호환성 유지
- 기본 Windows Console 지원

#### NFR-003: 접근성 (Accessibility)
- 색상 대비 유지
- 명확한 정보 계층 구조
- 직관적인 시각적 디자인

#### NFR-004: 유지보수성 (Maintainability)
- 기존 코드 구조 유지
- 쉬운 설정 확장성
- 명확한 코드 주석

---

## 🔧 상세 사양 (Specifications)

### SP-001: StatuslineData 구조체 변경

#### 1.1 필드 제거
```python
# 제거할 필드
- duration: str  # 시간 정보
- active_task: str  # [DEVELOP] 표시기
```

#### 1.2 보존 필드
```python
# 유지할 필드
- model: str  # 모델 정보
- claude_version: str  # Claude Code 버전
- version: str  # MoAI-ADK 버전
- directory: str  # 프로젝트 디렉토리
- branch: str  # Git 브랜치
- git_status: str  # Git 상태
- output_style: str  # 출력 스타일
- python_venv: str  # Python 가상환경
- exit_code: str  # 마지막 명령어 종료 코드
```

### SP-002: Renderer 로직 수정

#### 2.1 Powerline 모드 렌더링 (_render_powerline)
```python
# 제거할 세그먼트
- Timestamp 세그먼트 (lines 121-128)
- Active Task 세그먼트 (lines 174-180)

# 유지할 세그먼트 순서
1. Exit Code (선택적)
2. Model Information
3. Working Directory
4. Python Virtual Environment
5. Git Information
6. Output Style
```

#### 2.2 Simple 모드 렌더링 (_render_simple_powerline)
```python
# 제거할 세그먼트
- Timestamp 세그먼트 (lines 311-313)
- Task 세그먼트 (lines 338-339)
```

#### 2.3 Extended 모드 렌더링 (_render_extended)
```python
# 제거할 세그먼트
- Timestamp 세그먼트 (lines 210-212)
- Session Duration 세그먼트 (lines 242-243)
- Active Task 세그먼트 (lines 246-247)
```

### SP-003: 데이터 수집 함수 수정

#### 3.1 불필요 함수 제거
```python
# 제거 또는 주석 처리
- safe_collect_duration()  # 더 이상 사용하지 않음
- safe_collect_alfred_task()  # 더 이상 사용하지 않음
```

#### 3.2 build_statusline_data 함수 수정
```python
# 제거할 데이터 수집
# duration = safe_collect_duration()  # 제거
# active_task = safe_collect_alfred_task()  # 제거

# StatuslineData 생성 시 필드 제외
data = StatuslineData(
    # ... 기존 필드 ...
    # duration=duration,  # 제거
    # active_task=active_task,  # 제거
)
```

---

## 🔗 연관 요구사항 (Traceability)

### TAG BLOCK 관리
- **TAG-STATUSLINE-001**: 시간 표시 제거 구현
- **TAG-STATUSLINE-002**: [Develop] 표시기 제거 구현
- **TAG-STATUSLINE-003**: Windows 한글 이모지 호환성 보장
- **TAG-STATUSLINE-004**: 렌더링 성능 최적화

### 종속성 관계
- **SPEC-WINDOWS-COMPLETE-001**: Windows 최적화 구현 완료
- **MOAI-ADK-CORE-001**: 기본 상태선 아키텍처
- **STATUSLINE-RENDERER-001**: Powerline 렌더링 엔진

---

## ✅ 검증 기준 (Verification Criteria)

### 테스트 시나리오

#### Given-When-Then 형식

**Scenario 1: 시간 표시 제거 확인**
- **Given**: 상태선이 렌더링될 때
- **When**: 어떤 렌더링 모드에서든
- **Then**: 시간 정보(⏰ HH:MM:SS)가 표시되지 않아야 함

**Scenario 2: [Develop] 표시기 제거 확인**
- **Given**: 활성 작업이 있을 때
- **When**: 상태선이 렌더링되면
- **Then**: [DEVELOP] 또는 유사한 표시기가 나타나지 않아야 함

**Scenario 3: 필수 정보 보존 확인**
- **Given**: 정상적인 상태선 렌더링 시
- **When**: 상태선이 표시되면
- **Then**: 프로젝트 이름, 모델 정보, Git 상태가 정확히 표시되어야 함

**Scenario 4: Windows 한글 이모지 지원**
- **Given**: Windows 환경에서 한글 이모지를 포함한 프로젝트 이름일 때
- **When**: 상태선이 렌더링되면
- **Then**: 한글 이모지가 깨짐 없이 정상 표시되어야 함

**Scenario 5: 성능 향상 확인**
- **Given**: 상태선 렌더링 성능 측정 시
- **When**: 기존 구현과 비교하면
- **Then**: 렌더링 시간이 15% 이상 향상되어야 함

### 품질 게이트 (Quality Gates)

#### TRUST 5 기준
- **Test-first**: 모든 시나리오에 대한 테스트 케이스 존재 (85% 이상 커버리지)
- **Readable**: 명확한 코드 구조와 주석
- **Unified**: 일관된 코딩 스타일과 패턴
- **Secured**: 보안 취약점 없음
- **Trackable**: 변경 사항 추적 가능

---

## 📊 구현 계획 (Implementation Plan)

### Phase 1: 코드 분석 및 설계 (1일)
- [x] 현재 상태선 구조 분석 완료
- [x] 제거 대상 요소 식별 완료
- [ ] 상세 구현 설계

### Phase 2: 핵심 기능 구현 (2일)
- [ ] StatuslineData 구조체 수정
- [ ] Renderer 로직 수정 (Powerline, Simple, Extended)
- [ ] 데이터 수집 함수 정리

### Phase 3: 테스트 및 검증 (1일)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 수행
- [ ] Windows 환경 테스트

### Phase 4: 최종 검토 및 문서화 (1일)
- [ ] 코드 리뷰 및 품질 게이트 통과
- [ ] 사용자 문서 업데이트
- [ ] 배포 준비

---

## 🔄 상태 변경 이력 (Change History)

| 날짜 | 상태 | 변경 내용 | 담당자 |
|------|------|----------|--------|
| 2025-11-26 | draft | SPEC 문서 초안 작성 | GOOS |

---

**상태**: draft
**다음 단계**: 구현 계획 확정 및 개발 시작