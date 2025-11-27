# 모델 설정 스크립트 문서

**프로젝트**: moai-adk-윈도우최적화
**문서 버전**: 1.0.0
**작성일**: 2025-11-27
**최종 업데이트**: 2025-11-27
**작성자**: @cyans

---

## 📋 개요

본 문서는 Windows 환경에서 MoAI-ADK의 Claude 모델(GLM, Opus)을 설정하는 스크립트들의 상세한 기능과 사용법을 설명합니다. 각 스크립트의 특징, 설정 방법, 문제 해결 방법을 다룹니다.

---

## 🏗️ 스크립트 아키텍처

### 스크립트 목록

| 스크립트명 | 모델 | 주요 기능 | 실행 환경 |
|-----------|------|----------|----------|
| `claude-glm.bat` | GLM | 기본 설정, API 키 설정 | Windows Batch |
| `setup-glm.py` | GLM | Python 기반 설정 | Python 3.8+ |
| `setup-opus.py` | Opus | 고급 모델 설정 | Python 3.8+ |

### 스크립트 의존성

```
공통 의존성:
├── Python 3.8+
├── requests (>=2.25.1)
├── python-dotenv (>=0.19.0)
├── pyyaml (>=6.0)
└── click (>=8.0.0)

Windows 특화:
├── Windows 10/11
├── cmd.exe (배치 스크립트)
└── Windows 배치 처리
```

---

## 📄 자세한 스크립트 문서

### 1. claude-glm.bat

#### 개요
Claude GLM을 위한 Windows 배치 스크립트로, 사용자 친화적인 설치 가이드와 자동화된 설정 제공.

#### 기능 상세

```batch
@echo off
TITLE Claude GLM Setup for MoAI-ADK

echo ========================================
echo Claude GLM Setup for MoAI-ADK
echo ========================================
echo.
```

#### 주요 기능

1. **사전 환경 검사**
   ```batch
   # Python 버전 확인
   python --version >nul 2>&1
   IF %ERRORLEVEL% NEQ 0 (
       echo Python이 설치되어 있지 않습니다.
       pause
       exit /b 1
   )

   # 설정 파일 존재 확인
   IF NOT EXIST "settings.local.json" (
       echo settings.local.json 파일을 찾을 수 없습니다.
       echo 기본 설정 파일을 생성합니다...
       copy settings.template.json settings.local.json
   )
   ```

2. **API 키 유효성 검사**
   ```batch
   # .env 파일 존재 확인
   IF NOT EXIST ".env" (
       echo .env 파일을 찾을 수 없습니다.
       echo 환경 변수 설정을 확인하세요...
       pause
       exit /b 1
   )

   # API 키 포함 확인
   findstr /C:"GLM_API_KEY" ".env" >nul
   IF %ERRORLEVEL% NEQ 0 (
       echo GLM API 키가 설정되지 않았습니다.
       pause
       exit /b 1
   )
   ```

3. **설정 스크립트 호출**
   ```batch
   # Python 스크립트 실행
   python setup-glm.py

   IF %ERRORLEVEL% NEQ 0 (
       echo GLM 설정에 실패했습니다.
       pause
       exit /b 1
   )
   ```

4. **설치 완료 가이드**
   ```batch
   echo ========================================
   echo 설정이 완료되었습니다!
   echo ========================================
   echo.
   echo 다음 단계:
   echo 1. .moai/config/config.json 설정 확인
   echo 2. /moai:0-project 실행으로 프로젝트 초기화
   echo 3. /moai:1-plan으로 기능 개발 계획 수립
   echo.
   ```

#### 사용법

```batch
# 기본 실행
.\claude-glm.bat

# 관리자 권한으로 실행
runas /user:Administrator ".\claude-glm.bat"
```

#### 고급 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `/S` | 무인 모드 (대화 없음) | `claude-glm.bat /S` |
| `/V` | 상세 로깅 | `claude-glm.bat /V` |
| `/R` | 재설치 모드 | `claude-glm.bat /R` |

