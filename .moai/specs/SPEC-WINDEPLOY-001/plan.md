# Windows 배포 파이프라인 자동화 - 구현 계획

## 개요

SPEC-WINDEPLOY-001의 Windows 배포 파이프라인 자동화 시스템 구현에 대한 상세 계획. 5단계 배포 워크플로우 자동화, 사용자 확인 시스템, GitHub Actions CI/CD 통합을 포함한 전체 구현 전략을 제시합니다.

---

## 구현 목표

### 1차 목표 (MVP)
- 1, 3, 4, 5, 6단계 자동화 워크플로우 엔진 구현
- 기본적인 사용자 확인 시스템 구현
- Windows 환경에서의 안정적인 배포 기능

### 2차 목표 (완성)
- GitHub Actions CI/CD 완전 통합
- 고급 사용자 확인 기능 (progress bar, 상세 로깅)
- 자동 롤백 및 복구 시스템
- WSL2 지원 확장

---

## 상세 구현 계획

### Phase 1: 기반 구조 구축

#### 1.1 프로젝트 구조 설계
```
src/moai_adk/deployment/
├── __init__.py
├── windows/
│   ├── __init__.py
│   ├── workflow.py          # 배포 워크플로우 엔진
│   ├── steps.py            # 단계별 실행 로직
│   ├── confirmation.py     # 사용자 확인 시스템
│   ├── optimizer.py        # Windows 최적화
│   └── rollback.py         # 롤백 관리
├── cli/
│   └── commands.py         # CLI 명령어
└── utils/
    ├── git_helper.py       # Git 조작 도우미
    └── github_api.py       # GitHub API 연동
```

#### 1.2 핵심 모듈 설계
- **DeploymentWorkflow**: 전체 배프 프로세스 관리
- **StepConfirmation**: 사용자 인터페이스 및 확인
- **WindowsOptimizer**: Windows 특화 처리
- **RollbackManager**: 백업 및 복원 기능

#### 1.3 의존성 관리
```python
# pyproject.toml 추가 의존성
[project.optional-dependencies]
deployment = [
    "click>=8.0.0",          # CLI 인터페이스
    "rich>=12.0.0",          # 진행 상황 표시
    "github-api>=1.0.1",     # GitHub API 연동
    "pyyaml>=6.0",           # YAML 설정 처리
    "requests>=2.28.0",      # HTTP 요청
]
```

### Phase 2: 배포 워크플로우 엔진 구현

#### 2.1 단계별 실행 로직
```python
class DeploymentStep:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = "pending"

    async def execute(self) -> StepResult:
        """단계 실행 로직"""
        pass

    async def rollback(self) -> bool:
        """단계 롤백 로직"""
        pass

class DeploymentWorkflow:
    def __init__(self):
        self.steps = [
            CodeIntegrationStep(),
            UpstreamSetupStep(),
            GitHubPushStep(),
            LocalUpdateStep(),
            WindowsTestStep(),
            FutureUpdatesStep()
        ]
        self.current_step = 0

    async def execute_workflow(self):
        """전체 워크플로우 실행"""
        for i, step in enumerate(self.steps):
            if await self.confirm_step(step):
                result = await step.execute()
                if not result.success:
                    await self.handle_failure(i, result)
                    break
            else:
                self.console.print(f"[yellow]{step.name} 건너뛰기[/yellow]")
```

#### 2.2 단계별 상세 기능

**1단계: 코드 통합 (CodeIntegrationStep)**
```python
class CodeIntegrationStep(DeploymentStep):
    async def execute(self):
        """윈도우 최적화 코드 자동 병합"""
        # 1. 현재 브랜치 확인
        current_branch = await self.git_helper.get_current_branch()

        # 2. 윈도우 최적화 브랜치 확인
        windows_branch = "feature/windows-optimization"

        # 3. 충돌 확인 및 자동 병합
        if await self.git_helper.has_conflicts(current_branch, windows_branch):
            return await self.handle_merge_conflicts()

        # 4. 병합 실행
        merge_result = await self.git_helper.merge_branches(
            current_branch, windows_branch
        )

        return StepResult(success=merge_result, data=merge_result)
```

**3단계: GitHub 푸시 (GitHubPushStep)**
```python
class GitHubPushStep(DeploymentStep):
    async def execute(self):
        """GitHub에 변경사항 푸시 및 PR 생성"""
        # 1. 로컬 변경사항 커밋
        commit_hash = await self.git_helper.commit_changes(
            message="Auto merge: Windows optimization deployment"
        )

        # 2. 원격 저장소에 푸시
        push_result = await self.git_helper.push_to_origin()

        # 3. PR 자동 생성 (필요시)
        if self.should_create_pr:
            pr_url = await self.github_api.create_pull_request(
                title="Windows Optimization Deployment",
                body="Automated deployment of Windows optimization features",
                base="main",
                head=self.current_branch
            )

        return StepResult(success=True, data={"pr_url": pr_url})
```

