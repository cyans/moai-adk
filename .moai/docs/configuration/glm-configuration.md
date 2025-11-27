# GLM 환경 설정 가이드

**프로젝트**: moai-adk-윈도우최적화
**문서 버전**: 1.0.0
**작성일**: 2025-11-27
**최종 업데이트**: 2025-11-27
**작성자**: @cyans

---

## 📋 개요

본 문서는 MoAI-ADK에서 Claude GLM을 사용하기 위한 환경 설정 방법을 상세히 설명합니다. 설정 파일 구조, 환경 변수, 모델 선택, 성능 최적화 등 전반적인 설정 방법을 다룹니다.

---

## 🎯 설정 목표

### 주요 설정 목표

- [x] **언어 설정**: 한국어 대화, 영어 내부 추론 최적화
- [x] **모델 선택**: GLM/Opus 모델 적절한 선택 가이드
- [x] **성능 최적화**: 시스템 자원 효율적 사용
- [x] **보안 설정**: API 키 안전한 관리
- [x] **확장성**: 향후 모델 추가 용이한 구조

### 설정 우선순위

1. **기본 설정** (language, user.name)
2. **API 설정** (API 키, 엔드포인트)
3. **모델 설정** (GLM/Opus 선택, 파라미터)
4. **성능 설정** (캐시, 병렬 처리)
5. **보안 설정** (환경 변수, 파일 권한)

---

## ⚙️ 설정 파일 구조

### 기본 설정 파일 위치

```yaml
프로젝트 루트/
├── .moai/
│   ├── config/
│   │   └── config.json              # MoAI 전역 설정
│   └── memory/
├── .claude/
│   ├── settings.local.json         # 로컬 사용자 설정
│   ├── agents/                     # 에이전트 정의
│   ├── hooks/                       # 후킹 스크립트
│   ├── skills/                     # 기술 패키지
│   └── output-styles/              # 출력 스타일
└── .env                           # 환경 변수 (비공개)
```

### 설정 파일 계층 구조

```
Global Configuration (.moai/config/config.json)
    ↓
Local Configuration (.claude/settings.local.json)
    ↓
Environment Variables (.env)
```

---

## 🔧 상세 설정 방법

### 1. config.json (MoAI 전역 설정)

#### 기본 구조

```json
{
  "user": {
    "name": "@cyans"
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
  }
}
```

#### 필수 설정 필드

| 설정 필드 | 설명 | 기본값 | 권장값 |
|----------|------|--------|--------|
| `user.name` | 사용자 이름 | - | 실제 사용자 이름 |
| `language.conversation_language` | 대화 언어 | "en" | "ko" |
| `language.agent_prompt_language` | 에이전트 추론 언어 | "en" | "en" |
| `constitution.enforce_tdd` | TDD 강제 여부 | true | true |
| `git_strategy.personal.auto_commit` | 자동 커밋 | true | true |

#### 선택 설정 필드

| 설정 필드 | 설명 | 기본값 | 권장값 |
|----------|------|--------|--------|
| `moai.version_check.enabled` | 버전 체크 | true | true |
| `session.suppress_setup_messages` | 설정 메시지 숨기기 | false | false |
| `moai.update_check_frequency` | 업데이트 빈도 | "daily" | "daily" |

### 2. settings.local.json (로컬 설정)

#### 기본 구조

```json
{
  "project": {
    "name": "moai-adk-윈도우최적화",
    "mode": "personal",
    "locale": "ko",
    "language": "generic",
    "description": "{{PROJECT_DESCRIPTION}}",
    "owner": "@cyans"
  },
  "language": {
    "conversation_language": "ko",
    "conversation_language_name": "Korean",
    "agent_prompt_language": "en",
    "notes": "Language for sub-agent internal prompts (english=global standard, localized=user's conversation language)"
  },
  "constitution": {
    "enforce_tdd": true,
    "principles": {
      "simplicity": {
        "max_projects": 5,
        "notes": "Default recommendation. Adjust in .moai/config.json or via SPEC/ADR with documented rationale based on project size."
      }
    },
    "test_coverage_target": 90
  },
  "git_strategy": {
    "personal": {
      "auto_checkpoint": "disabled",
      "checkpoint_events": [
        "delete",
        "refactor",
        "merge",
        "script",
        "critical-file"
      ],
      "checkpoint_type": "local-branch",
      "max_checkpoints": 10,
      "cleanup_days": 7,
      "push_to_remote": false,
      "auto_commit": true,
      "branch_prefix": "feature/SPEC-",
      "develop_branch": "develop",
      "main_branch": "main",
      "prevent_branch_creation": false,
      "work_on_main": false
    },
    "team": {
      "auto_pr": false,
      "develop_branch": "develop",
      "draft_pr": false,
      "feature_prefix": "feature/SPEC-",
      "main_branch": "main",
      "use_gitflow": true,
      "default_pr_base": "develop",
      "prevent_main_direct_merge": false
    }
  }
}
```

