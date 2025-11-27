# Windows 최적화 기능 배포 가이드

이 문서는 `moai-adk windows-optimize` 명령어를 다른 Windows 컴퓨터에서 사용할 수 있도록 배포하는 방법을 설명합니다.

## 빠른 시작 (가장 간단한 방법)

### 1단계: GitHub에 푸시

```bash
# 현재 변경사항 커밋 및 푸시
git add .
git commit -m "feat(windows): Add windows-optimize command"
git push origin main
```

### 2단계: 다른 컴퓨터에서 설치

```bash
# GitHub에서 직접 설치
pip install git+https://github.com/cyans/moai-adk.git

# 또는 uv 사용
uv pip install git+https://github.com/cyans/moai-adk.git
```

### 3단계: 사용

```bash
# 새 프로젝트 초기화
moai-adk init

# Windows 최적화 적용
moai-adk windows-optimize

# Claude Code 재시작
```

## 상세 가이드

### 방법 1: GitHub에서 직접 설치 (권장)

**장점:**
- 가장 간단하고 빠름
- 자동 업데이트 가능
- 버전 관리 용이

**단계:**

1. **GitHub에 푸시**
   ```bash
   git add .
   git commit -m "feat(windows): Add windows-optimize command"
   git push origin main
   ```

2. **다른 컴퓨터에서 설치**
   ```bash
   pip install git+https://github.com/cyans/moai-adk.git
   ```

3. **프로젝트에서 사용**
   ```bash
   cd my-project
   moai-adk init
   moai-adk windows-optimize
   ```

### 방법 2: 로컬 빌드 후 배포

**장점:**
- 인터넷 연결 불필요
- 특정 버전 고정 가능

**단계:**

1. **패키지 빌드**
   ```bash
   # 빌드 도구 설치
   pip install build
   
   # 패키지 빌드
   python -m build
   ```

2. **생성된 파일 확인**
   ```
   dist/
     ├── moai_adk-0.30.2-py3-none-any.whl
     └── moai-adk-0.30.2.tar.gz
   ```

3. **배포 방법**

   **옵션 A: GitHub Releases**
   - GitHub Releases에 wheel 파일 업로드
   - 다른 컴퓨터에서: `pip install https://github.com/cyans/moai-adk/releases/download/v0.30.2/moai_adk-0.30.2-py3-none-any.whl`

   **옵션 B: 로컬 파일 공유**
   - USB나 네트워크로 wheel 파일 복사
   - 다른 컴퓨터에서: `pip install moai_adk-0.30.2-py3-none-any.whl`

### 방법 3: PyPI에 배포 (고급)

원본 `moai-adk`와 충돌을 피하기 위해 다른 패키지 이름을 사용해야 합니다.

**단계:**

1. **pyproject.toml 수정**
   ```toml
   [project]
   name = "moai-adk-windows"  # 다른 이름 사용
   version = "0.30.2"
   ```

2. **PyPI에 배포**
   ```bash
   pip install twine
   twine upload dist/*
   ```

## 업데이트 방법

원본 moai-adk가 업데이트되면:

```bash
# 1. upstream에서 최신 변경사항 가져오기
git fetch upstream
git merge upstream/main

# 2. 충돌 해결 후
git push origin main

# 3. 다른 컴퓨터에서 업데이트
pip install --upgrade git+https://github.com/cyans/moai-adk.git
```

## 사용 예시

### 새 프로젝트에서

```bash
# 1. 설치
pip install git+https://github.com/cyans/moai-adk.git

# 2. 프로젝트 초기화
moai-adk init

# 3. Windows 최적화 적용
moai-adk windows-optimize

# 4. Claude Code 재시작
```

### 기존 프로젝트에서

```bash
# Windows 최적화만 적용
moai-adk windows-optimize

# 상세 로그 확인
moai-adk windows-optimize --verbose

# 미리보기 (변경사항만 확인)
moai-adk windows-optimize --dry-run
```

## 문제 해결

### 설치 오류

```bash
# 캐시 클리어 후 재설치
pip cache purge
pip install --no-cache-dir git+https://github.com/cyans/moai-adk.git
```

### 명령어를 찾을 수 없음

```bash
# Python 경로 확인
python -m moai_adk windows-optimize

# 설치 확인
pip show moai-adk
```

## 배포 체크리스트

배포 전 확인사항:

- [ ] `windows-optimize` 명령어가 정상 작동하는지 확인
- [ ] 모든 테스트 통과
- [ ] `pyproject.toml` 버전 업데이트
- [ ] GitHub에 푸시 완료
- [ ] 다른 컴퓨터에서 테스트 완료

## 참고 사항

- Windows 최적화 기능은 Windows 환경에서만 작동합니다
- `windows-optimize` 명령어는 프로젝트별로 실행해야 합니다
- 각 프로젝트에서 `moai-adk init` 후 `windows-optimize`를 실행하세요