**4단계: 로컬 업데이트 (LocalUpdateStep)**
```python
class LocalUpdateStep(DeploymentStep):
    async def execute(self):
        """pip install --upgrade 자동화"""
        # 1. 현재 설치된 버전 확인
        current_version = await self.get_installed_version()

        # 2. PyPI에서 최신 버전 확인
        latest_version = await self.get_latest_pypi_version()

        # 3. 업데이트 실행
        if current_version < latest_version:
            update_result = await self.run_command([
                sys.executable, "-m", "pip", "install",
                "--upgrade", "moai-adk"
            ])

            if update_result.returncode == 0:
                return StepResult(success=True, data={"updated_to": latest_version})

        return StepResult(success=True, data={"status": "already_latest"})
```

### Phase 3: 사용자 확인 시스템

#### 3.1 인터랙티브 인터페이스
```python
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, TaskID
from rich.table import Table

class StepConfirmation:
    def __init__(self):
        self.console = Console()

    async def confirm_step(self, step: DeploymentStep) -> bool:
        """단계 실행 전 사용자 확인"""
        # 현재 상태 표시
        self._show_current_status(step)

        # 사용자 선택 받기
        choice = Prompt.ask(
            "\n[yellow]다음 단계를 실행하시겠습니까?[/yellow]",
            choices=["실행", "건너뛰기", "중단"],
            default="실행"
        )

        if choice == "중단":
            raise KeyboardInterrupt("사용자가 배포를 중단했습니다")

        return choice == "실행"

    def _show_current_status(self, step: DeploymentStep):
        """현재 단계 상태 표시"""
        table = Table(title="배포 상태")
        table.add_column("항목", style="cyan")
        table.add_column("내용", style="white")

        table.add_row("현재 단계", step.name)
        table.add_row("설명", step.description)
        table.add_row("상태", step.status)

        self.console.print(table)

    def show_progress(self, step_name: str, progress: float):
        """진행 상황 표시"""
        self.console.print(f"[blue]{step_name}[/blue] 진행률: {progress:.1%}")
```

#### 3.2 실시간 로깅 시스템
```python
import logging
from rich.logging import RichHandler

class DeploymentLogger:
    def __init__(self):
        self.logger = logging.getLogger("deployment")
        self.logger.addHandler(RichHandler(console=self.console))
        self.logger.setLevel(logging.INFO)

    def log_step_start(self, step_name: str):
        self.logger.info(f"[green]{step_name}[/green] 시작")

    def log_step_complete(self, step_name: str, duration: float):
        self.logger.info(f"[green]{step_name}[/green] 완료 ({duration:.2f}초)")

    def log_error(self, step_name: str, error: Exception):
        self.logger.error(f"[red]{step_name}[/red] 실패: {error}")
```

### Phase 4: GitHub Actions CI/CD 통합

#### 4.1 워크플로우 파일 구성
```yaml
# .github/workflows/windows-deploy.yml
name: Windows Deployment Pipeline

on:
  push:
    branches: [main, develop]
    paths: ['src/moai_adk/**']
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      stage:
        description: 'Deployment stage to run'
        required: true
        default: 'full'
        type: choice
        options:
          - full
          - test-only
          - deploy-only

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'

jobs:
  windows-deploy:
    runs-on: windows-latest
    timeout-minutes: 30

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.cache/pip
            node_modules
          key: ${{ runner.os }}-deps-${{ hashFiles('**/pyproject.toml') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[deployment]
          npm install -g @upstash/context7-mcp@latest

      - name: Run Windows tests
        run: |
          pytest tests/windows/ -v --cov=moai_adk
        env:
          PYTHONPATH: ${{ github.workspace }}

      - name: Build package
        run: |
          python -m build

      - name: Deploy to PyPI (on main)
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: |
          python -m twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}

      - name: Create Release
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ github.run_number }}
          release_name: Release v${{ github.run_number }}
          draft: false
          prerelease: false
```

#### 4.2 테스트 자동화
```python
# tests/windows/test_deployment.py
import pytest
import asyncio
from moai_adk.deployment.windows.workflow import DeploymentWorkflow

class TestDeploymentWorkflow:
    @pytest.fixture
    async def workflow(self):
        return DeploymentWorkflow()

    @pytest.mark.asyncio
    async def test_full_deployment(self, workflow):
        """전체 배포 워크플로우 테스트"""
        result = await workflow.execute_workflow()
        assert result.success == True

    @pytest.mark.asyncio
    async def test_step_execution(self, workflow):
        """개별 단계 실행 테스트"""
        for step in workflow.steps:
            result = await step.execute()
            assert result.success == True

    @pytest.mark.asyncio
    async def test_rollback_functionality(self, workflow):
        """롤백 기능 테스트"""
        # 일부 단계 실행 후 실패 시뮬레이션
        workflow.steps[2].force_failure = True

        with pytest.raises(DeploymentFailed):
            await workflow.execute_workflow()

        # 롤백 확인
        assert workflow.rollback_manager.has_backup()
```

### Phase 5: Windows 특화 최적화