#### 프로젝트별 설정

**개인 프로젝트 설정**:
```json
{
  "git_strategy": {
    "personal": {
      "auto_commit": true,
      "push_to_remote": false,
      "work_on_main": false
    }
  }
}
```

**팀 프로젝트 설정**:
```json
{
  "git_strategy": {
    "team": {
      "use_gitflow": true,
      "auto_pr": true,
      "prevent_main_direct_merge": true
    }
  }
}
```

### 3. .env (환경 변수)

#### 필수 환경 변수

```bash
# Claude API 키 (필수)
GLM_API_KEY=your_api_key_here

# 모델 선택
GLM_MODEL=claude-3-sonnet-20240229
GLM_MAX_TOKENS=4096
GLM_TEMPERATURE=0.7
```

#### 선택 환경 변수

```bash
# 성능 설정
GLM_CACHE_ENABLED=true
GLM_CACHE_SIZE=1GB
GLM_PARALLEL_PROCESSING=true
GLM_MAX_WORKERS=4

# 로깅 설정
GLM_LOG_LEVEL=INFO
GLM_FILE_LOGGING=true
GLM_LOG_ROTATION=true

# 네트워크 설정
GLM_TIMEOUT=60
GLM_RETRIES=3
GLM_PROXY_ENABLED=false
```

---

## 🤖 모델 설정

### GLM 모델 선택

#### 모델 비교

| 모델명 | 특징 | 추천 사용처 | 비용 |
|--------|------|-------------|------|
| `claude-3-sonnet-20240229` | 균형잡힌 성능/비용 | 일반 개발 | 중간 |
| `claude-3-opus-20240229` | 최고 성능 | 복잡한 작업 | 높음 |
| `claude-3-haiku-20240307` | 빠른 속도 | 간단한 작업 | 낮음 |

#### 모델 선택 가이드

```python
# model-selection.py
def recommend_model(task_type: str) -> str:
    """작업 유형에 맞는 모델 추천"""
    model_recommendations = {
        'development': 'claude-3-sonnet-20240229',
        'debugging': 'claude-3-opus-20240229',
        'documentation': 'claude-3-sonnet-20240229',
        'analysis': 'claude-3-opus-20240229',
        'testing': 'claude-3-haiku-20240307',
        'quick_tasks': 'claude-3-haiku-20240307'
    }
    return model_recommendations.get(task_type, 'claude-3-sonnet-20240229')
```

### 모델 파라미터 설정

#### 기본 파라미터

```json
{
  "model": {
    "name": "claude-3-sonnet-20240229",
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40
  }
}
```

#### 파라미터 설명

| 파라미터 | 설명 | 범위 | 추천값 |
|----------|------|------|--------|
| `max_tokens` | 응답 최대 길이 | 1-4096 | 4096 |
| `temperature` | 창의성 조절 | 0-1 | 0.7 |
| `top_p` | 확률 기반 샘플링 | 0-1 | 0.9 |
| `top_k` | 후보 단어 제한 | 0-100 | 40 |

---

## ⚡ 성능 최적화 설정

### 캐시 설정

```json
{
  "performance": {
    "cache_enabled": true,
    "cache_size": "1GB",
    "cache_ttl": 3600,
    "cache_compression": true
  }
}
```

### 병렬 처리 설정

```json
{
  "performance": {
    "parallel_processing": true,
    "max_workers": 4,
    "async_enabled": true,
    "batch_processing": true
  }
}
```

### 메모리 관리

```json
{
  "performance": {
    "memory_limit": "8GB",
    "garbage_collection": true,
    "memory_profiling": false
  }
}
```

### 성능 모니터링

