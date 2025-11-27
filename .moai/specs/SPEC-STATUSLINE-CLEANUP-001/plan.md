# 구현 계획: 상태선 불필요 요소 제거 및 최적화

**SPEC ID**: SPEC-STATUSLINE-CLEANUP-001
**생성일**: 2025-11-26
**담당자**: cyans
**예상 기간**: 5일

---

## 🎯 마일스톤 (Milestones)

### Phase 1: 분석 및 설계 완료
**기간**: 1일
**목표**: 기존 코드 구조 분석 및 변경 설계 완료

#### 작업 목록
- [x] 현재 상태선 아키텍처 분석 완료
- [x] 시간 표시 및 [Develop] 표시기 위치 식별 완료
- [x] 제거 대상 요소 상세 분석 완료
- [ ] 구현 방법론 설계
- [ ] 영향도 분석 및 리스크 평가

#### 주요 산출물
- 코드 분석 리포트
- 구현 설계 문서
- 영향도 분석 결과

### Phase 2: 핵심 기능 구현
**기간**: 2일
**목표**: 상태선 핵심 로직 수정 및 최적화

#### 작업 목록
- [ ] StatuslineData 구조체에서 불필요 필드 제거
- [ ] Powerline 렌더러에서 시간 및 작업 표시기 제거
- [ ] Simple 렌더러에서 불필요 세그먼트 제거
- [ ] Extended 렌더러 정리 및 최적화
- [ ] 데이터 수집 함수 정리
- [ ] Windows 한글 이모지 지원 보장

#### 주요 산출물
- 수정된 data.py
- 최적화된 renderer.py
- 정리된 main.py

### Phase 3: 테스트 및 검증
**기간**: 1일
**목표**: 모든 기능에 대한 포괄적 테스트 수행

#### 작업 목록
- [ ] 단위 테스트 케이스 작성
- [ ] 렌더링 모드별 테스트 수행
- [ ] Windows 환경 호환성 테스트
- [ ] 성능 벤치마킹 수행
- [ ] 한글 이모지 표시 테스트
- [ ] 회귀 테스트 수행

#### 주요 산출물
- 테스트 보고서
- 성능 측정 결과
- 호환성 검증 결과

### Phase 4: 최종 검토 및 배포
**기간**: 1일
**목표**: 품질 보증 및 배포 준비 완료

#### 작업 목록
- [ ] 코드 리뷰 및 품질 게이트 통과
- [ ] 문서 업데이트
- [ ] 사용자 가이드 수정
- [ ] 릴리스 노트 작성
- [ ] 배포 준비

#### 주요 산출물
- 최종 코드 리포지토리
- 업데이트된 문서
- 릴리스 노트

---

## 🔧 기술적 접근 방식 (Technical Approach)

### 아키텍처 변경 전략

#### 1. 점진적 수정 방식
- 기존 구조를 최대한 유지하면서 필요한 부분만 수정
- 하위 호환성을 보장하며 변경 사항 최소화
- 단계적 구현으로 리스크 관리

#### 2. 성능 최적화 전략
- 불필요한 데이터 수집 함수 제거로 오버헤드 감소
- 렌더링 파이프라인 단순화로 처리 속도 향상
- 메모리 사용량 최적화

#### 3. Windows 호환성 보장
- UTF-8 인코딩 처리 로직 유지 및 강화
- 한글 이모지 표시를 위한 안전 출력 함수 보존
- 다양한 터미널 환경 대응

### 코드 변경 우선순위

#### High Priority (즉시 수정)
1. **renderer.py**: 시간 및 작업 표시기 세그먼트 제거
2. **data.py**: 불필요 필드 제거
3. **main.py**: 데이터 수집 함수 정리

#### Medium Priority (2단계 수정)
1. 테스트 케이스 작성
2. 성능 최적화 적용
3. 문서 업데이트

#### Low Priority (마지막 단계)
1. 코드 스타일 정리
2. 주석 개선
3. 추가적인 기능 개선

---

## 🛠️ 구현 상세 (Implementation Details)

### Phase 2 상세 작업 계획

#### 작업 1: StatuslineData 구조체 수정
```python
# data.py 수정 내용
@dataclass
class StatuslineData:
    # 유지 필드
    model: str
    claude_version: str
    version: str
    directory: str
    branch: str
    git_status: str
    output_style: str
    # ... 기타 필드

    # 제거 필드 (주석 처리 또는 삭제)
    # duration: str  # 제거 예정
    # active_task: str  # 제거 예정
```

#### 작업 2: Powerline 렌더러 수정
```python
# renderer.py _render_powerline 메소드 수정
def _render_powerline(self, data: StatuslineData) -> str:
    # 기존 세그먼트 구성에서 시간과 작업 표시기 제거
    segment_configs = []

    # 1. Exit Code (선택적)
    # 2. Model Information
    # 3. Working Directory
    # 4. Python Virtual Environment
    # 5. Git Information
    # 6. Output Style (마지막)

    # Timestamp 세그먼트 (lines 121-128) - 제거
    # Active Task 세그먼트 (lines 174-180) - 제거
```

