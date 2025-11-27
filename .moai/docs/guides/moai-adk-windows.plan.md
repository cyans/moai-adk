<!-- 2016e6b3-123b-4e5f-9e5a-0b6583253cd5 61d4db20-56bb-4901-89c2-40cd341cdc4f -->
# MoAI-ADK 윈도우 최적화 배포 및 Upstream 관리 계획

## 1단계: 윈도우 최적화 코드를 Fork 저장소에 통합

현재 작업한 코드(`src/moai_adk/platform/`, `src/moai_adk/statusline/`)를 `moai-adk-temp/` 저장소에 복사하고 커밋합니다.

**작업 내용:**

- `src/moai_adk/platform/` → `moai-adk-temp/src/moai_adk/platform/`
- `src/moai_adk/statusline/` → `moai-adk-temp/src/moai_adk/statusline/` (변경된 파일만)
- 관련 테스트 파일도 함께 복사

## 2단계: Upstream 원격 저장소 설정

Fork 저장소에서 원본 저장소(modu-ai/moai-adk)를 upstream으로 설정합니다.

```bash
cd moai-adk-temp
git remote set-url upstream https://github.com/modu-ai/moai-adk.git
```

## 3단계: GitHub에 푸시

윈도우 최적화 브랜치를 생성하고 GitHub fork 저장소에 푸시합니다.

```bash
git checkout -b feature/windows-optimization
git add .
git commit -m "feat(windows): Add Windows platform optimization"
git push origin feature/windows-optimization
```

그 후 main/develop 브랜치에 병합합니다.

## 4단계: 로컬 moai-adk 업데이트

pip를 사용하여 GitHub fork 저장소에서 직접 설치합니다.

```bash
pip uninstall moai-adk
pip install git+https://github.com/cyans/moai-adk.git@develop
```

## 5단계: 윈도우 최적화 테스트

설치된 moai-adk가 윈도우 최적화가 제대로 적용되었는지 확인합니다.

- `moai --version` 명령어 실행
- statusline 한글/이모지 인코딩 테스트
- platform detector 동작 확인

## 6단계: Upstream 업데이트 병합 워크플로우 (향후 사용)

원본 moai-adk가 업데이트되면 다음 명령어로 병합합니다:

```bash
cd moai-adk-temp
git fetch upstream
git checkout develop
git merge upstream/main --no-edit
# 충돌 해결 후
git push origin develop
# 로컬 재설치
pip install git+https://github.com/cyans/moai-adk.git@develop --upgrade
```

---

**파일 경로 요약:**

- Fork 저장소: `D:\claude_code\moai-adk-윈도우최적화\moai-adk-temp\`
- 새 platform 모듈: `src/moai_adk/platform/` (5개 파일)
- 수정된 statusline: `src/moai_adk/statusline/` (4개 파일)

### To-dos

- [x] 윈도우 최적화 코드를 moai-adk-temp 저장소에 복사 및 통합
- [x] upstream 원격 저장소를 modu-ai/moai-adk로 설정
- [x] GitHub fork 저장소에 변경사항 푸시
- [x] pip로 로컬 moai-adk 업데이트
- [x] 윈도우 최적화 동작 테스트