```python
# performance-monitor.py
import psutil
import time
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.log_file = "performance.log"

    def log_performance(self):
        """성능 로깅"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }

        with open(self.log_file, 'a') as f:
            f.write(f"{data}\n")

    def check_performance_thresholds(self):
        """성능 임계값 확인"""
        alerts = []

        if psutil.cpu_percent() > 80:
            alerts.append("CPU 사용률이 높습니다")

        if psutil.virtual_memory().percent > 80:
            alerts.append("메모리 사용량이 많습니다")

        if psutil.disk_usage('/').percent > 90:
            alerts.append("디스크 공간이 부족합니다")

        return alerts
```

---

## 🔒 보안 설정

### API 키 관리

#### 안전한 키 저장

```bash
# .env 파일 권한 설정
chmod 600 .env

# Windows에서는 파일 속성에서 권한 설정
icacls .env /reset
icacls .env /inheritance:r
icacls .env /grant:r "%USERNAME%:R"
```

#### 키 관리 스크립트

```python
# key-manager.py
import os
from pathlib import Path

class KeyManager:
    def __init__(self):
        self.env_file = Path(".env")

    def store_key(self, key_name: str, key_value: str):
        """안전하게 키 저장"""
        if self.env_file.exists():
            with open(self.env_file, 'a') as f:
                f.write(f"\n{key_name}={key_value}\n")
        else:
            with open(self.env_file, 'w') as f:
                f.write(f"{key_name}={key_value}\n")

        # 권한 설정
        os.chmod(self.env_file, 0o600)

    def get_key(self, key_name: str) -> str:
        """키 값 가져오기"""
        if not self.env_file.exists():
            return None

        with open(self.env_file, 'r') as f:
            for line in f:
                if line.startswith(f"{key_name}="):
                    return line.split('=', 1)[1].strip()
        return None
```

### 로깅 보안

```json
{
  "logging": {
    "level": "INFO",
    "file_logging": true,
    "log_rotation": true,
    "max_log_size": "100MB",
    "backup_count": 5,
    "sensitive_data_filter": true,
    "encrypt_logs": false
  }
}
```

---

## 🌐 다국어 설정

### 언어 설정 구조

```json
{
  "language": {
    "conversation_language": "ko",
    "conversation_language_name": "Korean",
    "agent_prompt_language": "en",
    "fallback_language": "en",
    "supported_languages": [
      "ko", "en", "ja", "zh", "es", "fr", "de", "pt", "ru", "it", "ar", "hi"
    ],
    "localization": {
      "date_format": "YYYY-MM-DD",
      "time_format": "HH:mm:ss",
      "number_format": "comma",
      "timezone": "Asia/Seoul"
    }
  }
}
```

### 언어별 특성

| 언어 | 특징 | 추천 사용처 |
|------|------|-------------|
| **ko** (한국어) | 사용자 친화적 | 최종 사용자 대화 |
| **en** (영어) | 에이전트 최적화 | 내부 추론 과정 |
| **ja** (일본어) | 아시아 시장 | 일본 개발자용 |
| **zh** (중국어) | 중국 시장 | 중국 개발자용 |

---

## 📊 설정 검증

### 설정 검증 스크립트

```python
# config-validator.py
import json
import os
from pathlib import Path
from typing import Dict, Any, List

class ConfigValidator:
    def __init__(self):
        self.project_root = Path(".")
        self.config_files = {
            'moai_config': self.project_root / ".moai" / "config" / "config.json",
            'local_config': self.project_root / ".claude" / "settings.local.json",
            'env_file': self.project_root / ".env"
        }

    def validate_config(self) -> Dict[str, Any]:
        """전체 설정 검증"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'config_files': {}
        }

        # 설정 파일 검증
        for name, file_path in self.config_files.items():
            if file_path.exists():
                try:
                    if file_path.suffix == '.json':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        results['config_files'][name] = {
                            'valid': True,
                            'size': len(json.dumps(config)),
                            'keys': list(config.keys())
                        }
                    else:
                        results['config_files'][name] = {
                            'valid': True,
                            'size': file_path.stat().st_size,
                            'exists': True
                        }
                except Exception as e:
                    results['valid'] = False
                    results['errors'].append(f"{name}: {str(e)}")
            else:
                results['warnings'].append(f"{name}: 파일이 존재하지 않음")

        # API 키 검증
        self._validate_api_keys(results)

        return results

    def _validate_api_keys(self, results: Dict[str, Any]):
        """API 키 검증"""
        env_file = self.config_files['env_file']

        if not env_file.exists():
            results['warnings'].append("API 키 파일이 없음")
            return

        with open(env_file, 'r') as f:
            content = f.read()

        if 'GLM_API_KEY=' not in content:
            results['warnings'].append("GLM_API_KEY가 설정되지 않음")

        # 키 형식 검사
        for line in content.split('\n'):
            if line.startswith('GLM_API_KEY='):
                key_value = line.split('=', 1)[1].strip()
                if len(key_value) < 32:
                    results['warnings'].append("API 키가 너무 짧음")
```

