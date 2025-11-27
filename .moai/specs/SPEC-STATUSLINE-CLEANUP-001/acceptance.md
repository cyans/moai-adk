# 수용 기준: 상태선 불필요 요소 제거 및 최적화

**SPEC ID**: SPEC-STATUSLINE-CLEANUP-001
**생성일**: 2025-11-26
**검증자**: cyans
**상태**: draft

---

## 🎯 개요

본 문서는 SPEC-STATUSLINE-CLEANUP-001의 수용 기준을 정의합니다. 시간 표시와 [Develop] 표시기 제거를 통한 상태선 단순화가 성공적으로 완료되었는지 검증하는 기준을 제공합니다.

---

## ✅ 정의 완료 (Definition of Done)

### 기본 조건
- [ ] 모든 기능적 요구사항이 구현됨
- [ ] 모든 비기능적 요구사항이 충족됨
- [ ] 모든 테스트 케이스가 통과됨
- [ ] 코드 리뷰가 완료됨
- [ ] 품질 게이트(TRUST 5)를 통과함
- [ ] 사용자 승인 테스트가 통과됨

### 품질 조건
- [ ] 테스트 커버리지 85% 이상
- [ ] 성능 목표 달성 (렌더링 시간 15% 향상)
- [ ] Windows 한글 이모지 100% 표시
- [ ] 코드 스타일 가이드 준수
- [ ] 문서화 완료

---

## 🧪 수용 테스트 시나리오 (Acceptance Test Scenarios)

### Scenario 1: 시간 표시 제거 검증

#### Test Case 1.1: Powerline 모드
```gherkin
Given: Powerline 렌더링 모드가 활성화되어 있을 때
When: 상태선이 렌더링되면
Then: 시간 정보(⏰ HH:MM:SS)가 표시되지 않아야 함
And: 나머지 정보는 정상적으로 표시되어야 함
```

**검증 방법**:
```bash
# 테스트 실행
python -m moai_adk.statusline.main --mode=powerline

# 기대 결과 확인
# 시간 세그먼트 없는 Powerline 상태선 확인
# 예시 출력: "✓ EXIT 🤖 3.5 📁 project 🔀 main [+1] 💬 r2d2"
```

#### Test Case 1.2: Simple 모드
```gherkin
Given: Simple 렌더링 모드가 활성화되어 있을 때
When: 상태선이 렌더링되면
Then: 타임스탬프([HH:MM:SS])가 표시되지 않아야 함
And: ASCII 기반 상태선이 정상 표시되어야 함
```

**검증 방법**:
```bash
# 테스트 실행
python -m moai_adk.statusline.main --mode=simple

# 기대 결과 확인
# 타임스탬프 없는 Simple 상태선 확인
# 예시 출력: "AI:3.5 > DIR:project > GIT:main[+1] > STYLE:r2d2"
```

#### Test Case 1.3: Extended 모드
```gherkin
Given: Extended 렌더링 모드가 활성화되어 있을 때
When: 상태선이 렌더링되면
Then: 날짜/시간 정보(⏰ MM/DD HH:MM:SS)가 표시되지 않아야 함
And: 세션 시간(⏱️ duration)이 표시되지 않아야 함
```

**검증 방법**:
```bash
# 테스트 실행
python -m moai_adk.statusline.main --mode=extended

# 기대 결과 확인
# 시간 관련 세그먼트 없는 Extended 상태선 확인
# 예시 출력: "🤖 Claude 3.5 v4.5 │ 🗿 v0.27.2 │ 📁 project │ 🔀 main [+1] │ 💬 r2d2"
```

### Scenario 2: [Develop] 표시기 제거 검증

#### Test Case 2.1: 모든 렌더링 모드
```gherkin
Given: 활성 작업([DEVELOP]) 정보가 있을 때
When: 어떤 렌더링 모드에서든 상태선이 렌더링되면
Then: [DEVELOP] 또는 유사한 작업 표시기가 나타나지 않아야 함
And: 작업 관련 정보가 데이터 구조에서 제외되어야 함
```