#### 작업 3: Simple 렌더러 수정
```python
# renderer.py _render_simple_powerline 메소드 수정
def _render_simple_powerline(self, data: StatuslineData) -> str:
    segments = []

    # Model
    # Directory
    # Python venv
    # Git
    # Style

    # Timestamp (lines 311-313) - 제거
    # Task (lines 338-339) - 제거
```

### Windows 호환성 고려사항

#### 1. 한글 인코딩 처리
- 기존 UTF-8 강제 설정 로직 유지
- Windows Console 코드 페이지 설정 보존
- 안전 출력 함수(safe_print) 계속 사용

#### 2. 터미널 호환성
- Powerline 구분자 처리 로직 유지
- ANSI 색상 코드 호환성 보장
- Unicode 지원 감지 기능 보존

---

## 🧪 테스트 전략 (Testing Strategy)

### 테스트 분류

#### 1. 단위 테스트 (Unit Tests)
- **대상**: 각 렌더링 메소드별 기능
- **범위**:
  - `_render_powerline()` 메소드
  - `_render_simple_powerline()` 메소드
  - `_render_extended()` 메소드
  - `_render_minimal()` 메소드
- **기대 결과**: 요소 제거 후 정상 렌더링

#### 2. 통합 테스트 (Integration Tests)
- **대상**: 전체 상태선 생성 파이프라인
- **범위**:
  - `build_statusline_data()` 함수
  - `main()` 함수 전체 흐름
- **기대 결과**: 종단간(end-to-end) 정상 동작

#### 3. 호환성 테스트 (Compatibility Tests)
- **대상**: 다양한 Windows 터미널 환경
- **범위**:
  - Windows Terminal
  - VSCode Integrated Terminal
  - 기본 Windows Console (cmd, PowerShell)
- **기대 결과**: 모든 환경에서 정상 표시

#### 4. 성능 테스트 (Performance Tests)
- **대상**: 렌더링 성능 측정
- **측정 지표**:
  - 렌더링 시간 (단위: ms)
  - 메모리 사용량 (단위: MB)
  - CPU 사용률 (단위: %)
- **기대 결과**: 기존 대비 15% 이상 향상

### 테스트 데이터 준비

#### 1. 정상 케이스
- 일반적인 프로젝트 환경 데이터
- Git 상태가 있는 경우
- Python 가상환경이 활성화된 경우

#### 2. 경계 케이스
- 긴 프로젝트 이름 (한글 포함)
- 특수 문자 포함 Git 상태
- 빈 값 또는 null 값 처리

#### 3. 예외 케이스
- 잘못된 인코딩 데이터
- 너무 긴 상태 문자열
- 시스템 오류 상황

---

## 📈 성공 지표 (Success Metrics)

### 정량적 지표
- **성능 향상**: 렌더링 시간 15% 이상 단축
- **메모리 최적화**: 메모리 사용량 10% 이상 감소
- **코드 감소**: 불필요 코드 50라인 이상 제거
- **테스트 커버리지**: 85% 이상 달성

### 정성적 지표
- **시각적 단순화**: 상태선 길이 30% 감소
- **사용자 경험**: 더 깔끔하고 읽기 쉬운 인터페이스
- **호환성**: Windows 환경에서 한글 이모지 100% 정상 표시
- **유지보수성**: 코드 구조 단순화로 유지보수 용이성 향상

### 검증 기준
- [ ] 모든 Given-When-Then 시나리오 통과
- [ ] TRUST 5 품질 게이트 통과
- [ ] Windows 환경 테스트 통과
- [ ] 성능 벤치마크 목표 달성
- [ ] 사용자 승인 테스트 통과

---

## ⚠️ 리스크 관리 (Risk Management)

### 기술적 리스크

#### 1. 하위 호환성 깨짐
- **확률**: 낮음
- **영향**: 중간
- **완화책**: 점진적 수정, 철저한 테스트

#### 2. Windows 호환성 문제
- **확률**: 중간
- **영향**: 높음
- **완화책**: Windows 환경에서의 집중 테스트, UTF-8 처리 로직 보존

#### 3. 성능 저하
- **확률**: 낮음
- **영향**: 중간
- **완화책**: 성능 벤치마킹, 프로파일링

### 프로젝트 리스크

#### 1. 일정 지연
- **확률**: 중간
- **영향**: 중간
- **완화책**: 일정 버퍼 확보, 우선순위 조정

#### 2. 요구사항 변경
- **확률**: 낮음
- **영향**: 낮음
- **완화책**: 유연한 설계, 빠른 피드백 루프

---

## 📝 문서화 계획 (Documentation Plan)

### 기술 문서
- [x] SPEC 문서 (현재)
- [ ] API 문서 업데이트
- [ ] 코드 주석 개선
- [ ] 테스트 문서 작성

### 사용자 문서
- [ ] 사용자 가이드 업데이트
- [ ] 변경 로그 작성
- [ ] 릴리스 노트 준비
- [ ] 문제 해결 가이드

### 내부 문서
- [ ] 구현 노트
- [ ] 테스트 결과 보고서
- [ ] 성능 측정 보고서
- [ ] 회고 및 개선 사항

---

**상태**: 계획 완료
**다음 단계**: Phase 1 최종 검토 및 Phase 2 구현 시작