#!/bin/bash
# Git 자동 동기화 시작 스크립트

echo "🔧 Git 자동 동기화 설정 중..."

# watchdog 패키지 확인 및 설치
if ! python -c "import watchdog" 2>/dev/null; then
    echo "📦 watchdog 패키지 설치 중..."
    pip install watchdog>=3.0.0
else
    echo "✅ watchdog 패키지 이미 설치됨"
fi

echo ""
echo "🚀 자동 동기화 시작..."
echo ""

# 자동 동기화 스크립트 실행
python auto_sync.py