**검증 방법**:
```python
# 코드 검증
def test_no_active_task_display():
    # StatuslineData에 active_task 필드가 없는지 확인
    # 모든 렌더링 함수에서 active_task 참조가 제거되었는지 확인
```

### Scenario 3: 필수 정보 보존 검증

#### Test Case 3.1: 모델 정보 유지
```gherkin
Given: Claude 모델 정보가 있을 때
When: 상태선이 렌더링되면
Then: 모델 정보(🤖 Claude 3.5)가 항상 표시되어야 함
And: 모든 렌더링 모드에서 일관되게 표시되어야 함
```

#### Test Case 3.2: 프로젝트 정보 유지
```gherkin
Given: 프로젝트 디렉토리 정보가 있을 때
When: 상태선이 렌더링되면
Then: 디렉토리 이름(📁 project)이 정확히 표시되어야 함
And: 한글 디렉토리 이름도 깨짐 없이 표시되어야 함
```

#### Test Case 3.3: Git 정보 유지
```gherkin
Given: Git 리포지토리 정보가 있을 때
When: 상태선이 렌더링되면
Then: 브랜치 정보(🔀 main)와 상태 정보([+1 M2 ?1])가 표시되어야 함
And: Git 상태 변경 시 실시간으로 반영되어야 함
```

### Scenario 4: Windows 한글 이모지 호환성 검증

#### Test Case 4.1: 한글 프로젝트 이름
```gherkin
Given: 프로젝트 이름에 한글 또는 이모지가 포함되어 있을 때
When: Windows 환경에서 상태선이 렌더링되면
Then: 한글과 이모지가 깨짐 없이 정상 표시되어야 함
And: 인코딩 문제로 인한 오류가 발생하지 않아야 함
```

**검증 방법**:
```bash
# Windows 테스트
cd "D:\테스트-🚀프로젝트"
python -m moai_adk.statusline.main

# 기대 결과: 깨짐 없는 한글 및 이모지 표시
```

#### Test Case 4.2: 다양한 터미널 환경
```gherkin
Given: 다양한 Windows 터미널 환경에서 실행할 때
When: 상태선이 렌더링되면
Then: Windows Terminal, VSCode, cmd, PowerShell에서 모두 정상 표시되어야 함
And: ANSI 색상 코드와 Unicode 문자가 올바르게 처리되어야 함
```

### Scenario 5: 성능 향상 검증

#### Test Case 5.1: 렌더링 시간 측정
```gherkin
Given: 상태선 렌더링 성능을 측정할 때
When: 수정 전과 수정 후의 렌더링 시간을 비교하면
Then: 렌더링 시간이 15% 이상 향상되어야 함
And: 메모리 사용량이 10% 이상 감소해야 함
```

**검증 방법**:
```python
import time
import memory_profiler

def benchmark_performance():
    start_time = time.time()
    start_memory = memory_profiler.memory_usage()[0]

    # 상태선 렌더링 실행
    statusline = build_statusline_data(session_context)

    end_time = time.time()
    end_memory = memory_profiler.memory_usage()[0]

    render_time = end_time - start_time
    memory_usage = end_memory - start_memory

    return render_time, memory_usage
```

#### Test Case 5.2: 대량 데이터 처리
```gherkin
Given: 긴 상태 정보가 있을 때
When: 상태선이 반복적으로 렌더링될 때
Then: 성능 저하 없이 일관된 속도를 유지해야 함
And: 메모리 누수가 발생하지 않아야 함
```

---

## 🔍 상세 검증 절차 (Detailed Verification Procedures)

### Step 1: 코드 검증

#### 1.1 StatuslineData 구조체 확인
```bash
# 확인할 파일: src/moai_adk/statusline/data.py

# 기대 결과:
# - duration 필드가 제거되어 있음
# - active_task 필드가 제거되어 있음
# - 나머지 필드는 유지되어 있음
```

