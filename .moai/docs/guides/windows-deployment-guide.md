# Windows 배포 자동화 가이드

**프로젝트**: moai-adk-윈도우최적화
**문서 버전**: 1.0.0
**작성일**: 2025-11-27
**최종 업데이트**: 2025-11-27
**작성자**: @cyans

---

## 📋 개요

본 가이드는 Windows 환경에서 MoAI-ADK의 Claude Code를 설정하고 배포하는 자동화 프로세스를 상세히 설명합니다. 스크립트 기반의 자동화를 통해 반복적인 작업을 효율화하고 설정 오류를 최소화합니다.

---

## 🎯 배포 아키텍처

### 시스템 요구사항

| 항목 | 최소 요구사항 | 권장 사양 |
|------|-------------|-----------|
| OS | Windows 10 Pro/Enterprise | Windows 11 Pro/Enterprise |
| Python | 3.8 이상 | 3.10 이상 |
| 메모리 | 4GB | 8GB 이상 |
| 디스크 | 2GB 여유 공간 | 5GB 이상 |
| 네트워크 | 인터넷 연결 | 안정적 연결 |

### 배포 구조

```
moai-adk-윈도우최적화/
├── .moai/
│   ├── scripts/
│   │   ├── claude-glm.bat        # Claude GLM 배치 스크립트
│   │   ├── setup-glm.py          # GLM 설정 스크립트
│   │   └── setup-opus.py         # Opus 설정 스크립트
├── .claude/
│   ├── skills/                   # MoAI 기술 패키지
│   └── agents/                   # MoAI 에이전트 정의
└── 기본 프로젝트 구조
```

---

## 🚀 배포 프로세스

### 1단계: 사전 준비

#### 환경 검사

배포를 시작하기 전에 시스템 환경을 검사합니다:

```bash
# Python 버전 확인
python --version

# Git 설치 확인
git --version

# 필요한 라이브러리 설치
pip install requests
pip install python-dotenv
```

#### 디렉토리 구조 생성

```bash
# 기본 디렉토리 생성
mkdir -p C:\claude-code\moai-adk-윈도우최적화
cd C:\claude-code\moai-adk-윈도우최적화

# Git 저장소 초기화
git init
```

### 2단계: 스크립트 기반 배포

#### Claude GLM 배치 스크립트 실행

```batch
@echo off
TITLE Claude GLM Setup for MoAI-ADK

echo ========================================
echo Claude GLM Setup for MoAI-ADK
echo ========================================
echo.

REM 설정 파일 확인
IF NOT EXIST "settings.local.json" (
    echo settings.local.json 파일을 찾을 수 없습니다.
    echo 기본 설정 파일을 생성합니다...
    copy settings.template.json settings.local.json
)

REM API 키 설정 확인
IF NOT EXIST ".env" (
    echo .env 파일을 찾을 수 없습니다.
    echo 환경 변수 설정을 확인하세요...
    pause
    exit /b 1
)

REM Python 실행 파일 경로 확인
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python이 설치되어 있지 않습니다.
    echo Python 3.8 이상을 설치 후 다시 실행하세요.
    pause
    exit /b 1
)

REM GLM 설정 스크립트 실행
echo GLM 설정 스크립트를 실행합니다...
python setup-glm.py

IF %ERRORLEVEL% NEQ 0 (
    echo GLM 설정에 실패했습니다.
    pause
    exit /b 1
)

echo ========================================
echo 설정이 완료되었습니다!
echo ========================================
echo.
echo 다음 단계:
echo 1. .moai/config/config.json 설정 확인
echo 2. /moai:0-project 실행으로 프로젝트 초기화
echo 3. /moai:1-plan으로 기능 개발 계획 수립
echo.

pause
exit /b 0
```

#### Python GLM 설정 스크립트