---

### 2. setup-glm.py

#### 개요
Python으로 작성된 Claude GLM 설정 스크립트. 구조화된 설정 파일 관리, 의존성 설치, 자동 검증 기능 제공.

#### 클래스 구조

```python
class GLMSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / ".claude" / "settings.local.json"
        self.moai_config = self.project_root / ".moai" / "config" / "config.json"
        self.env_file = self.project_root / ".env"
```

#### 상세 메서드 분석

##### 1. 환경 검사 메서드

```python
def check_environment(self) -> Dict[str, Any]:
    """시스템 환경 상세 검사"""
    env_info = {
        'python_version': sys.version,
        'python_path': sys.executable,
        'platform': sys.platform,
        'os_version': platform.system(),
        'architecture': platform.architecture(),
        'dependencies': {}
    }

    # 필요한 패키지 확인
    required_packages = [
        'requests', 'python_dotenv', 'pyyaml', 'click'
    ]

    for package in required_packages:
        try:
            __import__(package)
            env_info['dependencies'][package] = 'installed'
        except ImportError:
            env_info['dependencies'][package] = 'missing'

    return env_info
```

##### 2. 설정 파일 관리

```python
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

def save_settings(self, config: Dict[str, Any]) -> bool:
    """설정 파일 저장"""
    try:
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"설정 파일 저장 실패: {e}")
        return False
```

##### 3. API 키 관리

```python
def setup_api_key(self) -> bool:
    """API 키 설정"""
    if not self.check_api_key():
        print("API 키 설정이 필요합니다.")

        # 인터랙티브 입력
        api_key = input("GLM API 키를 입력하세요: ").strip()

        if not api_key:
            print("API 키가 입력되지 않았습니다.")
            return False

        # 환경 변수 파일 업데이트
        with open(self.env_file, 'a', encoding='utf-8') as f:
            f.write(f"GLM_API_KEY={api_key}\n")

        print("API 키가 설정되었습니다.")
        return True
    return True

def validate_api_key(self) -> bool:
    """API 키 유효성 검사"""
    if not self.check_api_key():
        return False

    # 간단한 형식 검사
    with open(self.env_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'GLM_API_KEY=' in line:
                api_key = line.split('=')[1].strip()
                if len(api_key) >= 32:  # 일반적인 API 키 길이
                    return True

    print("API 키 형식이 올바르지 않습니다.")
    return False
```

##### 4. 의존성 관리

```python
def install_dependencies(self) -> bool:
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
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                dep,
                "--quiet"  # 조용한 모드
            ])
            print(f"✅ {dep} 설치 완료")
        except subprocess.CalledProcessError as e:
            print(f"❌ {dep} 설치 실패: {e}")
            return False

    return True

def check_dependencies(self) -> Dict[str, bool]:
    """의존성 상태 확인"""
    deps = {
        'requests': False,
        'python_dotenv': False,
        'yaml': False,
        'click': False
    }

    for dep in deps:
        try:
            __import__(dep)
            deps[dep] = True
        except ImportError:
            deps[dep] = False

    return deps
```

##### 5. 디렉토리 구조 생성

```python
def create_directories(self) -> bool:
    """필요한 디렉토리 생성"""
    directories = [
        self.project_root / ".moai" / "specs",
        self.project_root / ".moai" / "docs",
        self.project_root / ".moai" / "reports",
        self.project_root / ".moai" / "memory",
        self.project_root / ".moai" / "logs",
        self.project_root / ".claude" / "skills",
        self.project_root / ".claude" / "agents",
        self.project_root / ".claude" / "hooks",
        self.project_root / ".claude" / "output-styles",
        self.project_root / ".claude" / "settings"
    ]

    created_dirs = []
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(directory))
        except Exception as e:
            print(f"디렉토리 생성 실패: {directory} - {e}")
            return False

    print(f"디렉토리 생성 완료: {len(created_dirs)}개")
    return True
```