### 검증 실행

```python
# validator 실행 예시
validator = ConfigValidator()
result = validator.validate_config()

if result['valid']:
    print("✅ 설정 검증 통과")
else:
    print("❌ 설정 검증 실패")
    for error in result['errors']:
        print(f"  - {error}")

for warning in result['warnings']:
    print(f"⚠️  {warning}")
```

---

## 🔄 설정 업데이트

### 설정 업데이트 스크립트

```python
# config-updater.py
import json
from pathlib import Path
from typing import Dict, Any

class ConfigUpdater:
    def __init__(self):
        self.project_root = Path(".")
        self.moai_config = self.project_root / ".moai" / "config" / "config.json"

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """설정 업데이트"""
        try:
            # 기존 설정 로드
            if self.moai_config.exists():
                with open(self.moai_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}

            # 설정 업데이트 (깊은 병합)
            self._deep_merge(config, updates)

            # 저장
            with open(self.moai_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"설정 업데이트 실패: {e}")
            return False

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]):
        """깊은 병합 함수"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
```

### 자동 업데이트 예시

```python
# 자동 업데이트 실행
updater = ConfigUpdater()

# 최신 설정으로 업데이트
latest_updates = {
    "moai": {
        "version": "0.27.2",
        "update_check_frequency": "daily"
    },
    "language": {
        "conversation_language": "ko"
    }
}

if updater.update_config(latest_updates):
    print("✅ 설정이 성공적으로 업데이트되었습니다")
```

---

## 📋 설정 체크리스트

### 설정 완료 확인사항

- [ ] **기본 설정 확인**
  - [ ] 사용자 이름 설정 (`user.name`)
  - [ ] 대화 언어 설정 (`language.conversation_language`)
  - [ ] 에이전트 언어 설정 (`language.agent_prompt_language`)

- [ ] **API 설정 확인**
  - [ ] API 키 설정 (`.env` 파일)
  - [ ] 모델 선택 (`GLM_MODEL`)
  - [ ] 기본 파라미터 설정

- [ ] **성능 설정 확인**
  - [ ] 캐시 설정
  - [ ] 병렬 처리 설정
  - [ ] 메모리 한계 설정

- [ ] **보안 설정 확인**
  - [ ] 파일 권한 설정
  - [ ] 민감 정보 필터링
  - [ ] 로그 암호화 설정

- [ ] **검증 실행**
  - [ ] 설정 파일 무결성 검사
  - [ ] API 키 유효성 검사
  - [ ] 의존성 패키지 확인

---

## 📞 문제 해결

### 일반적인 문제

#### 문제 1: 설정 파일 오류

**현상**: 설정 파일을 읽을 수 없거나 형식이 잘림

**해결 방법**:
```bash
# 설정 파일 백업
cp .moai/config/config.json .moai/config/config.json.backup

# 기본 설정 복원
cp config-template.json .moai/config/config.json
```

#### 문제 2: API 키 오류

**현상**: 인증 실패 오류 발생

**해결 방법**:
```bash
# 환경 변수 파일 확인
cat .env

# API 키 재설정
echo "GLM_API_KEY=your_new_api_key" > .env
```

#### 문제 3: 모델 선택 오류

**현상**: 지원하지 않는 모델 오류

**해결 방법**:
```json
// 지원되는 모델로 변경
{
  "model": {
    "name": "claude-3-sonnet-20240229",
    "max_tokens": 4096
  }
}
```

### 고급 문제 해결

#### 설정 파일 복구