```python
#!/usr/bin/env python3
"""
Claude GLM 설정 스크립트 for MoAI-ADK Windows 환경
"""

import os
import json
import requests
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

class GLMSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / ".claude" / "settings.local.json"
        self.moai_config = self.project_root / ".moai" / "config" / "config.json"
        self.env_file = self.project_root / ".env"

    def load_settings(self) -> Dict[str, Any]:
        """기존 설정 파일 로드"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"설정 파일을 찾을 수 없습니다: {self.config_file}")
            return {}
        except json.JSONDecodeError:
            print("설정 파일 형식이 올바르지 않습니다.")
            return {}

    def check_api_key(self) -> bool:
        """API 키 확인"""
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'GLM_API_KEY=' in line:
                        return True
        return False

    def setup_api_key(self):
        """API 키 설정"""
        if not self.check_api_key():
            print("API 키 설정이 필요합니다.")
            api_key = input("GLM API 키를 입력하세요: ").strip()

            if api_key:
                with open(self.env_file, 'a', encoding='utf-8') as f:
                    f.write(f"GLM_API_KEY={api_key}\n")
                print("API 키가 설정되었습니다.")
            else:
                print("API 키가 입력되지 않았습니다.")
                return False
        return True

    def update_moai_config(self):
        """MoAI 구성 업데이트"""
        try:
            config = {}
            if self.moai_config.exists():
                with open(self.moai_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # 기본 설정 업데이트
            config.setdefault('user', {}).setdefault('name', '@cyans')
            config.setdefault('language', {}).setdefault('conversation_language', 'ko')
            config.setdefault('language', {}).setdefault('agent_prompt_language', 'en')

            with open(self.moai_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            print("MoAI 구성이 업데이트되었습니다.")
            return True

        except Exception as e:
            print(f"MoAI 구성 업데이트 실패: {e}")
            return False

    def create_directories(self):
        """필요한 디렉토리 생성"""
        directories = [
            self.project_root / ".moai" / "specs",
            self.project_root / ".moai" / "docs",
            self.project_root / ".moai" / "reports",
            self.project_root / ".moai" / "memory",
            self.project_root / ".moai" / "logs",
            self.project_root / ".claude" / "skills",
            self.project_root / ".claude" / "agents"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"디렉토리 생성: {directory}")

    def install_dependencies(self):
        """필요한 패키지 설치"""
        dependencies = [
            "requests>=2.25.1",
            "python-dotenv>=0.19.0",
            "pyyaml>=6.0",
            "click>=8.0.0"
        ]

        for dep in dependencies:
            try:
                print(f"패키지 설치 중: {dep}")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            except subprocess.CalledProcessError:
                print(f"패키지 설치 실패: {dep}")
                return False

        return True

    def verify_setup(self):
        """설정 검증"""
        print("\n설정 검증을 시작합니다...")

        # 파일 존재 확인
        checks = [
            ("settings.local.json", self.config_file.exists()),
            ("MoAI 구성 파일", self.moai_config.exists()),
            ("환경 변수 파일", self.env_file.exists()),
            ("specs 디렉토리", (self.project_root / ".moai" / "specs").exists())
        ]

        all_passed = True
        for name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {name}")
            if not passed:
                all_passed = False

        if all_passed:
            print("\n모든 설정 검증이 통과했습니다!")
            return True
        else:
            print("\n일부 설정 검증이 실패했습니다.")
            return False

    def run_setup(self):
        """설치 프로세스 실행"""
        print("Claude GLM 설정을 시작합니다...")

        try:
            # 1. 디렉토리 생성
            self.create_directories()

            # 2. API 키 설정
            if not self.setup_api_key():
                return False

            # 3. MoAI 구성 업데이트
            if not self.update_moai_config():
                return False

            # 4. 의존성 설치
            if not self.install_dependencies():
                return False

            # 5. 설정 검증
            if not self.verify_setup():
                return False

            print("\n🎉 설정이 성공적으로 완료되었습니다!")
            print("\n다음 단계:")
            print("1. cd {self.project_root}")
            print("2. /moai:0-project")
            print("3. /moai:1-plan \"프로젝트 기능 설명\"")

            return True

        except Exception as e:
            print(f"\n설치 중 오류 발생: {e}")
            return False

if __name__ == "__main__":
    setup = GLMSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)
```

#### Opus 설정 스크립트

