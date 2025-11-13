# 🔄 Git 자동 동기화 가이드

## 개요
파일을 수정할 때마다 자동으로 GitHub에 커밋하고 푸시하는 스크립트입니다.

## 🚀 빠른 시작

### 1. 필요한 패키지 설치
```bash
pip install watchdog
```

### 2. 스크립트 실행
```bash
python auto_sync.py
```

### 3. 파일 수정하기
이제 프로젝트의 파일을 수정하면 **자동으로 GitHub에 업로드**됩니다!

---

## ⚙️ 동작 방식

1. **파일 감시**: 프로젝트 디렉토리의 모든 파일 변경을 감지합니다
2. **변경 감지**: 파일 생성, 수정, 삭제를 실시간으로 감지합니다
3. **자동 커밋**: 변경사항을 자동으로 Git에 커밋합니다
4. **자동 푸시**: GitHub에 자동으로 푸시합니다 (재시도 로직 포함)

### 자동으로 무시되는 파일
- `.git/` - Git 내부 파일
- `__pycache__/` - Python 캐시
- `*.pyc` - Python 컴파일 파일
- `.env` - 환경 변수 (보안)
- `chroma_db/` - 벡터 DB
- `chat_history/` - 채팅 기록
- `*.log` - 로그 파일

---

## 📋 사용 예시

### 기본 실행
```bash
# 현재 디렉토리에서 자동 동기화 시작
python auto_sync.py
```

### 백그라운드 실행 (Linux/Mac)
```bash
# 백그라운드에서 실행
nohup python auto_sync.py > auto_sync.log 2>&1 &

# 프로세스 확인
ps aux | grep auto_sync

# 종료
kill $(pgrep -f auto_sync.py)
```

### 스크린 세션으로 실행 (서버 환경)
```bash
# 새 스크린 세션 생성
screen -S git-sync

# 스크립트 실행
python auto_sync.py

# Ctrl+A, D로 세션 분리
# 다시 접속: screen -r git-sync
```

---

## 🎯 실행 화면

```
╔═══════════════════════════════════════════════════════════╗
║          🤖 Git 자동 동기화 스크립트                      ║
║          파일 변경 시 자동으로 GitHub에 푸시합니다         ║
╚═══════════════════════════════════════════════════════════╝

✅ 브랜치 확인: claude/local-integration-setup-011CV5X2DN6gjH1SzxsWbo7T

📂 감시 경로: /home/user/llm-chatbot-server
🌿 브랜치: claude/local-integration-setup-011CV5X2DN6gjH1SzxsWbo7T
⏱️  동기화 딜레이: 5초

👀 파일 변경 감시 시작... (Ctrl+C로 종료)

📝 파일 변경 감지: /home/user/llm-chatbot-server/main.py

============================================================
🔄 Git 동기화 시작... [2024-11-13 10:30:45]
============================================================
📝 변경된 파일:
 M main.py

📦 변경사항 스테이징 중...
💾 커밋 중: Auto-sync: 2024-11-13 10:30:45
🚀 GitHub에 푸시 중 (브랜치: claude/local-integration-setup-011CV5X2DN6gjH1SzxsWbo7T)...
✅ GitHub에 성공적으로 푸시됨!
============================================================
```

---

## ⚠️ 주의사항

### 1. 브랜치 확인
스크립트는 자동으로 `claude/local-integration-setup-011CV5X2DN6gjH1SzxsWbo7T` 브랜치를 사용합니다.
- 브랜치가 없으면 자동으로 생성됩니다
- 다른 브랜치를 사용하려면 스크립트를 수정하세요

### 2. 네트워크 오류 처리
푸시 실패 시 자동으로 4번까지 재시도합니다:
- 1차 실패 → 2초 대기 후 재시도
- 2차 실패 → 4초 대기 후 재시도
- 3차 실패 → 8초 대기 후 재시도
- 4차 실패 → 16초 대기 후 재시도

### 3. 민감한 정보
`.env` 파일과 같은 민감한 정보는 자동으로 무시됩니다.
추가로 무시할 파일이 있다면 `.gitignore`에 추가하세요.

### 4. 과도한 커밋
너무 자주 파일을 수정하면 커밋이 많이 생성될 수 있습니다.
필요시 `delay` 값을 늘려서 동기화 빈도를 조절하세요.

---

## 🔧 커스터마이징

### 브랜치 변경
`auto_sync.py` 파일의 `branch` 변수를 수정하세요:
```python
branch = "your-branch-name"
```

### 동기화 딜레이 변경
```python
delay = 10  # 10초로 변경
```

### 무시 패턴 추가
```python
ignore_patterns = [
    '.git',
    '__pycache__',
    '*.pyc',
    '.env',
    'your-custom-pattern'  # 추가
]
```

---

## 🐛 문제 해결

### Q: "Git 저장소가 아닙니다" 오류
**A**: Git이 초기화된 디렉토리에서 실행하세요.
```bash
git init
```

### Q: 푸시 권한 오류 (403)
**A**: GitHub 인증을 확인하세요.
```bash
# SSH 키 설정 또는 Personal Access Token 사용
git config --global credential.helper store
```

### Q: 브랜치가 자동 생성되지 않음
**A**: 수동으로 브랜치를 생성하세요.
```bash
git checkout -b claude/local-integration-setup-011CV5X2DN6gjH1SzxsWbo7T
```

### Q: 스크립트가 멈춤
**A**: Ctrl+C로 종료하고 다시 실행하세요.

---

## 📊 성능 정보

- **메모리 사용량**: 약 20-30MB
- **CPU 사용량**: 거의 없음 (대기 중)
- **동기화 시간**: 파일 크기에 따라 1-10초

---

## 🔗 관련 문서

- [README.md](README.md) - 프로젝트 전체 가이드
- [QUICK_START.md](QUICK_START.md) - 빠른 시작 가이드
- [TEST_GUIDE.md](TEST_GUIDE.md) - 테스트 가이드

---

## 💡 팁

### 개발 워크플로우
1. **터미널 1**: 자동 동기화 스크립트 실행
   ```bash
   python auto_sync.py
   ```

2. **터미널 2**: 서버 실행
   ```bash
   python main.py
   ```

3. **터미널 3**: 코드 수정 및 테스트
   ```bash
   # 파일 수정하면 자동으로 GitHub에 업로드됨!
   ```

### VS Code 통합
`.vscode/tasks.json`에 추가:
```json
{
  "label": "Start Git Auto-Sync",
  "type": "shell",
  "command": "python auto_sync.py",
  "problemMatcher": [],
  "isBackground": true
}
```

---

**마지막 업데이트**: 2024-11-13
**버전**: 1.0.0