##### 6. 설정 검증

```python
def verify_setup(self) -> bool:
    """설정 검증"""
    print("\n설정 검증을 시작합니다...")

    checks = [
        ("settings.local.json", self.config_file.exists()),
        ("MoAI 구성 파일", self.moai_config.exists()),
        ("환경 변수 파일", self.env_file.exists()),
        ("API 키 설정", self.check_api_key()),
        ("specs 디렉토리", (self.project_root / ".moai" / "specs").exists()),
        ("docs 디렉토리", (self.project_root / ".moai" / "docs").exists()),
        ("의존성 패키지", all(self.check_dependencies().values()))
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n모든 설정 검증이 통과했습니다!")
        return True
    else:
        print("\n일부 설정 검증이 실패했습니다.")
        return False
```

#### 실행 로직

```python
def run_setup(self) -> bool:
    """설치 프로세스 실행"""
    print("Claude GLM 설정을 시작합니다...")

    try:
        # 1. 환경 검사
        env_info = self.check_environment()
        print(f"Python 버전: {env_info['python_version']}")
        print(f"플랫폼: {env_info['platform']}")

        # 2. 디렉토리 생성
        if not self.create_directories():
            return False

        # 3. API 키 설정
        if not self.setup_api_key():
            return False

        # 4. MoAI 구성 업데이트
        if not self.update_moai_config():
            return False

        # 5. 의존성 설치
        if not self.install_dependencies():
            return False

        # 6. 설정 검증
        if not self.verify_setup():
            return False

        print("\n🎉 설정이 성공적으로 완료되었습니다!")
        print("\n다음 단계:")
        print(f"1. cd {self.project_root}")
        print("2. /moai:0-project")
        print("3. /moai:1-plan \"프로젝트 기능 설명\"")

        return True

    except Exception as e:
        print(f"\n설치 중 오류 발생: {e}")
        return False
```

---

### 3. setup-opus.py

#### 개요
Claude Opus 고급 모델을 위한 전문 설정 스크립트. 고급 설정, 성능 최적화, 전용 실행 환경 제공.

#### 차별화 기능

```python
class OpusSetup(GLMSetup):  # GLMSetup 상속
    def __init__(self):
        super().__init__()
        self.opus_config = self.config_file.parent / "opus-config.json"
```

#### 고급 설정 관리

```python
def setup_opus_config(self) -> bool:
    """Opus 전용 구성 설정"""
    try:
        config = self.load_settings()

        # Opus 설정 추가
        config.setdefault('opus', {})
        config['opus'].update({
            'enabled': True,
            'model': 'claude-3-opus-20240229',
            'max_tokens': 4096,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40
        })

        # 고급 API 설정
        config.setdefault('api', {})
        config['api'].update({
            'base_url': 'https://api.anthropic.com',
            'version': '2023-06-01',
            'timeout': 60,
            'retries': 3
        })

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print("Opus 설정이 완료되었습니다.")
        return True

    except Exception as e:
        print(f"Opus 설정 실패: {e}")
        return False
```

#### 실행 환경 생성

```python
def create_opus_batch(self) -> bool:
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

    try:
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)

        # 실행 권한 설정 (Windows에서는 무시되지만 다른 플랫폼을 위해)
        os.chmod(batch_file, 0o755)

        print(f"Opus 배치 파일 생성: {batch_file}")
        return True

    except Exception as e:
        print(f"배치 파일 생성 실패: {e}")
        return False
```

#### 성능 최적화 설정