```python
#!/usr/bin/env python3
"""
Claude Opus 설정 스크립트 for MoAI-ADK Windows 환경
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

class OpusSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / ".claude" / "settings.local.json"
        self.moai_config = self.project_root / ".moai" / "config" / "config.json"
        self.env_file = self.project_root / ".env"

    def load_settings(self) -> Dict[str, Any]:
        """기존 설정 파일 로드"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def setup_opus_config(self):
        """Opus 전용 구성 설정"""
        try:
            config = self.load_settings()

            # Opus 설정 추가
            config.setdefault('opus', {})
            config['opus']['enabled'] = True
            config['opus']['model'] = 'claude-3-opus-20240229'
            config['opus']['max_tokens'] = 4096
            config['opus']['temperature'] = 0.7

            # API 엔드포인트 설정
            config.setdefault('api', {})
            config['api']['base_url'] = 'https://api.anthropic.com'
            config['api']['version'] = '2023-06-01'

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            print("Opus 설정이 완료되었습니다.")
            return True

        except Exception as e:
            print(f"Opus 설정 실패: {e}")
            return False

    def create_opus_batch(self):
        """Opus 실행 배치 파일 생성"""
        batch_content = """@echo off
TITLE Claude Opus for MoAI-ADK

echo ========================================
echo Claude Opus for MoAI-ADK
echo ========================================
echo.

REM 설정 확인
IF NOT EXIST ".env" (
    echo 환경 변수 파일이 없습니다.
    pause
    exit /b 1
)

REM API 키 확인
findstr /C:"GLM_API_KEY" ".env" >nul
IF %ERRORLEVEL% NEQ 0 (
    echo GLM API 키가 설정되지 않았습니다.
    pause
    exit /b 1
)

REM Claude 실행
echo Claude Opus를 실행합니다...
call claude

IF %ERRORLEVEL% NEQ 0 (
    echo 실행 실패했습니다.
    pause
    exit /b 1
)

echo.
echo 종료되었습니다.
pause
exit /b 0
"""

        batch_file = self.project_root / ".moai" / "scripts" / "claude-opus.bat"
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)

        # 실행 권한 부여
        os.chmod(batch_file, 0o755)
        print(f"Opus 배치 파일 생성: {batch_file}")

    def run_setup(self):
        """Opus 설정 실행"""
        print("Claude Opus 설정을 시작합니다...")

        try:
            # Opus 구성 설정
            if not self.setup_opus_config():
                return False

            # Opus 배치 파일 생성
            self.create_opus_batch()

            print("\n🎉 Opus 설정이 성공적으로 완료되었습니다!")
            print("\n사용 방법:")
            print("1. .moai/scripts/claude-opus.bat 실행")
            print("2. 또는 claude 명령어 직접 실행")

            return True

        except Exception as e:
            print(f"\n설치 중 오류 발생: {e}")
            return False

if __name__ == "__main__":
    setup = OpusSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)
```

---

## ⚙️ 설정 파일 구조

### 1. settings.local.json

```json
{
  "project": {
    "name": "moai-adk-윈도우최적화",
    "mode": "personal",
    "locale": "ko",
    "language": "generic"
  },
  "language": {
    "conversation_language": "ko",
    "agent_prompt_language": "en"
  },
  "constitution": {
    "enforce_tdd": true,
    "test_coverage_target": 90
  },
  "git_strategy": {
    "personal": {
      "auto_checkpoint": "disabled",
      "auto_commit": true,
      "branch_prefix": "feature/SPEC-"
    }
  },
  "opus": {
    "enabled": true,
    "model": "claude-3-opus-20240229",
    "max_tokens": 4096,
    "temperature": 0.7
  },
  "api": {
    "base_url": "https://api.anthropic.com",
    "version": "2023-06-01"
  }
}
```

### 2. .env 파일

```bash
# GLM API 키
GLM_API_KEY=your_api_key_here

# 선택적 설정
GLM_MODEL=claude-3-sonnet-20240229
GLM_MAX_TOKENS=4096
GLM_TEMPERATURE=0.7
```

---

## 🔧 문제 해결

### 일반적인 문제

#### 문제 1: Python이 설치되지 않음

**현상**: `python --version` 명령어가 인식되지 않음