```python
# config-recovery.py
import shutil
from pathlib import Path
from datetime import datetime

class ConfigRecovery:
    def __init__(self):
        self.backup_dir = Path(".moai/backups")
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self) -> Path:
        """설정 파일 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"config_backup_{timestamp}.json"

        config_file = Path(".moai/config/config.json")
        if config_file.exists():
            shutil.copy2(config_file, backup_file)
            return backup_file

        return None

    def restore_backup(self, backup_file: Path):
        """백업 파일 복원"""
        target_file = Path(".moai/config/config.json")
        shutil.copy2(backup_file, target_file)
        print(f"백업 복원 완료: {backup_file}")
```

---

## 📊 설정 모니터링

### 설정 변경 추적

```python
# config-monitor.py
import json
import hashlib
from pathlib import Path
from datetime import datetime

class ConfigMonitor:
    def __init__(self):
        self.project_root = Path(".")
        self.monitor_file = self.project_root / ".moai" / "logs" / "config_changes.log"

    def get_config_hash(self) -> str:
        """설정 파일 해시 계산"""
        config_file = self.project_root / ".moai" / "config" / "config.json"

        if not config_file.exists():
            return None

        with open(config_file, 'rb') as f:
            content = f.read()
            return hashlib.md5(content).hexdigest()

    def log_config_change(self, old_hash: str, new_hash: str):
        """설정 변경 로깅"""
        timestamp = datetime.now().isoformat()
        change_log = {
            'timestamp': timestamp,
            'old_hash': old_hash,
            'new_hash': new_hash,
            'changed': old_hash != new_hash
        }

        with open(self.monitor_file, 'a', encoding='utf-8') as f:
            f.write(f"{json.dumps(change_log, ensure_ascii=False)}\n")
```

---

## 🚀 설정 최적화 팁

### 성능 최적화 팁

1. **캐시 활용**
   ```json
   {
     "performance": {
       "cache_enabled": true,
       "cache_size": "2GB"
     }
   }
   ```

2. **병렬 처리 최적화**
   ```json
   {
     "performance": {
       "max_workers": min(4, CPU 코어 수),
       "async_enabled": true
     }
   }
   ```

3. **메모리 관리**
   ```json
   {
     "performance": {
       "memory_limit": "50% of available RAM",
       "garbage_collection": true
     }
   }
   ```

### 보안 최적화 팁

1. **정기적인 키 회전**
   ```bash
   # 정기적인 API 키 변경 스크립트
   ./rotate-api-keys.sh
   ```

2. **로그 보안**
   ```json
   {
     "logging": {
       "sensitive_data_filter": true,
       "log_retention_days": 30
     }
   }
   ```

3. **네트워크 보안**
   ```json
   {
     "security": {
       "https_only": true,
       "certificate_verification": true
     }
   }
   ```

---

## 📋 버전 정보

| 설정 요소 | 버전 | 최신 업데이트 | 설명 |
|----------|------|-------------|------|
| **MoAI 설정** | 0.27.2 | 2025-11-27 | 메인 설정 프레임워크 |
| **GLM 모델** | 3.5 | 2025-11-27 | Claude GLM 통합 |
| **지원 언어** | 12개 | 2025-11-27 | 다국어 지원 |
| **보안 수준** | 높음 | 2025-11-27 | 엔터프라이즈 보안 |

---

## 📞 지원 정보

### 기술 지원

- **문서**: [MoAI 공식 문서](https://moai-ai.github.io/docs/)
- **이슈 리포트**: [GitHub Issues](https://github.com/your-repo/issues)
- **커뮤니티**: [MoAI Discord 서버](https://discord.gg/moai)

### 설정 관련 문의

- **이메일**: support@moai-ai.com
- **문제 해결**: `.moai/logs/` 디렉토리 확인
- **버전 확인**: `/moai --version`

---

## 🔗 관련 문서

- [Windows 배포 자동화 가이드](../guides/windows-deployment-guide.md)
- [모델 설정 스크립트 문서](../guides/model-setup-scripts.md)
- [MoAI 공식 문서](https://moai-ai.github.io/docs/)

---

**문서 유지보수**: 이 문서는 MoAI-ADK의 주요 버전 업데이트 시 함께 갱신됩니다. 설정 변경 사항은 항상 최신 버전을 확인하시기 바랍니다.

**작성자**: @cyans
**마지막 업데이트**: 2025-11-27