```python
def optimize_performance(self) -> bool:
    """성능 최적화 설정"""
    try:
        config = self.load_settings()

        # 성능 설정
        config.setdefault('performance', {})
        config['performance'].update({
            'cache_enabled': True,
            'cache_size': '1GB',
            'parallel_processing': True,
            'max_workers': 4,
            'memory_limit': '8GB',
            'disk_cleanup': True
        })

        # 로깅 설정
        config.setdefault('logging', {})
        config['logging'].update({
            'level': 'INFO',
            'file_logging': True,
            'log_rotation': True,
            'max_log_size': '100MB',
            'backup_count': 5
        })

        self.save_settings(config)
        print("성능 최적화 설정이 완료되었습니다.")
        return True

    except Exception as e:
        print(f"성능 최적화 실패: {e}")
        return False
```

---

## 🔧 스크립트 확장 및 커스터마이징

### 사용자 정의 스크립트 예제

```python
# custom-setup.py
import json
import os
from pathlib import Path

class CustomSetup(GLMSetup):
    def __init__(self):
        super().__init__()
        self.custom_config = self.project_root / "custom-config.json"

    def add_custom_features(self):
        """사용자 정의 기능 추가"""
        config = self.load_settings()

        # 사용자 정의 설정
        config.setdefault('custom', {})
        config['custom'].update({
            'feature_flags': {
                'experimental_ai': True,
                'advanced_logging': False,
                'auto_backup': True
            },
            'preferences': {
                'language': 'ko',
                'theme': 'dark',
                'auto_update': True
            }
        })

        self.save_settings(config)
        print("사용자 정의 설정이 추가되었습니다.")
```

### 설정 템플릿 시스템

```python
# config-templates.py
from enum import Enum
from typing import Dict, Any

class ConfigTemplate(Enum):
    """사전 정의된 설정 템플릿"""
    DEVELOPMENT = {
        'name': '개발 환경',
        'features': {
            'debug_mode': True,
            'auto_reload': True,
            'test_coverage': 100
        }
    }

    PRODUCTION = {
        'name': '운영 환경',
        'features': {
            'debug_mode': False,
            'auto_reload': False,
            'test_coverage': 90,
            'security_hardening': True
        }
    }

    TESTING = {
        'name': '테스트 환경',
        'features': {
            'debug_mode': True,
            'auto_reload': False,
            'test_coverage': 95,
            'mock_data': True
        }
    }

def apply_template(template: ConfigTemplate) -> Dict[str, Any]:
    """설정 템플릿 적용"""
    return template.value
```

---

## 🚀 배포 및 관리

### 스크립트 패키징

```python
# setup-package.py
import subprocess
import shutil
from pathlib import Path

class ScriptPackager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"

    def create_installer(self):
        """설치 패키지 생성"""
        # 배드 디렉토리 정리
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

        # 디렉토리 구조 생성
        directories = [
            self.build_dir / "scripts",
            self.build_dir / "config",
            self.build_dir / "docs"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        # 스크립트 복사
        shutil.copy2(self.project_root / "claude-glm.bat",
                     self.build_dir / "scripts")
        shutil.copy2(self.project_root / "setup-glm.py",
                     self.build_dir / "scripts")
        shutil.copy2(self.project_root / "setup-opus.py",
                     self.build_dir / "scripts")

        # 설정 파일 복사
        shutil.copy2(self.project_root / "settings.template.json",
                     self.build_dir / "config")

        # 문서 복사
        shutil.copy2(self.project_root / "README.md",
                     self.build_dir / "docs")

        print("설치 패키지가 생성되었습니다:", self.build_dir)
```

### 버전 관리

```python
# version-manager.py
import json
from datetime import datetime
from pathlib import Path

class VersionManager:
    def __init__(self):
        self.version_file = Path(__file__).parent / "version.json"

    def get_version(self) -> str:
        """현재 버전 정보"""
        if self.version_file.exists():
            with open(self.version_file, 'r') as f:
                return json.load(f).get('version', '1.0.0')
        return '1.0.0'

    def update_version(self, new_version: str):
        """버전 업데이트"""
        version_info = {
            'version': new_version,
            'updated_at': datetime.now().isoformat(),
            'changelog': '버전 업데이트'
        }

        with open(self.version_file, 'w') as f:
            json.dump(version_info, f, indent=2)

        print(f"버전이 업데이트되었습니다: {new_version}")
```