#### 1.2 Renderer 로직 확인
```bash
# 확인할 파일: src/moai_adk/statusline/renderer.py

# 기대 결과:
# - _render_powerline()에서 시간 및 작업 세그먼트 제거
# - _render_simple_powerline()에서 관련 부분 제거
# - _render_extended()에서 관련 부분 제거
```

#### 1.3 데이터 수집 함수 확인
```bash
# 확인할 파일: src/moai_adk/statusline/main.py

# 기대 결과:
# - safe_collect_duration() 함수 호출 제거
# - safe_collect_alfred_task() 함수 호출 제거
# - build_statusline_data()에서 관련 필드 제외
```

### Step 2: 기능 검증

#### 2.1 렌더링 모드별 테스트
```bash
# Powerline 모드 테스트
MOAI_STATUSLINE_MODE=powerline python -m moai_adk.statusline.main

# Simple 모드 테스트
MOAI_STATUSLINE_MODE=simple python -m moai_adk.statusline.main

# Extended 모드 테스트
MOAI_STATUSLINE_MODE=extended python -m moai_adk.statusline.main

# Minimal 모드 테스트
MOAI_STATUSLINE_MODE=minimal python -m moai_adk.statusline.main
```

#### 2.2 Windows 환경 테스트
```bash
# 한글 프로젝트 테스트
cd "D:\한글-🚀테스트프로젝트"
python -m moai_adk.statusline.main

# PowerShell 테스트
powershell -Command "python -m moai_adk.statusline.main"

# CMD 테스트
cmd /C "python -m moai_adk.statusline.main"
```

### Step 3: 성능 검증

#### 3.1 벤치마킹 스크립트 실행
```python
# benchmark.py
import time
import statistics
from moai_adk.statusline.main import build_statusline_data

def benchmark_statusline():
    times = []
    for i in range(100):
        start = time.perf_counter()
        statusline = build_statusline_data({})
        end = time.perf_counter()
        times.append(end - start)

    avg_time = statistics.mean(times)
    median_time = statistics.median(times)

    print(f"Average render time: {avg_time*1000:.2f}ms")
    print(f"Median render time: {median_time*1000:.2f}ms")

    return avg_time

if __name__ == "__main__":
    benchmark_statusline()
```

#### 3.2 메모리 사용량 측정
```bash
# memory_profiler 설치 필요
pip install memory_profiler

# 메모리 프로파일링 실행
python -m memory_profiler moai_adk/statusline/main.py
```

---

## 📊 수용 기준 체크리스트 (Acceptance Checklist)

### 기능적 요구사항
- [ ] **FR-001**: 시간 표시 제거
  - [ ] Powerline 모드에서 ⏰ HH:MM:SS 제거됨
  - [ ] Simple 모드에서 [HH:MM:SS] 제거됨
  - [ ] Extended 모드에서 날짜/시간 제거됨

- [ ] **FR-002**: [Develop] 표시기 제거
  - [ ] 모든 렌더링 모드에서 작업 표시기 제거됨
  - [ ] StatuslineData에서 active_task 필드 제거됨
  - [ ] 데이터 수집 함수 정리됨

- [ ] **FR-003**: 필수 정보 보존
  - [ ] 모델 정보 정상 표시됨
  - [ ] 프로젝트 정보 정상 표시됨
  - [ ] Git 상태 정상 표시됨
  - [ ] 배지 상태 정상 표시됨

- [ ] **FR-004**: 렌더링 모드 호환성
  - [ ] Powerline 모드 정상 동작
  - [ ] Simple 모드 정상 동작
  - [ ] Extended 모드 정상 동작
  - [ ] Minimal 모드 정상 동작