#### 5.1 경로 및 인코딩 처리
```python
import os
import sys
from pathlib import Path

class WindowsOptimizer:
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        self.is_wsl = self._detect_wsl()

    def _detect_wsl(self) -> bool:
        """WSL2 환경 감지"""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except FileNotFoundError:
            return False

    def normalize_path(self, path: str) -> str:
        """Windows 경로 정규화"""
        if self.is_windows:
            return str(Path(path).as_posix())
        return path

    def setup_encoding(self):
        """Windows 인코딩 설정"""
        if self.is_windows:
            # UTF-8 기반 인코딩 설정
            os.environ['PYTHONIOENCODING'] = 'utf-8'

            # Console encoding 설정
            import locale
            try:
                locale.setlocale(locale.LC_ALL, 'Korean_Korea.UTF8')
            except locale.Error:
                pass  # 기본값 사용

    def configure_windows_env(self):
        """Windows 환경변수 설정"""
        if self.is_windows:
            # APPDATA 경로 설정
            appdata = os.environ.get('APPDATA', '')
            if appdata:
                os.environ['MOAI_CONFIG_DIR'] = os.path.join(appdata, 'moai-adk')

            # USERPROFILE 경로 설정
            userprofile = os.environ.get('USERPROFILE', '')
            if userprofile:
                os.environ['MOAI_DATA_DIR'] = os.path.join(userprofile, '.moai')
```

#### 5.2 PowerShell 호환성
```python
import subprocess
from typing import List, Optional

class PowerShellExecutor:
    def __init__(self):
        self.ps_available = self._check_powershell()

    def _check_powershell(self) -> bool:
        """PowerShell 사용 가능 여부 확인"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Host'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def execute_command(self, command: str) -> subprocess.CompletedProcess:
        """PowerShell 명령어 실행"""
        if self.ps_available:
            return await asyncio.create_subprocess_exec(
                'powershell', '-Command', command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            # CMD fallback
            return await asyncio.create_subprocess_exec(
                'cmd', '/c', command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
```

---

## 기술 스택 및 도구

### 핵심 기술 스택
- **Python 3.11+**: 주요 개발 언어
- **Click**: CLI 프레임워크
- **Rich**: 터미널 UI 및 진행 상황 표시
- **PyYAML**: 설정 파일 처리
- **GitHub API**: 저장소 조작
- **pytest**: 테스트 프레임워크

### CI/CD 도구
- **GitHub Actions**: 배포 파이프라인
- **Windows Runner**: Windows 환경 테스트
- **PyPI**: 패키지 배포
- **Twine**: Python 패키지 업로드

### 개발 및 테스트 도구
- **pytest-asyncio**: 비동기 테스트
- **pytest-cov**: 코드 커버리지
- **black**: 코드 포매팅
- **flake8**: 린팅
- **mypy**: 타입 검사

---

## 타임라인 및 마일스톤

### 1주차: 기반 구조
- 프로젝트 구조 설계 및 구현
- 핵심 모듈 기본 구조 작성
- 의존성 설정 및 개발 환경 구축

### 2주차: 워크플로우 엔진
- 배포 워크플로우 엔진 구현
- 1, 3, 4단계 자동화 로직 작성
- 기본적인 사용자 확인 시스템

### 3주차: CI/CD 통합
- GitHub Actions 워크플로우 작성
- Windows 환경 테스트 자동화
- PyPI 배포 연동

### 4주차: 최적화 및 테스트
- Windows 특화 최적화 구현
- 롤백 및 복구 기능 완성
- 전체 시스템 통합 테스트

---

## 리소스 요구사항

### 개발 리소스
- **개발자**: 1-2명 (Python, Windows 환경 전문가)
- **DevOps 엔지니어**: 1명 (GitHub Actions, CI/CD 전문가)
- **테스터**: 1명 (Windows 다양한 환경 테스트)

### 기술 리소스
- **GitHub 저장소**: 소스 코드 관리
- **PyPI 계정**: 패키지 배포
- **Windows 테스트 환경**: 다양한 Windows 10/11 버전
- **WSL2 환경**: Linux 호환성 테스트

---

## 위험 관리 계획

### 기술적 위험
- **Windows 호환성**: 다양한 Windows 버전 테스트 수행
- **Git 충돌**: 자동 병합 실패 시 수동 개입 프로세스
- **네트워크 오류**: 재시도 메커니즘 및 오프라인 모드

### 운영적 위험
- **배포 실패**: 롤백 기능 및 이전 버전 복원
- **권한 문제**: 사전 권한 확인 및 명확한 에러 메시지
- **데이터 손실**: 자동 백업 및 상태 저장

---

## 성공 기준

### 기능적 기준
- 모든 5개 단계가 성공적으로 자동화
- 사용자 확인 시스템 정상 동작
- Windows 환경에서 안정적인 배포

### 품질 기준
- 테스트 커버리지 85% 이상
- 배포 성공률 95% 이상
- 롤백 성공률 100%

### 성능 기준
- 전체 배포 시간 10분 이내
- 단계별 실행 시간 2분 이내
- 오류 복구 시간 1분 이내