**해결 방법**:
1. [Python 공식 홈페이지](https://www.python.org/)에서 Python 3.8+ 설치
2. "Add Python to PATH" 옵션 선택
3. 설치 후 재부팅
4. `python --version`으로 설치 확인

#### 문제 2: API 키 오류

**현상**: 인증 오류 발생

**해결 방법**:
1. [Anthropic Console](https://console.anthropic.com/)에서 API 키 발급
2. `.env` 파일에 정확한 API 키 설정
3. 파일 권한 확인 (600 설정)

#### 문제 3: 디렉토리 권한 오류

**현상**: 파일 생성 또는 수정 불가

**해결 방법**:
```bash
# 관리자 권한으로 실행
# 또는 특정 디렉토리 권한 설정
icacls "C:\claude-code\moai-adk-윈도우최적화" /grant Users:(OI)(CI)F
```

### 고급 문제 해결

#### 로그 파일 확인

```bash
# 로그 파일 위치
echo %USERPROFILE%\.claude\logs\
echo %USERPROFILE%\.moai\logs\
```

#### 설정 재설정

```batch
@echo off
echo 설정을 재설정합니다...
echo.

# 백업 생성
if exist settings.local.json (
    copy settings.local.json settings.local.json.backup
    echo 기존 설정이 백업되었습니다.
)

# 기본 설정으로 복원
copy settings.template.json settings.local.json
echo 설정이 초기화되었습니다.
pause
```

---

## 📊 모니터링 및 유지보수

### 성능 모니터링

```python
# monitoring.py
import psutil
import time
import json
from datetime import datetime

def monitor_performance():
    """시스템 성능 모니터링"""
    data = {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }

    with open('performance.log', 'a') as f:
        f.write(json.dumps(data) + '\n')

    return data

# 실행 예시
monitor_performance()
```

### 정기 유지보수 작업

| 작업 | 주기 | 설명 |
|------|------|------|
| 설정 검증 | 매주 | 설정 파일 무결성 확인 |
| 의존성 업데이트 | 매월 | 최신 패키지 버전 확인 |
| 로깅 정리 | 분기 | 오래된 로그 파일 삭제 |
| 백업 | 매일 | 중요 설정 파일 백업 |

---

## 🚀 배포 최적화

### 자동화 스크립트 개선

```python
# deploy.py
import os
import json
import subprocess
from pathlib import Path

class AutomatedDeploy:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_log = self.project_root / "deployment.log"

    def log_deployment(self, message: str):
        """배포 로깅"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        with open(self.deployment_log, 'a') as f:
            f.write(log_entry)

    def pre_deployment_checks(self):
        """사전 배포 검사"""
        checks = [
            ("Python 버전 확인", self.check_python_version()),
            ("의존성 설치 확인", self.check_dependencies()),
            ("설정 파일 검증", self.validate_config())
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            self.log_deployment(f"{check_name}: {status}")
            if not passed:
                all_passed = False

        return all_passed

    def deploy(self):
        """배포 실행"""
        if not self.pre_deployment_checks():
            self.log_deployment("배포 검사 실패 - 배포 중단")
            return False

        try:
            self.log_deployment("배포 시작")

            # 스크립트 실행
            subprocess.run(["python", "setup-glm.py"], check=True)
            subprocess.run(["python", "setup-opus.py"], check=True)

            self.log_deployment("배포 완료")
            return True

        except subprocess.CalledProcessError as e:
            self.log_deployment(f"배포 실패: {e}")
            return False

# 배포 실행
if __name__ == "__main__":
    deployer = AutomatedDeploy()
    success = deployer.deploy()
    sys.exit(0 if success else 1)
```

---

## 📋 배포 체크리스트

### 사전 배포 확인사항

- [ ] Python 3.8+ 설치 확인
- [ ] Git 설치 확인
- [ ] 디스크 공간 확인 (최소 2GB)
- [ ] 네트워크 연결 확인
- [ ] API 키 준비

### 배포 프로세스

- [ ] 프로젝트 디렉토리 생성
- [ ] Git 저장소 초기화
- [ ] 스크립트 파일 복사
- [ ] 환경 변수 설정
- [ ] 의존성 설치
- [ ] 설정 검증
- [ ] 테스트 실행

### 배포 후 확인

- [ ] 설정 검증 완료
- [ ] Claude 실행 확인
- [ ] MoAI 명령어 테스트
- [ ] 문서 생성 확인
- [ ] 로그 파일 확인

---

## 📞 지원 정보

### 기술 지원

- **이슈 리포트**: [GitHub Issues](https://github.com/your-repo/moai-adk-윈도우최적화/issues)
- **문서**: [MoAI 공식 문서](https://moai-ai.github.io/docs/)
- **커뮤니티**: [MoAI Discord 서버](https://discord.gg/moai)

### 연락처

- **개발자**: @cyans
- **이메일**: support@moai-ai.com
- **문서 버전**: 1.0.0

---

**문서 유지보수**: 이 문서는 프로젝트 업데이트에 따라 정기적으로 갱신됩니다. 변경사항은 `CHANGELOG.md` 파일에서 확인할 수 있습니다.