### 비기능적 요구사항
- [ ] **NFR-001**: 성능
  - [ ] 렌더링 시간 15% 이상 향상
  - [ ] 메모리 사용량 10% 이상 감소
  - [ ] CPU 사용량 최소화

- [ ] **NFR-002**: 호환성
  - [ ] Windows Terminal 한글 이모지 정상 표시
  - [ ] VSCode Terminal 호환성 유지
  - [ ] 기본 Windows Console 지원

- [ ] **NFR-003**: 접근성
  - [ ] 색상 대비 유지
  - [ ] 명확한 정보 계층 구조
  - [ ] 직관적인 시각적 디자인

- [ ] **NFR-004**: 유지보수성
  - [ ] 기존 코드 구조 유지
  - [ ] 명확한 코드 주석
  - [ ] 쉬운 설정 확장성

### 품질 기준
- [ ] **TRUST 5**: 품질 게이트 통과
  - [ ] Test-first: 테스트 커버리지 85% 이상
  - [ ] Readable: 명확한 코드 구조
  - [ ] Unified: 일관된 코딩 스타일
  - [ ] Secured: 보안 취약점 없음
  - [ ] Trackable: 변경 추적 가능

---

## 🚫 거절 기준 (Rejection Criteria)

### 즉각적 거절 (Immediate Rejection)
- 시간 정보가 여전히 표시되는 경우
- [Develop] 표시기가 여전히 표시되는 경우
- 필수 정보가 누락된 경우
- Windows 환경에서 한글 이모지가 깨지는 경우
- 렌더링 오류가 발생하는 경우

### 수정 후 재검토 (Fix and Re-test)
- 성능 향상 목표에 미달하는 경우
- 테스트 커버리지 85% 미만인 경우
- 일부 터미널 환경에서 호환성 문제가 있는 경우
- 코드 품질 가이드를 위반하는 경우

---

## 📝 검증 보고서 템플릿 (Verification Report Template)

```markdown
# 수용 테스트 보고서

## 테스트 개요
- **테스트 일자**: [날짜]
- **테스트 환경**: [Windows 버전, 터미널 환경]
- **테스터**: [이름]
- **SPEC 버전**: [버전]

## 테스트 결과 요약
- **총 테스트 케이스**: [수]
- **통과**: [수]
- **실패**: [수]
- **결과**: [PASS/FAIL]

## 상세 결과
### 기능 테스트
- [ ] 시간 표시 제거: 통과/실패
- [ ] [Develop] 표시기 제거: 통과/실패
- [ ] 필수 정보 보존: 통과/실패
- [ ] 렌더링 모드 호환성: 통과/실패

### 비기능 테스트
- [ ] 성능 향상: 통과/실패 (측정치: X% 향상)
- [ ] Windows 호환성: 통과/실패
- [ ] 접근성: 통과/실패
- [ ] 유지보수성: 통과/실패

### 품질 게이트
- [ ] TRUST 5 통과: 통과/실패
- [ ] 테스트 커버리지: [수]% (목표: 85% 이상)

## 발견된 문제
1. [문제 설명]
2. [문제 설명]

## 권장 사항
- [개선/수정 권장사항]

## 최종 결정
- [ ] 승인 (Approve)
- [ ] 조건부 승인 (Conditional Approval)
- [ ] 거절 (Reject)
```

---

## ✅ 최종 승인 조건 (Final Approval Conditions)

### 승인을 위한 필수 조건
1. 모든 수용 테스트 케이스 통과
2. 성능 목표 달성 (렌더링 시간 15% 향상)
3. Windows 환경 호환성 100% 보장
4. TRUST 5 품질 게이트 통과
5. 사용자 승인 테스트 통과

### 승인 절차
1. 개발자 자체 검증 완료
2. 코드 리뷰 통과
3. 수용 테스트 수행
4. 보고서 작성 및 검토
5. 최종 승인 결정

---

**상태**: draft
**다음 단계**: 구현 완료 후 수용 테스트 수행