---

## 📊 모니터링 및 로깅

### 실행 로깅

```python
# logging-setup.py
import logging
from pathlib import Path
from datetime import datetime

class SetupLogger:
    def __init__(self):
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # 로거 설정
        self.logger = logging.getLogger('moai-setup')
        self.logger.setLevel(logging.INFO)

        # 핸들러 설정
        log_file = self.log_dir / f"setup_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        console_handler = logging.StreamHandler()

        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_step(self, step: str, status: str):
        """설치 단계 로깅"""
        self.logger.info(f"[STEP] {step}: {status}")

    def log_error(self, error: str):
        """오류 로깅"""
        self.logger.error(f"[ERROR] {error}")

    def log_success(self, message: str):
        """성공 로깅"""
        self.logger.info(f"[SUCCESS] {message}")
```

---

## 🔒 보안 설정

### 환경 변수 보안

```python
# security-manager.py
import os
import secrets
from pathlib import Path
from typing import Optional

class SecurityManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"

    def generate_secure_key(self, length: int = 32) -> str:
        """보안 키 생성"""
        return secrets.token_urlsafe(length)

    def secure_environment_file(self):
        """환경 변수 파일 보안 설정"""
        if not self.env_file.exists():
            # 새로운 환경 변수 파일 생성
            env_content = f"""
# MoAI-ADK 환경 변수
GLM_API_KEY={self.generate_secure_key()}
GLM_MODEL=claude-3-sonnet-20240229
GLM_MAX_TOKENS=4096
GLM_TEMPERATURE=0.7
            """

            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(env_content.strip())

            # 파일 권한 설정 (Unix 시스템에서만 유효)
            os.chmod(self.env_file, 0o600)

            print("보안 환경 변수 파일이 생성되었습니다.")
```

---

## 📋 설정 체크리스트

### 스크립트 실행 전 확인사항

- [ ] Python 3.8+ 설치 확인
- [ ] 필요한 패키지 설치 확인
- [ ] 네트워크 연결 확인
- [ ] API 키 준비
- [ ] 관리자 권한 확인 (필요한 경우)

### 설정 후 확인사항

- [ ] 설정 파일 생성 확인
- [ ] 환경 변수 설정 확인
- [ ] 의존성 설치 확인
- [ ] 디렉토리 구조 확인
- [ ] 설정 검증 통과 확인

---

## 📞 지원 및 리소스

### 문제 해결

```python
# troubleshooting.py
class Troubleshooter:
    def common_issues(self):
        """일반적인 문제 해결 가이드"""
        issues = {
            "Python not found": [
                "Python 3.8+ 설치 확인",
                "PATH 환경 변수 설정 확인",
                "재부팅 후 재시도"
            ],
            "API key error": [
                "API 키 형식 확인 (32자 이상)",
                "파일 권한 확인",
                "API 키 유효성 확인"
            ],
            "Permission denied": [
                "관리자 권한으로 실행",
                "파일 권한 확인",
                "안티바이러스 설정 확인"
            ]
        }

        return issues
```

### 관련 문서

- [MoAI 공식 문서](https://moai-ai.github.io/docs/)
- [Claude API 문서](https://docs.anthropic.com/claude)
- [Python 배치 스크립트 가이드](https://docs.python.org/3/library/subprocess.html)

### 버전 정보

| 스크립트 | 버전 | 최신 업데이트 |
|---------|------|--------------|
| claude-glm.bat | 1.0.0 | 2025-11-27 |
| setup-glm.py | 1.0.0 | 2025-11-27 |
| setup-opus.py | 1.0.0 | 2025-11-27 |

---

**문서 유지보수**: 이 문서는 주요 버전 업데이트 시 함께 갱신됩니다. 버전 1.0.0의 모든 기능이 포함되어 있습니다.